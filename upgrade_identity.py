
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "civictrack.db"

PRIMARY_ADMIN_EMAIL = "gangulyrohit2008@gmail.com"
PRIMARY_ADMIN_ID = "PRI/2026"

ADMIN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def create_backup():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = DATABASE_PATH.parent / (
        f"civictrack_before_identity_{timestamp}.db"
    )

    source = sqlite3.connect(str(DATABASE_PATH))
    destination = sqlite3.connect(str(backup_path))

    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    return backup_path


def get_columns(connection):
    return {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    }


def generate_admin_id(connection):
    while True:
        candidate = "".join(
            secrets.choice(ADMIN_ALPHABET)
            for _ in range(8)
        )

        existing = connection.execute(
            "SELECT id FROM users WHERE admin_id = ?",
            (candidate,)
        ).fetchone()

        if existing is None:
            return candidate


def generate_officer_uid(connection, length=8):
    if not 4 <= length <= 18:
        raise ValueError(
            "Officer UID length must be between 4 and 18 digits."
        )

    lower = 10 ** (length - 1)
    upper = (10 ** length) - 1

    while True:
        candidate = str(
            secrets.randbelow(upper - lower + 1) + lower
        )

        existing = connection.execute(
            "SELECT id FROM users WHERE officer_uid = ?",
            (candidate,)
        ).fetchone()

        if existing is None:
            return candidate


def upgrade_database():

    backup_path = create_backup()

    print("Database backup created:")
    print(backup_path)

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        primary = connection.execute(
            """
            SELECT id, full_name, email, role, is_active
            FROM users
            WHERE LOWER(email) = LOWER(?)
              AND role = 'admin'
            """,
            (PRIMARY_ADMIN_EMAIL,)
        ).fetchone()

        if primary is None:
            raise RuntimeError(
                "Primary administrator was not found. "
                "No migration changes were committed."
            )

        if not primary["is_active"]:
            raise RuntimeError(
                "Primary administrator is inactive."
            )

        # Add new identity and recovery columns.
        additions = {
            "admin_id": "TEXT",
            "officer_uid": "TEXT",
            "is_primary_admin": "INTEGER NOT NULL DEFAULT 0",
            "security_question": "TEXT",
            "security_answer_hash": "TEXT",
        }

        existing_columns = get_columns(connection)

        for column, definition in additions.items():

            if column not in existing_columns:

                connection.execute(
                    f"ALTER TABLE users ADD COLUMN "
                    f"{column} {definition}"
                )

                print(f"Added column: {column}")

        # Mark the primary administrator.
        connection.execute(
            """
            UPDATE users
            SET is_primary_admin = 0
            WHERE role = 'admin'
            """
        )

        connection.execute(
            """
            UPDATE users
            SET admin_id = ?,
                is_primary_admin = 1
            WHERE id = ?
            """,
            (PRIMARY_ADMIN_ID, primary["id"])
        )

        # Generate IDs for all other administrators.
        other_admins = connection.execute(
            """
            SELECT id
            FROM users
            WHERE role = 'admin'
              AND id <> ?
            """,
            (primary["id"],)
        ).fetchall()

        for admin in other_admins:

            admin_id = generate_admin_id(connection)

            connection.execute(
                """
                UPDATE users
                SET admin_id = ?,
                    is_primary_admin = 0
                WHERE id = ?
                """,
                (admin_id, admin["id"])
            )

        # Assign eight-digit UIDs to existing officers.
        officers = connection.execute(
            """
            SELECT id
            FROM users
            WHERE role = 'officer'
            """
        ).fetchall()

        for officer in officers:

            uid = generate_officer_uid(connection, 8)

            connection.execute(
                """
                UPDATE users
                SET officer_uid = ?
                WHERE id = ?
                """,
                (uid, officer["id"])
            )

        # Ensure OTP storage exists.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                purpose TEXT NOT NULL
                    CHECK (purpose = 'password_reset'),
                otp_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_password_reset_otps_user
            ON password_reset_otps(user_id, purpose, used)
            """
        )

        # Enforce unique login IDs.
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_admin_id_unique
            ON users(admin_id)
            WHERE admin_id IS NOT NULL
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_officer_uid_unique
            ON users(officer_uid)
            WHERE officer_uid IS NOT NULL
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_one_primary_admin
            ON users(is_primary_admin)
            WHERE is_primary_admin = 1
            """
        )

        # Verify the primary administrator.
        verified = connection.execute(
            """
            SELECT admin_id, is_primary_admin, role, is_active
            FROM users
            WHERE id = ?
            """,
            (primary["id"],)
        ).fetchone()

        if not (
            verified["admin_id"] == PRIMARY_ADMIN_ID
            and verified["is_primary_admin"] == 1
            and verified["role"] == "admin"
            and verified["is_active"] == 1
        ):
            raise RuntimeError(
                "Primary administrator verification failed."
            )

        connection.commit()

        print("\nIDENTITY MIGRATION SUCCESSFUL")
        print("--------------------------------")
        print("Primary Admin ID:", PRIMARY_ADMIN_ID)
        print("Existing accounts preserved.")
        print("Existing complaint records preserved.")

        print("\nOFFICER UIDs")

        for row in connection.execute(
            """
            SELECT full_name, officer_uid
            FROM users
            WHERE role = 'officer'
            ORDER BY id
            """
        ):
            print(row["full_name"], ":", row["officer_uid"])

        print("\nADMINISTRATOR IDs")

        for row in connection.execute(
            """
            SELECT full_name, admin_id
            FROM users
            WHERE role = 'admin'
            ORDER BY id
            """
        ):
            print(row["full_name"], ":", row["admin_id"])

    except Exception:

        connection.rollback()

        print("\nMIGRATION FAILED")
        print("All database changes were rolled back.")
        print("Backup:", backup_path)

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    upgrade_database()
