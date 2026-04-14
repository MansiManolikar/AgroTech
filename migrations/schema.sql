CREATE DATABASE IF NOT EXISTS irrigation_portal;
USE irrigation_portal;

-- Users (farmers + agronomist operators)
CREATE TABLE IF NOT EXISTS users (
   id            INT AUTO_INCREMENT PRIMARY KEY,
   name          VARCHAR(120) NOT NULL,
   email         VARCHAR(150) NOT NULL UNIQUE,
   phone         VARCHAR(20),
   password_hash VARCHAR(255) NOT NULL,
   role          ENUM('farmer','operator') NOT NULL DEFAULT 'farmer',
   language      VARCHAR(10) DEFAULT 'en',
   notif_sms     TINYINT(1) DEFAULT 1,
   notif_email   TINYINT(1) DEFAULT 1,
   created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
   is_active     TINYINT(1) DEFAULT 1
);

-- Farm Profiles
CREATE TABLE IF NOT EXISTS farm_profiles (
   id          INT AUTO_INCREMENT PRIMARY KEY,
   user_id     INT NOT NULL,
   farm_name   VARCHAR(150) NOT NULL,
   address     TEXT,
   latitude    DECIMAL(10,7),
   longitude   DECIMAL(10,7),
   pincode     VARCHAR(10),
   total_area  DECIMAL(10,2) COMMENT 'in acres',
   created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Agro-Zones
CREATE TABLE IF NOT EXISTS agro_zones (
   id          INT AUTO_INCREMENT PRIMARY KEY,
   farm_id     INT NOT NULL,
   zone_name   VARCHAR(100) NOT NULL,
   area        DECIMAL(10,2) COMMENT 'in acres',
   soil_type   VARCHAR(80),
   created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (farm_id) REFERENCES farm_profiles(id) ON DELETE CASCADE
);

-- Crop Catalog
CREATE TABLE IF NOT EXISTS crop_catalog (
   id              INT AUTO_INCREMENT PRIMARY KEY,
   crop_name       VARCHAR(100) NOT NULL,
   crop_type       VARCHAR(80),
   season          VARCHAR(50),
   water_req_mm    DECIMAL(8,2) COMMENT 'mm per day',
   growth_days     INT,
   created_by      INT,
   created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Zone-Crop Assignments
CREATE TABLE IF NOT EXISTS zone_crops (
   id             INT AUTO_INCREMENT PRIMARY KEY,
   zone_id        INT NOT NULL,
   crop_id        INT NOT NULL,
   sow_date       DATE,
   expected_harvest DATE,
   current_stage  VARCHAR(80),
   assigned_by    INT,
   created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (zone_id) REFERENCES agro_zones(id) ON DELETE CASCADE,
   FOREIGN KEY (crop_id) REFERENCES crop_catalog(id),
   FOREIGN KEY (assigned_by) REFERENCES users(id)
);

-- IoT Sensors linked to zones
CREATE TABLE IF NOT EXISTS sensors (
   id           INT AUTO_INCREMENT PRIMARY KEY,
   zone_id      INT NOT NULL,
   sensor_type  ENUM('soil_moisture','weather','rain') NOT NULL,
   sensor_uid   VARCHAR(100) UNIQUE,
   installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   is_active    TINYINT(1) DEFAULT 1,
   FOREIGN KEY (zone_id) REFERENCES agro_zones(id) ON DELETE CASCADE
);

-- Irrigation Schedules
CREATE TABLE IF NOT EXISTS irrigation_schedules (
   id               INT AUTO_INCREMENT PRIMARY KEY,
   zone_id          INT NOT NULL,
   scheduled_date   DATE NOT NULL,
   scheduled_time   TIME NOT NULL,
   duration_mins    INT NOT NULL,
   method           ENUM('drip','sprinkler','flood') NOT NULL,
   status           ENUM('pending','completed','skipped','conflict') DEFAULT 'pending',
   rain_skip        TINYINT(1) DEFAULT 0,
   created_by       INT,
   created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (zone_id) REFERENCES agro_zones(id) ON DELETE CASCADE,
   FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Threshold Alerts Config
CREATE TABLE IF NOT EXISTS alert_thresholds (
   id                  INT AUTO_INCREMENT PRIMARY KEY,
   zone_id             INT NOT NULL,
   moisture_low_pct    DECIMAL(5,2) DEFAULT 30.00,
   moisture_high_pct   DECIMAL(5,2) DEFAULT 80.00,
   rain_avoid_mm       DECIMAL(5,2) DEFAULT 5.00,
   notify_sms          TINYINT(1) DEFAULT 1,
   notify_email        TINYINT(1) DEFAULT 1,
   created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (zone_id) REFERENCES agro_zones(id) ON DELETE CASCADE
);

-- Advisory Subscriptions
CREATE TABLE IF NOT EXISTS advisory_subscriptions (
   id         INT AUTO_INCREMENT PRIMARY KEY,
   user_id    INT NOT NULL,
   zone_id    INT NOT NULL,
   is_active  TINYINT(1) DEFAULT 1,
   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
   FOREIGN KEY (zone_id) REFERENCES agro_zones(id) ON DELETE CASCADE
);

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
   id         INT AUTO_INCREMENT PRIMARY KEY,
   user_id    INT,
   action     VARCHAR(255) NOT NULL,
   entity     VARCHAR(80),
   entity_id  INT,
   details    TEXT,
   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (user_id) REFERENCES users(id)
);