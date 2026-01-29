
USE master;
GO

PRINT 'Starting complete database reset...';
GO

-- Drop database if exists (this removes EVERYTHING)
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'FlightReservationDB')
BEGIN
    PRINT 'Dropping existing database...';
    ALTER DATABASE FlightReservationDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE FlightReservationDB;
    PRINT '✓ Old database dropped';
END
GO

-- Create fresh database
PRINT 'Creating fresh database...';
CREATE DATABASE FlightReservationDB;
GO

USE FlightReservationDB;
GO

PRINT ' Fresh database created successfully!';
PRINT '';
PRINT '========================================';
PRINT 'DATABASE RESET COMPLETE!';
PRINT '========================================';
PRINT '';
PRINT 'NEXT STEPS:';
PRINT '1. Run SQLQuery_1.sql (Schema)';
PRINT '2. Run SQLQuery_2.sql (Indexes)';
PRINT '3. Run SQLQuery_3.sql (Stored Procedures)';
PRINT '4. Run SQLQuery_4.sql (Functions & Triggers)';
PRINT '5. Run SQLQuery_5.sql (Views & Sample Data)';
PRINT '========================================';
GO