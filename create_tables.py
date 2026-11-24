
import sqlite3

from database.db_connection import get_connection, initialize_database


def create_tables():
    """
    Create CivicTrack database tables and update
    the OTP structure for email and SMS verification.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ------------------------------------------
        # 1. USERS TABLE
        # ------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                role TEXT NOT NULL DEFAULT 'citizen'
                    CHECK(role IN ('citizen', 'officer', 'admin')),
                department_id INTEGER,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (department_id)
                    REFERENCES departments(id)
            )
        """)

        # ------------------------------------------
        # 2. DEPARTMENTS TABLE
        # ------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ------------------------------------------
        # 3. COMPLAINTS TABLE
        # ------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT NOT NULL UNIQUE,

                citizen_id INTEGER NOT NULL,
                assigned_officer_id INTEGER,
                department_id INTEGER,

                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,

                address TEXT NOT NULL,
                latitude REAL,
                longitude REAL,

                image_path TEXT,

                severity TEXT NOT NULL DEFAULT 'Medium'
                    CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')),

                priority_score INTEGER NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(status IN (
                        'Pending',
                        'Under Review',
                        'Assigned',
                        'In Progress',
                        'Resolved',
                        'Rejected'
                    )),

                officer_remarks TEXT,
                resolution_details TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,

                FOREIGN KEY (citizen_id)
                    REFERENCES users(id),

                FOREIGN KEY (assigned_officer_id)
                    REFERENCES users(id),

                FOREIGN KEY (department_id)
                    REFERENCES departments(id)
            )
        """)

        # ------------------------------------------
        # 4. STATUS HISTORY TABLE
        # ------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                complaint_id INTEGER NOT NULL,
                updated_by INTEGER,

                old_status TEXT,
                new_status TEXT NOT NULL,
                remarks TEXT,

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (complaint_id)
                    REFERENCES complaints(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (updated_by)
                    REFERENCES users(id)
            )
        """)

        # ------------------------------------------
        # 5. PASSWORD RESET OTP TABLE
        # ------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otps (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                purpose TEXT NOT NULL
                    CHECK(purpose = 'password_reset'),

                otp_hash TEXT NOT NULL,

                delivery_method TEXT NOT NULL DEFAULT 'email'
                    CHECK(
                        delivery_method IN ('email', 'sms')
                    ),

                expires_at TEXT NOT NULL,

                attempts INTEGER NOT NULL DEFAULT 0,

                used INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # ------------------------------------------
        # 6. MIGRATE EXISTING OTP TABLE
        # ------------------------------------------

        existing_columns = {
            row["name"]
            for row in cursor.execute(
                "PRAGMA table_info(password_reset_otps)"
            ).fetchall()
        }

        if "delivery_method" not in existing_columns:

            cursor.execute("""
                ALTER TABLE password_reset_otps

                ADD COLUMN delivery_method TEXT
                    NOT NULL DEFAULT 'email'
                    CHECK(
                        delivery_method IN ('email', 'sms')
                    )
            """)

            print("Added delivery_method to existing OTP table.")

        else:

            print("OTP delivery_method column already exists.")

        # ------------------------------------------
        # 7. CREATE DATABASE INDEXES
        # ------------------------------------------

        indexes = [

            """
            CREATE INDEX IF NOT EXISTS idx_users_email
            ON users(email)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_complaints_tracking
            ON complaints(tracking_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_complaints_citizen
            ON complaints(citizen_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_complaints_officer
            ON complaints(assigned_officer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_complaints_status
            ON complaints(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_complaints_department
            ON complaints(department_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_password_reset_otps_channel
            ON password_reset_otps(
                user_id,
                purpose,
                delivery_method,
                used
            )
            """
        ]

        for query in indexes:
            cursor.execute(query)

        # ------------------------------------------
        # 8. INSERT DEFAULT DEPARTMENTS
        # ------------------------------------------

        departments = [

            (
                "Roads and Infrastructure",
                "Handles potholes, damaged roads and public infrastructure."
            ),

            (
                "Sanitation Department",
                "Handles garbage collection and sanitation complaints."
            ),

            (
                "Electricity Department",
                "Handles streetlights and public electricity complaints."
            ),

            (
                "Water Supply Department",
                "Handles water leakage and water supply complaints."
            ),

            (
                "Public Works Department",
                "Handles footpaths and other public infrastructure issues."
            )

        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO departments (
                department_name,
                description
            )
            VALUES (?, ?)
        """, departments)

        connection.commit()

        # ------------------------------------------
        # 9. VERIFY OTP DATABASE STRUCTURE
        # ------------------------------------------

        columns = [
            row["name"]
            for row in cursor.execute(
                "PRAGMA table_info(password_reset_otps)"
            ).fetchall()
        ]

        if "delivery_method" not in columns:
            raise RuntimeError(
                "OTP delivery method column was not created."
            )

        print("\n======================================")
        print("CIVICTRACK DATABASE INITIALIZATION")
        print("======================================")

        print("Users table: READY")
        print("Departments table: READY")
        print("Complaints table: READY")
        print("Status history table: READY")
        print("OTP table: READY")
        print("Email OTP channel: READY")

        print("\nExisting database records preserved.")
        print("Database initialization successful.")

    except Exception:

        connection.rollback()

        print("Database initialization failed.")
        raise

    finally:

        connection.close()


if __name__ == "__main__":
    create_tables()
