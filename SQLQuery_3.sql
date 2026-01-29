
-- Flight Reservation System - Stored Procedures



USE FlightReservationDB;
GO

PRINT 'Creating stored procedures...';
GO


-- SP 1: Search Available Flights

CREATE OR ALTER PROCEDURE SP_SearchFlights
    @departure_airport_id INT,
    @arrival_airport_id INT,
    @travel_date DATE,
    @class_type VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        f.flight_id,
        f.flight_number,
        al.airline_name,
        al.airline_code,
        dep.airport_name AS departure_airport,
        dep.city AS departure_city,
        arr.airport_name AS arrival_airport,
        arr.city AS arrival_city,
        f.departure_datetime,
        f.arrival_datetime,
        f.flight_duration_minutes,
        f.base_price,
        f.available_seats,
        ac.aircraft_model,
        f.status,
        f.gate_number,
        -- Calculate price based on class
        CASE 
            WHEN @class_type = 'Economy' THEN f.base_price
            WHEN @class_type = 'Business' THEN f.base_price * 2.5
            WHEN @class_type = 'First Class' THEN f.base_price * 4.0
            ELSE f.base_price
        END AS class_price
    FROM FLIGHTS f
    INNER JOIN AIRLINES al ON f.airline_id = al.airline_id
    INNER JOIN AIRPORTS dep ON f.departure_airport_id = dep.airport_id
    INNER JOIN AIRPORTS arr ON f.arrival_airport_id = arr.airport_id
    INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
    WHERE f.departure_airport_id = @departure_airport_id
        AND f.arrival_airport_id = @arrival_airport_id
        AND CAST(f.departure_datetime AS DATE) = @travel_date
        AND f.status IN ('Scheduled', 'Boarding')
        AND f.available_seats > 0
    ORDER BY f.departure_datetime;
END;
GO


-- SP 2: Create Reservation

CREATE OR ALTER PROCEDURE SP_CreateReservation
    @passenger_id INT,
    @flight_id INT,
    @class_type VARCHAR(20),
    @seat_number VARCHAR(5) = NULL,
    @reservation_id INT OUTPUT,
    @booking_reference VARCHAR(10) OUTPUT,
    @total_price DECIMAL(10,2) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Check if flight exists and has available seats
        DECLARE @available_seats INT, @base_price DECIMAL(10,2), @flight_status VARCHAR(20);
        
        SELECT @available_seats = available_seats, 
               @base_price = base_price,
               @flight_status = status
        FROM FLIGHTS 
        WHERE flight_id = @flight_id;
        
        IF @available_seats IS NULL
        BEGIN
            RAISERROR('Flight not found', 16, 1);
            RETURN;
        END
        
        IF @flight_status NOT IN ('Scheduled', 'Boarding')
        BEGIN
            RAISERROR('Flight is not available for booking', 16, 1);
            RETURN;
        END
        
        IF @available_seats <= 0
        BEGIN
            RAISERROR('No seats available on this flight', 16, 1);
            RETURN;
        END
        
        -- Calculate price based on class
        SET @total_price = CASE 
            WHEN @class_type = 'Economy' THEN @base_price
            WHEN @class_type = 'Business' THEN @base_price * 2.5
            WHEN @class_type = 'First Class' THEN @base_price * 4.0
            ELSE @base_price
        END;
        
        -- Apply dynamic pricing based on booking window
        DECLARE @days_until_departure INT;
        SELECT @days_until_departure = DATEDIFF(DAY, GETDATE(), departure_datetime)
        FROM FLIGHTS WHERE flight_id = @flight_id;
        
        IF @days_until_departure < 7
            SET @total_price = @total_price * 1.5;
        ELSE IF @days_until_departure < 14
            SET @total_price = @total_price * 1.3;
        ELSE IF @days_until_departure < 30
            SET @total_price = @total_price * 1.1;
        
        -- Generate booking reference
        SET @booking_reference = 
            CHAR(65 + ABS(CHECKSUM(NEWID())) % 26) +
            CHAR(65 + ABS(CHECKSUM(NEWID())) % 26) +
            CAST(ABS(CHECKSUM(NEWID())) % 1000000 AS VARCHAR(6));
        
        -- Assign seat if not provided
        IF @seat_number IS NULL
        BEGIN
            SET @seat_number = @class_type + '-' + CAST((SELECT COUNT(*) FROM RESERVATIONS WHERE flight_id = @flight_id) + 1 AS VARCHAR(3));
        END
        
        -- Check if seat is already booked
        IF EXISTS (SELECT 1 FROM RESERVATIONS WHERE flight_id = @flight_id AND seat_number = @seat_number AND reservation_status = 'Confirmed')
        BEGIN
            RAISERROR('Seat already booked', 16, 1);
            RETURN;
        END
        
        -- Create reservation
        INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, seat_number, class_type, total_price)
        VALUES (@passenger_id, @flight_id, @booking_reference, @seat_number, @class_type, @total_price);
        
        SET @reservation_id = SCOPE_IDENTITY();
        
        
        COMMIT TRANSACTION;
        
        PRINT 'Reservation created successfully. Booking Reference: ' + @booking_reference;
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO



