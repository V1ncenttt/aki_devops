CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- Patients Table
CREATE TABLE Patients (
    mrn VARCHAR(50) PRIMARY KEY,
    age INT,
    sex ENUM('M', 'F', 'Other')
);

-- Measurements Table
CREATE TABLE Measurements (
    mrn VARCHAR(50),
    measurement_date DATETIME,
    measurement_value FLOAT,
    PRIMARY KEY (mrn, measurement_date),
    FOREIGN KEY (mrn) REFERENCES Patients(mrn) ON DELETE CASCADE
);

-- Index for fast lookups of measurements by mrn
CREATE INDEX idx_measurements_mrn ON Measurements(mrn);

-- Index for fast queries on measurement_date
CREATE INDEX idx_measurements_date ON Measurements(measurement_date);

-- Use SQL dump????