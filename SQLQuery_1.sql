
-- Flight Reservation System - Database Schema
-- M S SQL Server Database


USE master;
GO

-- Drop database if exists
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'FlightReservationDB')
BEGIN
    ALTER DATABASE FlightReservationDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE FlightReservationDB;
END
GO

-- Create database
CREATE DATABASE FlightReservationDB;
GO

USE FlightReservationDB;
GO


-- TABLE 1: AIRLINES

CREATE TABLE AIRLINES (
    airline_id INT IDENTITY(1,1) PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    airline_code VARCHAR(10) NOT NULL UNIQUE,
    country VARCHAR(50) NOT NULL,
    contact_number VARCHAR(20),
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive')),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_airline_email CHECK (email LIKE '%_@__%.__%')
);


-- TABLE 2: AIRPORTS

CREATE TABLE AIRPORTS (
    airport_id INT IDENTITY(1,1) PRIMARY KEY,
    airport_code VARCHAR(10) NOT NULL UNIQUE,
    airport_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    timezone VARCHAR(50),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    status VARCHAR(20) DEFAULT 'Operational' CHECK (status IN ('Operational', 'Closed', 'Under Maintenance')),
    created_date DATETIME DEFAULT GETDATE()
);


-- TABLE 3: AIRCRAFT

CREATE TABLE AIRCRAFT (
    aircraft_id INT IDENTITY(1,1) PRIMARY KEY,
    airline_id INT NOT NULL,
    aircraft_model VARCHAR(50) NOT NULL,
    registration_number VARCHAR(20) NOT NULL UNIQUE,
    total_seats INT NOT NULL CHECK (total_seats > 0),
    economy_seats INT NOT NULL CHECK (economy_seats > 0),
    business_seats INT NOT NULL CHECK (business_seats > 0),
    first_class_seats INT NOT NULL CHECK (first_class_seats >= 0),
    manufacturing_year INT CHECK (manufacturing_year BETWEEN 1950 AND YEAR(GETDATE())),
    last_maintenance_date DATE,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Maintenance', 'Retired')),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Aircraft_Airline FOREIGN KEY (airline_id) REFERENCES AIRLINES(airline_id) ON DELETE CASCADE,
    CONSTRAINT CHK_total_seats CHECK (total_seats = economy_seats + business_seats + first_class_seats)
);


-- TABLE 4: PASSENGERS

CREATE TABLE PASSENGERS (
    passenger_id INT IDENTITY(1,1) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < GETDATE()),
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    nationality VARCHAR(50) NOT NULL,
    passport_number VARCHAR(20) NOT NULL UNIQUE,
    passport_expiry_date DATE NOT NULL CHECK (passport_expiry_date > GETDATE()),
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    frequent_flyer_number VARCHAR(20) NULL,
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_passenger_email CHECK (email LIKE '%_@__%.__%'),
    CONSTRAINT CHK_passenger_age CHECK (DATEDIFF(YEAR, date_of_birth, GETDATE()) >= 0)
);



-- TABLE 5: USERS (System Access)

CREATE TABLE USERS (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Agent', 'Customer')),
    passenger_id INT NULL,
    is_active BIT DEFAULT 1,
    last_login DATETIME,
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Users_Passenger FOREIGN KEY (passenger_id) REFERENCES PASSENGERS(passenger_id) ON DELETE SET NULL,
    CONSTRAINT CHK_user_email CHECK (email LIKE '%_@__%.__%')
);


-- TABLE 6: FLIGHTS

CREATE TABLE FLIGHTS (
    flight_id INT IDENTITY(1,1) PRIMARY KEY,
    airline_id INT NOT NULL,
    aircraft_id INT NOT NULL,
    flight_number VARCHAR(20) NOT NULL,
    departure_airport_id INT NOT NULL,
    arrival_airport_id INT NOT NULL,
    departure_datetime DATETIME NOT NULL,
    arrival_datetime DATETIME NOT NULL,
    flight_duration_minutes AS DATEDIFF(MINUTE, departure_datetime, arrival_datetime) PERSISTED,
    base_price DECIMAL(10,2) NOT NULL CHECK (base_price > 0),
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    status VARCHAR(20) DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Boarding', 'Departed', 'Arrived', 'Cancelled', 'Delayed')),
    gate_number VARCHAR(10),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Flight_Airline FOREIGN KEY (airline_id) REFERENCES AIRLINES(airline_id) ON DELETE NO ACTION,
    CONSTRAINT FK_Flight_Aircraft FOREIGN KEY (aircraft_id) REFERENCES AIRCRAFT(aircraft_id) ON DELETE NO ACTION,
    CONSTRAINT FK_Flight_Departure FOREIGN KEY (departure_airport_id) REFERENCES AIRPORTS(airport_id) ON DELETE NO ACTION,
    CONSTRAINT FK_Flight_Arrival FOREIGN KEY (arrival_airport_id) REFERENCES AIRPORTS(airport_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_arrival_after_departure CHECK (arrival_datetime > departure_datetime),
    CONSTRAINT CHK_different_airports CHECK (departure_airport_id != arrival_airport_id),
    CONSTRAINT UQ_flight_schedule UNIQUE (flight_number, departure_datetime)
);

-- TABLE 7: RESERVATIONS

CREATE TABLE RESERVATIONS (
    reservation_id INT IDENTITY(1,1) PRIMARY KEY,
    passenger_id INT NOT NULL,
    flight_id INT NOT NULL,
    booking_reference VARCHAR(10) NOT NULL UNIQUE,
    seat_number VARCHAR(5),
    class_type VARCHAR(20) NOT NULL CHECK (class_type IN ('Economy', 'Business', 'First Class')),
    booking_date DATETIME DEFAULT GETDATE(),
    total_price DECIMAL(10,2) NOT NULL CHECK (total_price > 0),
    payment_status VARCHAR(20) DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Paid', 'Refunded', 'Cancelled')),
    reservation_status VARCHAR(20) DEFAULT 'Confirmed' CHECK (reservation_status IN ('Confirmed', 'Cancelled', 'Completed', 'No-Show', 'Checked-In')),
    special_requests VARCHAR(500),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Reservation_Passenger FOREIGN KEY (passenger_id) REFERENCES PASSENGERS(passenger_id) ON DELETE NO ACTION,
    CONSTRAINT FK_Reservation_Flight FOREIGN KEY (flight_id) REFERENCES FLIGHTS(flight_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_seat_per_flight UNIQUE (flight_id, seat_number)
);

-- TABLE 8: PAYMENTS

CREATE TABLE PAYMENTS (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    reservation_id INT NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer', 'Cash')),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    payment_date DATETIME DEFAULT GETDATE(),
    transaction_id VARCHAR(100) UNIQUE,
    payment_status VARCHAR(20) DEFAULT 'Pending' CHECK (payment_status IN ('Success', 'Failed', 'Pending', 'Refunded')),
    card_last_four VARCHAR(4),
    notes VARCHAR(200),
    CONSTRAINT FK_Payment_Reservation FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE CASCADE
);


-- TABLE 9: AUDIT_LOG (For tracking changes)

CREATE TABLE AUDIT_LOG (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id INT,
    old_value VARCHAR(MAX),
    new_value VARCHAR(MAX),
    changed_by VARCHAR(50),
    changed_date DATETIME DEFAULT GETDATE()
);

PRINT 'Database schema created successfully!';
PRINT 'Total tables created: 12';
GO