-- SP 3: Register User

CREATE OR ALTER PROCEDURE SP_RegisterUser
    @username VARCHAR(50),
    @password_hash VARCHAR(255),
    @email VARCHAR(100),
    @role VARCHAR(20) = 'Customer',
    @passenger_id INT = NULL,
    @user_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Check if username exists
        IF EXISTS (SELECT 1 FROM USERS WHERE username = @username)
        BEGIN
            RAISERROR('Username already exists', 16, 1);
            RETURN;
        END
        
        -- Check if email exists
        IF EXISTS (SELECT 1 FROM USERS WHERE email = @email)
        BEGIN
            RAISERROR('Email already registered', 16, 1);
            RETURN;
        END
        
        -- Insert user
        INSERT INTO USERS (username, password_hash, email, role, passenger_id)
        VALUES (@username, @password_hash, @email, @role, @passenger_id);
        
        SET @user_id = SCOPE_IDENTITY();
        
        COMMIT TRANSACTION;
        
        PRINT 'User registered successfully. User ID: ' + CAST(@user_id AS VARCHAR(10));
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO


-- SP 4: Authenticate User

CREATE OR ALTER PROCEDURE SP_AuthenticateUser
    @username VARCHAR(50),
    @password_hash VARCHAR(255),
    @user_id INT OUTPUT,
    @role VARCHAR(20) OUTPUT,
    @passenger_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        @user_id = user_id,
        @role = role,
        @passenger_id = passenger_id
    FROM USERS
    WHERE username = @username 
        AND password_hash = @password_hash 
        AND is_active = 1;
    
    IF @user_id IS NOT NULL
    BEGIN
        -- Update last login
        UPDATE USERS 
        SET last_login = GETDATE()
        WHERE user_id = @user_id;
        
        PRINT 'Authentication successful';
    END
    ELSE
    BEGIN
        PRINT 'Authentication failed';
    END
END;
GO


-- SP 5: Get Flight Statistics

CREATE OR ALTER PROCEDURE SP_GetFlightStatistics
    @flight_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        f.flight_id,
        f.flight_number,
        al.airline_name,
        f.departure_datetime,
        f.status,
        ac.total_seats,
        f.available_seats,
        (ac.total_seats - f.available_seats) AS booked_seats,
        CAST((ac.total_seats - f.available_seats) * 100.0 / ac.total_seats AS DECIMAL(5,2)) AS occupancy_percentage,
        COUNT(r.reservation_id) AS total_reservations,
        SUM(CASE WHEN r.payment_status = 'Paid' THEN 1 ELSE 0 END) AS paid_reservations,
        SUM(CASE WHEN r.payment_status = 'Paid' THEN r.total_price ELSE 0 END) AS total_revenue
    FROM FLIGHTS f
    INNER JOIN AIRLINES al ON f.airline_id = al.airline_id
    INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
    LEFT JOIN RESERVATIONS r ON f.flight_id = r.flight_id
    WHERE f.flight_id = @flight_id
    GROUP BY f.flight_id, f.flight_number, al.airline_name, f.departure_datetime, 
             f.status, ac.total_seats, f.available_seats;
END;
GO


