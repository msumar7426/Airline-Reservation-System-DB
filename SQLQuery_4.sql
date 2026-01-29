
-- Flight Reservation System - Functions & Triggers


USE FlightReservationDB;
GO
-- TRIGGER 1: Update Available Seats on Reservation

CREATE OR ALTER TRIGGER TRG_UpdateAvailableSeats
ON RESERVATIONS
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update available seats for affected flights
    UPDATE f
    SET available_seats = ac.total_seats - (
        SELECT COUNT(*) 
        FROM RESERVATIONS r
        WHERE r.flight_id = f.flight_id 
            AND r.reservation_status IN ('Confirmed', 'Checked-In')
    )
    FROM FLIGHTS f
    INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
    WHERE f.flight_id IN (SELECT DISTINCT flight_id FROM inserted);
END;
GO


-- TRIGGER 2: Update Payment Status on Payment

CREATE OR ALTER TRIGGER TRG_UpdatePaymentStatus
ON PAYMENTS
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update reservation payment status if payment is successful
    UPDATE r
    SET payment_status = CASE 
        WHEN i.payment_status = 'Success' THEN 'Paid'
        WHEN i.payment_status = 'Refunded' THEN 'Refunded'
        ELSE r.payment_status
    END
    FROM RESERVATIONS r
    INNER JOIN inserted i ON r.reservation_id = i.reservation_id
    WHERE i.payment_status IN ('Success', 'Refunded');
END;
GO

PRINT 'All functions and triggers created successfully!';
PRINT 'Total Functions: 2';
PRINT 'Total Triggers: 2';
GO


PRINT 'Creating user-defined functions...';
GO


-- FUNCTION 1: Calculate Dynamic Ticket Price

CREATE OR ALTER FUNCTION FN_CalculateTicketPrice
(
    @base_price DECIMAL(10,2),
    @class_type VARCHAR(20),
    @booking_date DATETIME,
    @departure_date DATETIME
)
RETURNS DECIMAL(10,2)
AS
BEGIN
    DECLARE @final_price DECIMAL(10,2);
    DECLARE @class_multiplier DECIMAL(5,2);
    DECLARE @days_until_departure INT;
    DECLARE @demand_multiplier DECIMAL(5,2);
    
    -- Class multiplier
    SET @class_multiplier = CASE 
        WHEN @class_type = 'Economy' THEN 1.0
        WHEN @class_type = 'Business' THEN 2.5
        WHEN @class_type = 'First Class' THEN 4.0
        ELSE 1.0
    END;
    
    -- Days until departure
    SET @days_until_departure = DATEDIFF(DAY, @booking_date, @departure_date);
    
    -- Demand multiplier based on booking window
    SET @demand_multiplier = CASE 
        WHEN @days_until_departure < 7 THEN 1.5
        WHEN @days_until_departure < 14 THEN 1.3
        WHEN @days_until_departure < 30 THEN 1.1
        ELSE 1.0
    END;
    
    -- Calculate final price
    SET @final_price = @base_price * @class_multiplier * @demand_multiplier;
    
    RETURN @final_price;
END;
GO


-- FUNCTION 2: Get Available Seats by Class

CREATE OR ALTER FUNCTION FN_GetAvailableSeatsByClass
(
    @flight_id INT,
    @class_type VARCHAR(20)
)
RETURNS INT
AS
BEGIN
    DECLARE @total_class_seats INT;
    DECLARE @booked_class_seats INT;
    DECLARE @available INT;
    
    -- Get total seats for the class
    SELECT @total_class_seats = CASE 
        WHEN @class_type = 'Economy' THEN ac.economy_seats
        WHEN @class_type = 'Business' THEN ac.business_seats
        WHEN @class_type = 'First Class' THEN ac.first_class_seats
        ELSE 0
    END
    FROM FLIGHTS f
    INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
    WHERE f.flight_id = @flight_id;
    
    -- Get booked seats for the class
    SELECT @booked_class_seats = COUNT(*)
    FROM RESERVATIONS
    WHERE flight_id = @flight_id 
        AND class_type = @class_type
        AND reservation_status IN ('Confirmed', 'Checked-In');
    
    SET @available = ISNULL(@total_class_seats, 0) - ISNULL(@booked_class_seats, 0);
    
    RETURN CASE WHEN @available < 0 THEN 0 ELSE @available END;
END;
GO


PRINT 'All functions created successfully!';
GO

