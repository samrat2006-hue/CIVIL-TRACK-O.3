
import sqlite3
from pathlib import Path


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE_PATH = Path(__file__).resolve().parent / "civictrack.db"

PRIMARY_ADMIN_EMAIL = "gangulyrohit2008@gmail.com"


# --------------------------------------------------
# DATABASE UPGRADE
# --------------------------------------------------

def upgrade_database():

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        print("\nStarting CivicTrack database upgrade...")

        # 1. Verify the primary administrator.
        admin = connection.execute(
            """
            SELECT id, full_name, email, role, is_active
            FROM users
            WHERE email = ?
              AND role = 'admin'
            """,
            (PRIMARY_ADMIN_EMAIL,)
        ).fetchone()

        if admin is None:
            raise RuntimeError(
                "Primary administrator was not found. "
                "No cleanup has been performed."
            )

        if admin["is_active"] != 1:
            raise RuntimeError(
                "Primary administrator is inactive. "
                "No cleanup has been performed."
            )

        admin_id = admin["id"]

        print(
            f"Verified primary administrator: "
            f"{admin['full_name']} ({admin['email']})"
        )

        # 2. Add security-question fields if missing.
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        if "security_question" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN security_question TEXT
                """
            )
            print("Added security_question column.")

        if "security_answer_hash" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN security_answer_hash TEXT
                """
            )
            print("Added security_answer_hash column.")

        # 3. Create secure OTP storage.
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

        print("Created OTP storage table.")

        # 4. Count existing records before cleanup.
        account_counts = connection.execute(
            """
            SELECT role, COUNT(*) AS total
            FROM users
            GROUP BY role
            """
        ).fetchall()

        print("\nAccounts before cleanup:")
        for row in account_counts:
            print(f"{row['role']}: {row['total']}")

        complaint_count = connection.execute(
            "SELECT COUNT(*) FROM complaints"
        ).fetchone()[0]

        history_count = connection.execute(
            "SELECT COUNT(*) FROM status_history"
        ).fetchone()[0]

        print(f"Complaints before cleanup: {complaint_count}")
        print(f"History records before cleanup: {history_count}")

        # 5. Remove existing complaint history and complaints.
        connection.execute("DELETE FROM status_history")
        connection.execute("DELETE FROM complaints")

        # 6. Preserve the primary administrator only.
        connection.execute(
            "DELETE FROM users WHERE id <> ?",
            (admin_id,)
        )

        # 7. Confirm the primary administrator remains.
        remaining_users = connection.execute(
            """
            SELECT id, full_name, email, role, is_active
            FROM users
            """
        ).fetchall()

        if len(remaining_users) != 1:
            raise RuntimeError(
                "Unexpected remaining account count. "
                "The transaction will be rolled back."
            )

        remaining_admin = remaining_users[0]

        if (
            remaining_admin["email"] != PRIMARY_ADMIN_EMAIL
            or remaining_admin["role"] != "admin"
            or remaining_admin["is_active"] != 1
        ):
            raise RuntimeError(
                "Primary administrator verification failed. "
                "The transaction will be rolled back."
            )

        # 8. Commit all changes together.
        connection.commit()

        print("\n========== UPGRADE SUCCESSFUL ==========")
        print("Primary administrator preserved:")
        print(remaining_admin["email"])
        print("Remaining accounts: 1")
        print("Remaining complaints: 0")
        print("Remaining history records: 0")
        print("Security-question columns: ready")
        print("OTP storage: ready")
        print("\nDatabase upgrade completed successfully.")

    except Exception:
        connection.rollback()
        print("\nUPGRADE FAILED.")
        print("All database changes were rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    upgrade_database()