-- SP 6: Check-In Passenger
CREATE OR ALTER PROCEDURE SP_CheckInPassenger
    @reservation_id INT,
    @boarding_pass_info VARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @status VARCHAR(20);
    DECLARE @flight_id INT;
    DECLARE @seat VARCHAR(5);
    
    SELECT @status = reservation_status, @flight_id = flight_id, @seat = seat_number
    FROM RESERVATIONS WHERE reservation_id = @reservation_id;
    
    IF @status IS NULL
    BEGIN
        RAISERROR('Reservation not found.', 16, 1);
        RETURN;
    END

    IF @status = 'Cancelled'
    BEGIN
        RAISERROR('Cannot check-in a cancelled reservation.', 16, 1);
        RETURN;
    END
    
    -- Update status
    UPDATE RESERVATIONS 
    SET reservation_status = 'Checked-In' 
    WHERE reservation_id = @reservation_id;
    
    -- Generate simple boarding pass info
    SELECT @boarding_pass_info = 
        'BOARDING PASS\n' +
        'Flight: ' + f.flight_number + '\n' +
        'Gate: ' + ISNULL(f.gate_number, 'TBA') + '\n' +
        'Seat: ' + @seat + '\n' +
        'Passenger: ' + p.first_name + ' ' + p.last_name
    FROM RESERVATIONS r
    JOIN FLIGHTS f ON r.flight_id = f.flight_id
    JOIN PASSENGERS p ON r.passenger_id = p.passenger_id
    WHERE r.reservation_id = @reservation_id;

    PRINT 'Passenger checked in successfully.';
END;
GO

-- SP 7: Cancel Reservation
CREATE OR ALTER PROCEDURE SP_CancelReservation
    @reservation_id INT,
    @reason VARCHAR(200),
    @refund_amount DECIMAL(10,2) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @paid_amount DECIMAL(10,2);
    DECLARE @payment_status VARCHAR(20);
    
    SELECT @paid_amount = total_price, @payment_status = payment_status
    FROM RESERVATIONS WHERE reservation_id = @reservation_id;
    
    IF @paid_amount IS NULL
    BEGIN
        RAISERROR('Reservation not found.', 16, 1);
        RETURN;
    END
    
    -- Update status
    UPDATE RESERVATIONS 
    SET reservation_status = 'Cancelled',
        special_requests = ISNULL(special_requests, '') + ' [Cancelled: ' + @reason + ']'
    WHERE reservation_id = @reservation_id;
    
    -- Calculate refund (Simple logic: 100% if paid)
    IF @payment_status = 'Paid'
    BEGIN
        SET @refund_amount = @paid_amount;
        -- Trigger logic will handle specific payment status updates if needed, 
        -- but here we just return the calculation
        
        -- Optionally update payment to Refunded if you want
        UPDATE PAYMENTS SET payment_status = 'Refunded' WHERE reservation_id = @reservation_id AND payment_status = 'Success';
    END
    ELSE
    BEGIN
        SET @refund_amount = 0.00;
    END
    
    PRINT 'Reservation cancelled.';
END;
GO

-- SP 8: Process Payment
CREATE OR ALTER PROCEDURE SP_ProcessPayment
    @reservation_id INT,
    @payment_method VARCHAR(20),
    @amount DECIMAL(10,2),
    @card_last_four VARCHAR(4) = NULL,
    @payment_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Simple validation
    IF NOT EXISTS (SELECT 1 FROM RESERVATIONS WHERE reservation_id = @reservation_id)
    BEGIN
        RAISERROR('Reservation not found.', 16, 1);
        RETURN;
    END
    
    -- Insert Payment
    INSERT INTO PAYMENTS (reservation_id, payment_method, amount, payment_date, payment_status, transaction_id, card_last_four)
    VALUES (@reservation_id, @payment_method, @amount, GETDATE(), 'Success', 'TXN' + CAST(ABS(CHECKSUM(NEWID())) AS VARCHAR(20)), @card_last_four);
    
    SET @payment_id = SCOPE_IDENTITY();
    
    
    
    PRINT 'Payment processed successfully.';
END;
GO

PRINT 'Total procedures: 8';
GO