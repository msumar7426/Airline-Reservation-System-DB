
-- Flight Reservation System - Views & Sample Data

USE FlightReservationDB;
GO

-- VIEW 1: Available Flights with Details

CREATE OR ALTER VIEW VW_AvailableFlights
AS
SELECT 
    f.flight_id,
    f.flight_number,
    al.airline_name,
    al.airline_code,
    dep.airport_code AS departure_code,
    dep.airport_name AS departure_airport,
    dep.city AS departure_city,
    dep.country AS departure_country,
    arr.airport_code AS arrival_code,
    arr.airport_name AS arrival_airport,
    arr.city AS arrival_city,
    arr.country AS arrival_country,
    f.departure_datetime,
    f.arrival_datetime,
    f.flight_duration_minutes,
    f.base_price,
    f.available_seats,
    ac.aircraft_model,
    ac.total_seats,
    f.status,
    f.gate_number,
    CAST((ac.total_seats - f.available_seats) * 100.0 / ac.total_seats AS DECIMAL(5,2)) AS occupancy_rate
FROM FLIGHTS f
INNER JOIN AIRLINES al ON f.airline_id = al.airline_id
INNER JOIN AIRPORTS dep ON f.departure_airport_id = dep.airport_id
INNER JOIN AIRPORTS arr ON f.arrival_airport_id = arr.airport_id
INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
WHERE f.status IN ('Scheduled', 'Boarding') 
    AND f.available_seats > 0;
GO


-- VIEW 2: Passenger Reservation Details

CREATE OR ALTER VIEW VW_PassengerReservationDetails
AS
SELECT 
    r.reservation_id,
    r.booking_reference,
    p.passenger_id,
    p.first_name + ' ' + p.last_name AS passenger_name,
    p.email,
    p.phone_number,
    p.passport_number,
    f.flight_id,
    f.flight_number,
    al.airline_name,
    dep.city AS departure_city,
    arr.city AS arrival_city,
    f.departure_datetime,
    f.arrival_datetime,
    r.seat_number,
    r.class_type,
    r.total_price,
    r.payment_status,
    r.reservation_status,
    r.booking_date,
    pay.payment_method,
    pay.payment_date,
    pay.transaction_id
FROM RESERVATIONS r
INNER JOIN PASSENGERS p ON r.passenger_id = p.passenger_id
INNER JOIN FLIGHTS f ON r.flight_id = f.flight_id
INNER JOIN AIRLINES al ON f.airline_id = al.airline_id
INNER JOIN AIRPORTS dep ON f.departure_airport_id = dep.airport_id
INNER JOIN AIRPORTS arr ON f.arrival_airport_id = arr.airport_id
LEFT JOIN PAYMENTS pay ON r.reservation_id = pay.reservation_id AND pay.payment_status = 'Success';
GO


-- VIEW 3: Flight Statistics

CREATE OR ALTER VIEW VW_FlightStatistics
AS
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
GROUP BY f.flight_id, f.flight_number, al.airline_name, f.departure_datetime, 
         f.status, ac.total_seats, f.available_seats;
GO


-- VIEW 4: Airline Performance

CREATE OR ALTER VIEW VW_AirlinePerformance
AS
SELECT 
    al.airline_id,
    al.airline_name,
    al.airline_code,
    COUNT(DISTINCT f.flight_id) AS total_flights,
    SUM(ac.total_seats - f.available_seats) AS total_passengers,
    AVG(CAST((ac.total_seats - f.available_seats) * 100.0 / ac.total_seats AS DECIMAL(5,2))) AS avg_occupancy_rate,
    SUM(CASE WHEN r.payment_status = 'Paid' THEN r.total_price ELSE 0 END) AS total_revenue,
    COUNT(DISTINCT r.reservation_id) AS total_bookings
FROM AIRLINES al
INNER JOIN FLIGHTS f ON al.airline_id = f.airline_id
INNER JOIN AIRCRAFT ac ON f.aircraft_id = ac.aircraft_id
LEFT JOIN RESERVATIONS r ON f.flight_id = r.flight_id
GROUP BY al.airline_id, al.airline_name, al.airline_code;
GO


-- VIEW 5: Daily Revenue Report

CREATE OR ALTER VIEW VW_DailyRevenue
AS
SELECT 
    CAST(r.booking_date AS DATE) AS booking_date,
    COUNT(r.reservation_id) AS total_bookings,
    SUM(r.total_price) AS gross_revenue,
    SUM(CASE WHEN r.payment_status = 'Paid' THEN r.total_price ELSE 0 END) AS paid_revenue,
    SUM(CASE WHEN r.reservation_status = 'Cancelled' THEN r.total_price ELSE 0 END) AS cancelled_revenue,
    COUNT(DISTINCT r.passenger_id) AS unique_passengers
