import mysql.connector
import hashlib

DB_CONFIG = {
   'host': 'localhost',
   'user': 'root',
   'password': '',
   'database': 'agritech'
}

def get_db():
   return mysql.connector.connect(**DB_CONFIG)

def init_db():
   conn = mysql.connector.connect(
       host=DB_CONFIG['host'],
       user=DB_CONFIG['user'],
       password=DB_CONFIG['password']
   )
   c = conn.cursor()
   c.execute("CREATE DATABASE IF NOT EXISTS agritech")
   conn.commit()
   conn.close()

   conn = mysql.connector.connect(**DB_CONFIG)
   c = conn.cursor()

   c.execute("""
   CREATE TABLE IF NOT EXISTS users (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(255),
       email VARCHAR(255) UNIQUE,
       password TEXT,
       role VARCHAR(50),
       phone VARCHAR(20),
       security_question VARCHAR(255),
       security_answer VARCHAR(255),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   # Add columns if upgrading existing DB
   for col, defn in [
       ('security_question', 'VARCHAR(255)'),
       ('security_answer',   'VARCHAR(255)')
   ]:
       c.execute("SHOW COLUMNS FROM users LIKE %s", (col,))
       if not c.fetchone():
           c.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")

   c.execute("""
   CREATE TABLE IF NOT EXISTS agro_zones (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(255),
       region VARCHAR(255),
       soil_type VARCHAR(255),
       climate VARCHAR(255),
       description TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   c.execute("""
   CREATE TABLE IF NOT EXISTS crops (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(255),
       variety VARCHAR(255),
       growth_duration INT,
       water_requirement FLOAT,
       moisture_threshold FLOAT,
       stages TEXT,
       description TEXT
   )
   """)

   c.execute("""
   CREATE TABLE IF NOT EXISTS farms (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT,
       name VARCHAR(255),
       location VARCHAR(255),
       area FLOAT,
       crop_id INT,
       zone_id INT,
       soil_type VARCHAR(255),
       irrigation_type VARCHAR(255),
       planting_date DATE,
       zone_status VARCHAR(50) DEFAULT 'pending'
   )
   """)

   c.execute("SHOW COLUMNS FROM farms LIKE 'zone_status'")
   if not c.fetchone():
       c.execute("ALTER TABLE farms ADD COLUMN zone_status VARCHAR(50) DEFAULT 'pending'")
   c.execute("UPDATE farms SET zone_status = 'pending' WHERE zone_status IS NULL")

   c.execute("""
   CREATE TABLE IF NOT EXISTS alerts (
       id INT AUTO_INCREMENT PRIMARY KEY,
       farm_id INT,
       alert_type VARCHAR(50),
       message TEXT,
       severity VARCHAR(50),
       is_read BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   c.execute("""
   CREATE TABLE IF NOT EXISTS advisories (
       id INT AUTO_INCREMENT PRIMARY KEY,
       operator_id INT,
       title VARCHAR(255),
       content TEXT,
       crop_id INT,
       zone_id INT,
       advisory_type VARCHAR(50),
       is_published BOOLEAN DEFAULT TRUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   c.execute("""
   CREATE TABLE IF NOT EXISTS irrigation_schedules (
       id INT AUTO_INCREMENT PRIMARY KEY,
       farm_id INT,
       scheduled_date DATE,
       scheduled_time TIME,
       duration_minutes INT,
       water_amount FLOAT,
       status VARCHAR(50),
       approval_status VARCHAR(50) DEFAULT 'pending',
       reason TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   c.execute("SHOW COLUMNS FROM irrigation_schedules LIKE 'scheduled_time'")
   if not c.fetchone():
       c.execute("ALTER TABLE irrigation_schedules ADD COLUMN scheduled_time TIME AFTER scheduled_date")

   c.execute("SHOW COLUMNS FROM irrigation_schedules LIKE 'approval_status'")
   if not c.fetchone():
       c.execute("ALTER TABLE irrigation_schedules ADD COLUMN approval_status VARCHAR(50) DEFAULT 'pending' AFTER status")
   c.execute("UPDATE irrigation_schedules SET approval_status = 'pending' WHERE approval_status IS NULL")

   c.execute("""
   CREATE TABLE IF NOT EXISTS audit_logs (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT,
       action VARCHAR(255),
       details TEXT,
       ip_address VARCHAR(50),
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """)

   # Ensure a default operator account exists for first-time setup.
   c.execute("""
   INSERT INTO users (name, email, password, role, phone)
   SELECT %s, %s, %s, %s, %s
   FROM DUAL
   WHERE NOT EXISTS (
       SELECT 1 FROM users WHERE email = %s
   )
   """, (
       'Admin',
       'admin@agritech.com',
       hash_password('Admin@123'),
       'operator',
       '9874561237',
       'admin@agritech.com',
   ))

   conn.commit()
   conn.close()

def hash_password(password):
   return hashlib.sha256(password.encode()).hexdigest()

def init_notifications_table():
    """Add notifications table — called from app.py after init_db()"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(50) DEFAULT 'info',
        is_read BOOLEAN DEFAULT FALSE,
        link VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()