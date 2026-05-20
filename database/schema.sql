-- MySQL Database Schema for Eye Diagnosis System

CREATE DATABASE IF NOT EXISTS eye_diagnosis_db;
USE eye_diagnosis_db;

-- Users table stores both patients and doctors
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient', 'doctor', 'admin') DEFAULT 'patient',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DiagnosisReports stores predictions from the AI model
CREATE TABLE IF NOT EXISTS DiagnosisReports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    image_path VARCHAR(255) NOT NULL,
    diagnosis_result VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Appointments between patients and doctors
CREATE TABLE IF NOT EXISTS Appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY(doctor_id) REFERENCES Users(id) ON DELETE CASCADE
);