FROM RESERVATIONS r
GROUP BY CAST(r.booking_date AS DATE);
GO

PRINT 'All views created successfully!';
PRINT 'Total Views: 5';
GO


-- SAMPLE DATA INSERTION WITH ERROR HANDLING

PRINT '';
PRINT 'Checking for existing data...';
GO

-- Clear existing data if script is run multiple times
IF EXISTS (SELECT 1 FROM RESERVATIONS) OR 
   EXISTS (SELECT 1 FROM PAYMENTS)
BEGIN
    PRINT 'Existing data found. Cleaning up...';

    DELETE FROM PAYMENTS;
    DBCC CHECKIDENT ('PAYMENTS', RESEED, 0);

    DELETE FROM RESERVATIONS;
    DBCC CHECKIDENT ('RESERVATIONS', RESEED, 0);

    DELETE FROM FLIGHTS;
    DBCC CHECKIDENT ('FLIGHTS', RESEED, 0);

    DELETE FROM USERS;
    DBCC CHECKIDENT ('USERS', RESEED, 0);

    DELETE FROM PASSENGERS;
    DBCC CHECKIDENT ('PASSENGERS', RESEED, 0);

    DELETE FROM AIRCRAFT;
    DBCC CHECKIDENT ('AIRCRAFT', RESEED, 0);

    DELETE FROM AIRPORTS;
    DBCC CHECKIDENT ('AIRPORTS', RESEED, 0);

    DELETE FROM AIRLINES;
    DBCC CHECKIDENT ('AIRLINES', RESEED, 0);
    PRINT 'Cleanup complete.';
END
GO

PRINT 'Inserting sample data...';
GO

-- Insert Airlines
IF NOT EXISTS (SELECT 1 FROM AIRLINES)
BEGIN
    INSERT INTO AIRLINES (airline_name, airline_code, country, contact_number, email) VALUES
    ('Pakistan International Airlines', 'PIA', 'Pakistan', '+92-111-786-786', 'contact@piac.com.pk'),
    ('Emirates', 'EK', 'UAE', '+971-4-214-4444', 'support@emirates.com'),
    ('Qatar Airways', 'QR', 'Qatar', '+974-4023-0000', 'support@qatarairways.com'),
    ('Turkish Airlines', 'TK', 'Turkey', '+90-212-444-0849', 'callcenter@thy.com'),
    ('Air Arabia', 'G9', 'UAE', '+971-6-508-8888', 'customercare@airarabia.com');
    
    PRINT '5 Airlines inserted';
END
ELSE
    PRINT 'Airlines already exist, skipping...';
GO

-- Insert Airports
IF NOT EXISTS (SELECT 1 FROM AIRPORTS)
BEGIN
    INSERT INTO AIRPORTS (airport_code, airport_name, city, country, timezone, latitude, longitude) VALUES
    ('LHE', 'Allama Iqbal International Airport', 'Lahore', 'Pakistan', 'PKT', 31.521600, 74.403600),
    ('KHI', 'Jinnah International Airport', 'Karachi', 'Pakistan', 'PKT', 24.906500, 67.160800),
    ('ISB', 'Islamabad International Airport', 'Islamabad', 'Pakistan', 'PKT', 33.616900, 73.099200),
    ('DXB', 'Dubai International Airport', 'Dubai', 'UAE', 'GST', 25.252800, 55.364400),
    ('DOH', 'Hamad International Airport', 'Doha', 'Qatar', 'AST', 25.273100, 51.608100),
    ('IST', 'Istanbul Airport', 'Istanbul', 'Turkey', 'TRT', 41.275300, 28.751900),
    ('LHR', 'Heathrow Airport', 'London', 'UK', 'GMT', 51.470000, -0.454300),
    ('JFK', 'John F Kennedy International', 'New York', 'USA', 'EST', 40.639800, -73.778900),
    ('SHJ', 'Sharjah International Airport', 'Sharjah', 'UAE', 'GST', 25.328600, 55.517200),
    ('MCT', 'Muscat International Airport', 'Muscat', 'Oman', 'GST', 23.593300, 58.284400);
    
    PRINT '10 Airports inserted';
END
ELSE
    PRINT 'Airports already exist, skipping...';
GO

