CREATE DATABASE IF NOT EXISTS asistencia_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asistencia_db;

-- Django creara sus propias tablas de usuarios, permisos y sesiones.
-- Este archivo documenta las tablas principales del dominio.

CREATE TABLE empleados (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    employee_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL DEFAULT '',
    department VARCHAR(100) NOT NULL DEFAULT '',
    position VARCHAR(100) NOT NULL DEFAULT '',
    hire_date DATE NULL,
    termination_date DATE NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL
);

CREATE TABLE horarios (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL
);

CREATE TABLE horarios_dia (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    schedule_id BIGINT NOT NULL,
    weekday SMALLINT UNSIGNED NOT NULL,
    start_time TIME(6) NOT NULL,
    end_time TIME(6) NOT NULL,
    tolerance_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 10,
    regular_hours NUMERIC(5,2) NOT NULL DEFAULT 8.00,
    is_rest_day BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE KEY uq_schedule_weekday (schedule_id, weekday)
);

CREATE TABLE empleados_horarios (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL,
    schedule_id BIGINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE asistencias (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL,
    date DATE NOT NULL,
    schedule_day_id BIGINT NULL,
    check_in_time TIME(6) NULL,
    check_out_time TIME(6) NULL,
    status VARCHAR(20) NULL,
    total_hours NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    overtime_hours NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    notes LONGTEXT NOT NULL,
    modified_by_id INT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    UNIQUE KEY uq_employee_date (employee_id, date)
);

CREATE TABLE registros_asistencia (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    attendance_id BIGINT NOT NULL,
    employee_id BIGINT NOT NULL,
    record_type VARCHAR(10) NOT NULL,
    device_date DATE NOT NULL,
    device_time TIME(6) NOT NULL,
    device_datetime DATETIME(6) NOT NULL,
    server_datetime DATETIME(6) NOT NULL,
    latitude NUMERIC(10,8) NULL,
    longitude NUMERIC(11,8) NULL,
    gps_accuracy NUMERIC(8,2) NULL,
    employee_photo VARCHAR(100) NULL,
    environment_photo VARCHAR(100) NULL,
    device_id VARCHAR(255) NOT NULL DEFAULT '',
    source_ip CHAR(39) NULL,
    created_at DATETIME(6) NOT NULL
);

CREATE TABLE justificaciones (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    attendance_id BIGINT NOT NULL,
    employee_id BIGINT NOT NULL,
    justification_type VARCHAR(20) NOT NULL,
    reason LONGTEXT NOT NULL,
    attachment VARCHAR(100) NULL,
    approved_by_id INT NOT NULL,
    approved_at DATETIME(6) NOT NULL
);
