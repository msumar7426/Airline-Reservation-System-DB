
-- Flight Reservation System - Indexes



USE FlightReservationDB;
GO

PRINT 'Creating indexes for performance optimization...';
GO


-- FLIGHTS TABLE INDEXES


-- Index for searching flights by departure date and status
CREATE NONCLUSTERED INDEX idx_flights_departure_status
ON FLIGHTS(departure_datetime, status)
INCLUDE (flight_id, flight_number, arrival_datetime, base_price, available_seats);
GO

-- Index for searching flights by route
CREATE NONCLUSTERED INDEX idx_flights_route
ON FLIGHTS(departure_airport_id, arrival_airport_id, departure_datetime)
INCLUDE (flight_id, flight_number, airline_id, base_price, available_seats);
GO

-- Index for airline-wise flight queries
CREATE NONCLUSTERED INDEX idx_flights_airline_date
ON FLIGHTS(airline_id, departure_datetime)
INCLUDE (flight_number, status, available_seats);
GO

-- Index for flight number lookup
CREATE NONCLUSTERED INDEX idx_flights_number
ON FLIGHTS(flight_number, departure_datetime);


-- RESERVATIONS TABLE INDEXES


-- Index for flight-wise reservations
CREATE NONCLUSTERED INDEX idx_reservations_flight
ON RESERVATIONS(flight_id, reservation_status)
INCLUDE (passenger_id, seat_number, class_type);
GO




-- USERS TABLE INDEXES


-- Index for username login
CREATE NONCLUSTERED INDEX idx_users_username
ON USERS(username, is_active)
INCLUDE (user_id, password_hash, role, passenger_id);
GO

-- AIRCRAFT TABLE INDE

-- Index for airline's aircraft lookup
CREATE NONCLUSTERED INDEX idx_aircraft_airline
ON AIRCRAFT(airline_id, status)
INCLUDE (aircraft_id, aircraft_model, total_seats);
GO

-- Index for registration number lookup
CREATE NONCLUSTERED INDEX idx_aircraft_registration
ON AIRCRAFT(registration_number)
INCLUDE (aircraft_id, airline_id, status);
GO


-- AIRPORTS TABLE INDEXES

-- Index for airport code lookup
CREATE NONCLUSTERED INDEX idx_airports_code
ON AIRPORTS(airport_code)
INCLUDE (airport_id, airport_name, city, country);
GO

-- Index for city-based search
CREATE NONCLUSTERED INDEX idx_airports_city_country
ON AIRPORTS(city, country, status);
GO

-- AUDIT_LOG TABLE INDEXES

-- Index for audit tracking
CREATE NONCLUSTERED INDEX idx_audit_table_date
ON AUDIT_LOG(table_name, changed_date DESC)
INCLUDE (operation_type, record_id, changed_by);
GO

-- Index for record-specific audit
CREATE NONCLUSTERED INDEX idx_audit_record
ON AUDIT_LOG(table_name, record_id, changed_date DESC);
GO

PRINT 'All indexes created successfully!';
GO


-- VIEW INDEX STATISTICS

SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    i.is_unique AS IsUnique
FROM sys.indexes i
WHERE OBJECT_SCHEMA_NAME(i.object_id) = 'dbo'
    AND i.type > 0  -- Exclude heap
ORDER BY TableName, IndexName;
GO