-- Insert Aircraft
IF NOT EXISTS (SELECT 1 FROM AIRCRAFT)
BEGIN
    INSERT INTO AIRCRAFT (airline_id, aircraft_model, registration_number, total_seats, economy_seats, business_seats, first_class_seats, manufacturing_year, status) VALUES
    (1, 'Boeing 777-300ER', 'AP-BHV', 409, 340, 60, 9, 2015, 'Active'),
    (1, 'Airbus A320', 'AP-BLD', 162, 150, 12, 0, 2018, 'Active'),
    (2, 'Airbus A380-800', 'A6-EUA', 517, 399, 76, 42, 2017, 'Active'),
    (2, 'Boeing 777-300ER', 'A6-EMW', 354, 304, 42, 8, 2016, 'Active'),
    (3, 'Boeing 787-9', 'A7-BCP', 311, 247, 52, 12, 2019, 'Active'),
    (3, 'Airbus A350-900', 'A7-ALH', 283, 247, 36, 0, 2020, 'Active'),
    (4, 'Boeing 737-800', 'TC-JGU', 171, 159, 12, 0, 2014, 'Active'),
    (4, 'Airbus A330-300', 'TC-JOC', 289, 249, 40, 0, 2013, 'Active'),
    (5, 'Airbus A320-200', 'A6-ANV', 168, 156, 12, 0, 2017, 'Active'),
    (5, 'Airbus A321-200', 'A6-AOS', 220, 200, 20, 0, 2019, 'Active');
    
    PRINT '10 Aircraft inserted';
END
ELSE
    PRINT 'Aircraft already exist, skipping...';
GO

-- Insert Passengers
IF NOT EXISTS (SELECT 1 FROM PASSENGERS)
BEGIN
    INSERT INTO PASSENGERS (first_name, last_name, date_of_birth, gender, nationality, passport_number, passport_expiry_date, email, phone_number) VALUES
    ('Ahmed', 'Khan', '1990-05-15', 'Male', 'Pakistani', 'AB1234567', '2027-12-31', 'ahmed.khan@email.com', '+92-300-1234567'),
    ('Sarah', 'Ali', '1985-08-22', 'Female', 'Pakistani', 'CD2345678', '2026-06-30', 'sarah.ali@email.com', '+92-321-2345678'),
    ('Muhammad', 'Hassan', '1992-11-10', 'Male', 'Pakistani', 'EF3456789', '2028-03-15', 'm.hassan@email.com', '+92-333-3456789'),
    ('Fatima', 'Malik', '1988-03-25', 'Female', 'Pakistani', 'GH4567890', '2027-09-20', 'fatima.malik@email.com', '+92-345-4567890'),
    ('Ali', 'Raza', '1995-07-18', 'Male', 'Pakistani', 'IJ5678901', '2029-01-10', 'ali.raza@email.com', '+92-300-5678901'),
    ('Ayesha', 'Ahmed', '1991-12-05', 'Female', 'Pakistani', 'KL6789012', '2026-11-25', 'ayesha.ahmed@email.com', '+92-321-6789012'),
    ('Usman', 'Sheikh', '1987-09-30', 'Male', 'Pakistani', 'MN7890123', '2028-07-14', 'usman.sheikh@email.com', '+92-333-7890123'),
    ('Zainab', 'Hussain', '1993-04-12', 'Female', 'Pakistani', 'OP8901234', '2027-05-08', 'zainab.hussain@email.com', '+92-345-8901234'),
    ('Bilal', 'Siddiqui', '1989-06-28', 'Male', 'Pakistani', 'QR9012345', '2029-02-19', 'bilal.siddiqui@email.com', '+92-300-9012345'),
    ('Hira', 'Tariq', '1994-10-15', 'Female', 'Pakistani', 'ST0123456', '2026-12-30', 'hira.tariq@email.com', '+92-321-0123456');
    
    PRINT '10 Passengers inserted';
END
ELSE
    PRINT 'Passengers already exist, skipping...';
GO

-- Insert Users
IF NOT EXISTS (SELECT 1 FROM USERS)
BEGIN
    INSERT INTO USERS (username, password_hash, email, role, passenger_id) VALUES
    ('admin', 'admin123hash', 'admin@flightreservation.com', 'Admin', NULL),
    ('umar', '123', 'umar@example.com', 'Admin', NULL),
    ('agent1', 'agent123hash', 'agent1@flightreservation.com', 'Agent', NULL),
    ('ahmed_khan', 'pass123hash', 'ahmed.khan@email.com', 'Customer', 1),
    ('sarah_ali', 'pass123hash', 'sarah.ali@email.com', 'Customer', 2),
    ('m_hassan', 'pass123hash', 'm.hassan@email.com', 'Customer', 3),
    ('fatima_m', 'pass123hash', 'fatima.malik@email.com', 'Customer', 4),
    ('ali_raza', 'pass123hash', 'ali.raza@email.com', 'Customer', 5);
    
    PRINT '7 Users inserted';
