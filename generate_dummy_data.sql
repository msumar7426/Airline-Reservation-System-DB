-- Generate Dummy Data for Analytics
USE FlightReservationDB;
GO

-- 1. Create some passengers
INSERT INTO PASSENGERS (first_name, last_name, date_of_birth, nationality, passport_number, passport_expiry_date, email, phone_number)
VALUES 
('John', 'Doe', '1985-05-15', 'USA', 'A12345678', '2030-01-01', 'john.doe@email.com', '12345678901'),
('Sarah', 'Smith', '1990-11-22', 'UK', 'B98765432', '2029-05-15', 'sarah.smith@email.com', '19876543210'),
('Ahmed', 'Khan', '1992-03-30', 'UAE', 'C11223344', '2031-12-10', 'ahmed.k@email.com', '971501234567'),
('Maria', 'Garcia', '1988-07-04', 'Spain', 'D55667788', '2028-09-20', 'maria.g@email.com', '34612345678');

-- 2. Create bookings for recent flights (Simulating past bookings for analytics)
DECLARE @p1 INT, @p2 INT, @p3 INT, @p4 INT;
SELECT @p1 = passenger_id FROM PASSENGERS WHERE email = 'john.doe@email.com';
SELECT @p2 = passenger_id FROM PASSENGERS WHERE email = 'sarah.smith@email.com';
SELECT @p3 = passenger_id FROM PASSENGERS WHERE email = 'ahmed.k@email.com';
SELECT @p4 = passenger_id FROM PASSENGERS WHERE email = 'maria.g@email.com';

-- Flight 1: Emirates Dubai -> London (Business & First)
INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, booking_date, seat_number, class_type, total_price, reservation_status, payment_status)
VALUES 
(@p1, 4, 'BK-AUTO-01', GETDATE(), '1A', 'First Class', 5000.00, 'Confirmed', 'Paid'),
(@p2, 4, 'BK-AUTO-02', GETDATE(), '2B', 'Business', 2500.00, 'Confirmed', 'Paid');

-- Flight 2: Qatar Airways Doha -> London (Economy)
INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, booking_date, seat_number, class_type, total_price, reservation_status, payment_status)
VALUES 
(@p3, 7, 'BK-AUTO-03', GETDATE(), '15A', 'Economy', 800.00, 'Confirmed', 'Paid');

-- Flight 3: Turkish Airlines Istanbul -> London
INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, booking_date, seat_number, class_type, total_price, reservation_status, payment_status)
VALUES 
(@p4, 11, 'BK-AUTO-04', GETDATE(), '12F', 'Economy', 750.00, 'Confirmed', 'Paid');

-- Flight 4: Multiple Bookings on PIA Islamabad -> Istanbul
INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, booking_date, seat_number, class_type, total_price, reservation_status, payment_status)
VALUES 
(@p1, 3, 'BK-AUTO-05', GETDATE(), '3A', 'Business', 1200.00, 'Confirmed', 'Paid'),
(@p3, 3, 'BK-AUTO-06', GETDATE(), '20D', 'Economy', 500.00, 'Confirmed', 'Paid');

PRINT 'Dummy data generated successfully.';