END
ELSE
    PRINT 'Users already exist, skipping...';
GO

-- Insert Flights (Next 30 days)
IF NOT EXISTS (SELECT 1 FROM FLIGHTS)
BEGIN
    DECLARE @baseDate DATETIME = GETDATE();

    INSERT INTO FLIGHTS (airline_id, aircraft_id, flight_number, departure_airport_id, arrival_airport_id, departure_datetime, arrival_datetime, base_price, available_seats, status, gate_number) VALUES
    -- PIA Flights
    (1, 1, 'PK-301', 1, 4, DATEADD(DAY, 1, @baseDate), DATEADD(HOUR, 3, DATEADD(DAY, 1, @baseDate)), 25000, 409, 'Scheduled', 'A12'),
    (1, 2, 'PK-302', 2, 5, DATEADD(DAY, 2, @baseDate), DATEADD(HOUR, 2, DATEADD(DAY, 2, @baseDate)), 22000, 162, 'Scheduled', 'B5'),
    (1, 1, 'PK-303', 3, 6, DATEADD(DAY, 3, @baseDate), DATEADD(HOUR, 5, DATEADD(DAY, 3, @baseDate)), 35000, 409, 'Scheduled', 'C8'),
    -- Emirates Flights
    (2, 3, 'EK-601', 4, 7, DATEADD(DAY, 2, @baseDate), DATEADD(HOUR, 7, DATEADD(DAY, 2, @baseDate)), 45000, 517, 'Scheduled', 'D15'),
    (2, 4, 'EK-602', 4, 8, DATEADD(DAY, 4, @baseDate), DATEADD(HOUR, 14, DATEADD(DAY, 4, @baseDate)), 85000, 354, 'Scheduled', 'E22'),
    (2, 3, 'EK-603', 1, 4, DATEADD(DAY, 5, @baseDate), DATEADD(HOUR, 3, DATEADD(DAY, 5, @baseDate)), 28000, 517, 'Scheduled', 'A18'),
    -- Qatar Airways Flights
    (3, 5, 'QR-701', 5, 7, DATEADD(DAY, 3, @baseDate), DATEADD(HOUR, 7, DATEADD(DAY, 3, @baseDate)), 42000, 311, 'Scheduled', 'F10'),
    (3, 6, 'QR-702', 2, 5, DATEADD(DAY, 4, @baseDate), DATEADD(HOUR, 2, DATEADD(DAY, 4, @baseDate)), 20000, 283, 'Scheduled', 'G7'),
    (3, 5, 'QR-703', 3, 5, DATEADD(DAY, 6, @baseDate), DATEADD(HOUR, 2, DATEADD(DAY, 6, @baseDate)), 21000, 311, 'Scheduled', 'H12'),
    -- Turkish Airlines Flights
    (4, 7, 'TK-801', 1, 6, DATEADD(DAY, 5, @baseDate), DATEADD(HOUR, 5, DATEADD(DAY, 5, @baseDate)), 32000, 171, 'Scheduled', 'I20'),
    (4, 8, 'TK-802', 6, 7, DATEADD(DAY, 6, @baseDate), DATEADD(HOUR, 4, DATEADD(DAY, 6, @baseDate)), 38000, 289, 'Scheduled', 'J25'),
    (4, 7, 'TK-803', 2, 6, DATEADD(DAY, 7, @baseDate), DATEADD(HOUR, 5, DATEADD(DAY, 7, @baseDate)), 33000, 171, 'Scheduled', 'K14'),
    -- Air Arabia Flights
    (5, 9, 'G9-501', 1, 9, DATEADD(DAY, 1, @baseDate), DATEADD(HOUR, 3, DATEADD(DAY, 1, @baseDate)), 18000, 168, 'Scheduled', 'L5'),
    (5, 10, 'G9-502', 2, 10, DATEADD(DAY, 2, @baseDate), DATEADD(HOUR, 2, DATEADD(DAY, 2, @baseDate)), 19000, 220, 'Scheduled', 'M8'),
    (5, 9, 'G9-503', 3, 4, DATEADD(DAY, 3, @baseDate), DATEADD(HOUR, 3, DATEADD(DAY, 3, @baseDate)), 17000, 168, 'Scheduled', 'N11');
    
    PRINT '15 Flights inserted';
END
ELSE
    PRINT ' Flights already exist, skipping...';
GO

-- Insert Sample Reservations
IF NOT EXISTS (SELECT 1 FROM RESERVATIONS)
BEGIN
    INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, seat_number, class_type, total_price, payment_status, reservation_status) VALUES
    (1, 1, 'AB100001', 'E12A', 'Economy', 25000, 'Paid', 'Confirmed'),
    (2, 1, 'AB100002', 'E12B', 'Economy', 25000, 'Paid', 'Confirmed'),
    (3, 2, 'CD200001', 'E5A', 'Economy', 22000, 'Paid', 'Confirmed'),
    (4, 3, 'EF300001', 'B3C', 'Business', 87500, 'Paid', 'Confirmed'),
    (5, 4, 'GH400001', 'F8D', 'First Class', 180000, 'Pending', 'Confirmed'),
    (6, 5, 'IJ500001', 'E15B', 'Economy', 85000, 'Paid', 'Confirmed'),
    (7, 6, 'KL600001', 'E20A', 'Economy', 28000, 'Paid', 'Confirmed'),
    (8, 7, 'MN700001', 'B5A', 'Business', 105000, 'Paid', 'Confirmed'),
    (9, 8, 'OP800001', 'E10C', 'Economy', 20000, 'Paid', 'Confirmed'),
    (10, 9, 'QR900001', 'E18D', 'Economy', 21000, 'Pending', 'Confirmed');
    
    PRINT '10 Reservations inserted';
END
ELSE
    PRINT 'Reservations already exist, skipping...';
GO

-- Insert Sample Payments
IF NOT EXISTS (SELECT 1 FROM PAYMENTS)
BEGIN
    INSERT INTO PAYMENTS (reservation_id, payment_method, amount, transaction_id, payment_status, card_last_four) VALUES
    (1, 'Credit Card', 25000, 'TXN20250001', 'Success', '1234'),
    (2, 'Debit Card', 25000, 'TXN20250002', 'Success', '5678'),
    (3, 'Credit Card', 22000, 'TXN20250003', 'Success', '9012'),
    (4, 'PayPal', 87500, 'TXN20250004', 'Success', NULL),
    (6, 'Credit Card', 85000, 'TXN20250005', 'Success', '3456'),
    (7, 'Bank Transfer', 28000, 'TXN20250006', 'Success', NULL),
    (8, 'Credit Card', 105000, 'TXN20250007', 'Success', '7890'),
    (9, 'Debit Card', 20000, 'TXN20250008', 'Success', '2345');
    
    PRINT '8 Payments inserted';
END
ELSE
    PRINT 'Payments already exist, skipping...';
GO


PRINT '';
PRINT '========================================';
PRINT 'DATABASE SETUP COMPLETE!';
PRINT '========================================';
PRINT 'Summary:';
PRINT '- 5 Airlines';
PRINT '- 10 Airports';
PRINT '- 10 Aircraft';
PRINT '- 10 Passengers';
PRINT '- 7 Users';
PRINT '- 15 Flights';
PRINT '- 10 Reservations';
PRINT '- 8 Payments';

PRINT '========================================';
GO

-- Final verification
SELECT 'Tables' AS Type, COUNT(*) AS Count 
FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'
UNION ALL
SELECT 'Stored Procedures', COUNT(*) 
FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'PROCEDURE'
UNION ALL
SELECT 'Functions', COUNT(*) 
FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'FUNCTION'
UNION ALL
SELECT 'Views', COUNT(*) 
FROM INFORMATION_SCHEMA.VIEWS
UNION ALL
SELECT 'Triggers', COUNT(*) 
FROM sys.triggers WHERE parent_class = 1;

SELECT 'Airlines' AS Table_Name, COUNT(*) AS Record_Count FROM AIRLINES
UNION ALL SELECT 'Airports', COUNT(*) FROM AIRPORTS
UNION ALL SELECT 'Aircraft', COUNT(*) FROM AIRCRAFT
UNION ALL SELECT 'Passengers', COUNT(*) FROM PASSENGERS
UNION ALL SELECT 'Users', COUNT(*) FROM USERS
UNION ALL SELECT 'Flights', COUNT(*) FROM FLIGHTS
UNION ALL SELECT 'Reservations', COUNT(*) FROM RESERVATIONS
UNION ALL SELECT 'Payments', COUNT(*) FROM PAYMENTS;
GO

PRINT '';
PRINT '========================================';
PRINT ' ALL DATABASE OBJECTS VERIFIED!';
PRINT '========================================';
GO