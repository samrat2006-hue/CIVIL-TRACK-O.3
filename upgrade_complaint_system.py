
import json
import sqlite3
from datetime import datetime
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "civictrack.db"
BACKUP_DIR = DATABASE_DIR / "backups"

NEW_DEPARTMENTS = [
    (
        "Sewage and stormwater drainage department",
        "Handles sewage systems, blocked drains and stormwater drainage."
    ),
    (
        "Public health and vector control department",
        "Handles public health, mosquito control and vector-related issues."
    ),
    (
        "Town planning and building control department",
        "Handles town planning, building regulations and construction control."
    ),
    (
        "Estate or encroachment removal department",
        "Handles public land encroachment and removal-related complaints."
    ),
    (
        "Parks, garden and horticulture department",
        "Handles parks, trees, gardens and public green spaces."
    ),
    (
        "Traffic and transportation cell",
        "Handles traffic management, parking and transportation issues."
    ),
    (
        "Revenue and taxation department",
        "Handles municipal property records, revenue and taxation matters."
    ),
    (
        "Fire and emergency services",
        "Handles municipal fire safety and emergency-service matters."
    ),
]


# --------------------------------------------------
# EXISTING DEPARTMENT MIGRATION
# --------------------------------------------------

LEGACY_DEPARTMENT_RENAMES = {
    1: (
        "Engineering and public works department",
        "Handles roads, footpaths and public infrastructure."
    ),
    2: (
        "Solid waste management department",
        "Handles garbage collection and solid waste management."
    ),
    3: (
        "Electrical and street lighting department",
        "Handles streetlights and public electrical infrastructure."
    ),
    4: (
        "Water supply and hydraulic engineering department",
        "Handles water supply, pipelines and hydraulic infrastructure."
    ),
}


# --------------------------------------------------
# LEGACY CATEGORY MIGRATION
# --------------------------------------------------

LEGACY_CATEGORY_MAPPING = {
    "Road Damage": (
        "Roads and footpaths",
        "Engineering and public works department"
    ),
    "Garbage / Sanitation": (
        "Garbage and sanitation",
        "Solid waste management department"
    ),
    "Streetlight / Electricity": (
        "Street lights and electricity",
        "Electrical and street lighting department"
    ),
    "Water Leakage / Water Supply": (
        "Water supply",
        "Water supply and hydraulic engineering department"
    ),
    "Public Infrastructure": (
        "Others",
        "Engineering and public works department"
    ),
}


# --------------------------------------------------
# DATABASE BACKUP
# --------------------------------------------------

def create_backup():
    """
    Create a consistent SQLite backup before migration.
    """

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database file was not found: {DATABASE_PATH}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = (
        BACKUP_DIR
        / f"civictrack_before_complaint_upgrade_{timestamp}.db"
    )

    source = sqlite3.connect(str(DATABASE_PATH))
    destination = sqlite3.connect(str(backup_path))

    try:
        source.backup(destination)
        destination.commit()

    finally:
        destination.close()
        source.close()

    return backup_path


# --------------------------------------------------
# SCHEMA HELPERS
# --------------------------------------------------

def get_table_columns(cursor, table_name):
    """
    Return the existing column names of a table.
    """

    rows = cursor.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return {
        row[1]
        for row in rows
    }


def add_missing_column(
    cursor,
    table_name,
    column_name,
    column_definition
):
    """
    Add a column only when it does not already exist.
    """

    columns = get_table_columns(
        cursor,
        table_name
    )

    if column_name not in columns:

        cursor.execute(
            f"""
            ALTER TABLE "{table_name}"
            ADD COLUMN "{column_name}" {column_definition}
            """
        )

        print(f"Added column: {table_name}.{column_name}")


# --------------------------------------------------
# COMPLAINT TABLE UPGRADE
# --------------------------------------------------

def upgrade_complaint_columns(cursor):
    """
    Add structured address, complainant and media fields.

    Existing columns are deliberately retained.
    """

    new_columns = [
        ("issue_location", "TEXT"),
        ("street_locality", "TEXT"),
        ("ward_number", "TEXT"),
        ("municipality", "TEXT"),
        ("district", "TEXT"),
        ("state", "TEXT"),
        ("complainant_name", "TEXT"),
        ("complainant_phone", "TEXT"),
        ("image_paths", "TEXT"),
        ("video_path", "TEXT"),
    ]

    for column_name, column_definition in new_columns:

        add_missing_column(
            cursor,
            "complaints",
            column_name,
            column_definition
        )


# --------------------------------------------------
# DEPARTMENT TABLE UPGRADE
# --------------------------------------------------

def upgrade_departments(cursor):
    """
    Preserve existing department IDs and officer relationships.

    Old department ID 5 is retained as an inactive legacy record.
    """

    add_missing_column(
        cursor,
        "departments",
        "is_active",
        "INTEGER NOT NULL DEFAULT 1"
    )

    # Rename the four existing departments without changing IDs.
    for department_id, details in LEGACY_DEPARTMENT_RENAMES.items():

        department_name, description = details

        cursor.execute(
            """
            UPDATE departments
            SET department_name = ?,
                description = ?,
                is_active = 1
            WHERE id = ?
            """,
            (
                department_name,
                description,
                department_id
            )
        )

    # Preserve the old fifth department as an inactive legacy record.
    cursor.execute(
        """
        UPDATE departments
        SET department_name = 'Public Works Department (Legacy - Inactive)',
            description = 'Archived legacy department. Existing records are preserved.',
            is_active = 0
        WHERE id = 5
        """
    )

    # Insert the remaining eight departments.
    for department_name, description in NEW_DEPARTMENTS:

        cursor.execute(
            """
            INSERT OR IGNORE INTO departments (
                department_name,
                description,
                is_active
            )
            VALUES (?, ?, 1)
            """,
            (
                department_name,
                description
            )
        )

    # Ensure the four renamed departments are active.
    cursor.execute(
        """
        UPDATE departments
        SET is_active = 1
        WHERE id IN (1, 2, 3, 4)
        """
    )


# --------------------------------------------------
# EXISTING COMPLAINT DATA MIGRATION
# --------------------------------------------------

def migrate_existing_complaints(cursor):
    """
    Preserve old complaints while adding the new information structure.
    """

    # Get department IDs by their new names.
    department_rows = cursor.execute(
        """
        SELECT id, department_name
        FROM departments
        """
    ).fetchall()

    department_ids = {
        row[1]: row[0]
        for row in department_rows
    }

    # Convert old category labels to their new equivalents.
    for old_category, mapping in LEGACY_CATEGORY_MAPPING.items():

        new_category, department_name = mapping

        department_id = department_ids.get(
            department_name
        )

        cursor.execute(
            """
            UPDATE complaints
            SET category = ?,
                department_id = ?
            WHERE category = ?
            """,
            (
                new_category,
                department_id,
                old_category
            )
        )

    # Preserve existing photographs in the new multiple-image field.
    rows = cursor.execute(
        """
        SELECT id, image_path, image_paths
        FROM complaints
        """
    ).fetchall()

    for row in rows:

        complaint_id = row[0]
        old_image_path = row[1]
        existing_image_paths = row[2]

        if (
            old_image_path
            and not existing_image_paths
        ):

            cursor.execute(
                """
                UPDATE complaints
                SET image_paths = ?
                WHERE id = ?
                """,
                (
                    json.dumps([old_image_path]),
                    complaint_id
                )
            )

    # Fill complainant details from existing citizen accounts.
    cursor.execute(
        """
        UPDATE complaints
        SET complainant_name = (
            SELECT full_name
            FROM users
            WHERE users.id = complaints.citizen_id
        )
        WHERE complainant_name IS NULL
           OR complainant_name = ''
        """
    )

    cursor.execute(
        """
        UPDATE complaints
        SET complainant_phone = (
            SELECT phone
            FROM users
            WHERE users.id = complaints.citizen_id
        )
        WHERE complainant_phone IS NULL
           OR complainant_phone = ''
        """
    )


# --------------------------------------------------
# DATABASE MIGRATION
# --------------------------------------------------

def upgrade_database():

    print("=" * 60)
    print("CIVICTRACK COMPLAINT SYSTEM DATABASE UPGRADE")
    print("=" * 60)

    # Always back up before modifying the database.
    backup_path = create_backup()

    print("\nDatabase backup created:")
    print(backup_path)

    connection = sqlite3.connect(
        str(DATABASE_PATH)
    )

    connection.row_factory = sqlite3.Row

    try:

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        cursor = connection.cursor()

        # Confirm that required existing tables are present.
        required_tables = [
            "users",
            "departments",
            "complaints",
            "status_history",
        ]

        existing_tables = {
            row[0]
            for row in cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        missing_tables = [
            table
            for table in required_tables
            if table not in existing_tables
        ]

        if missing_tables:
            raise RuntimeError(
                "Required database tables are missing: "
                + ", ".join(missing_tables)
            )

        # Perform all changes in one transaction.
        upgrade_complaint_columns(cursor)

        upgrade_departments(cursor)

        migrate_existing_complaints(cursor)

        # Verify that all active department records are present.
        active_departments = cursor.execute(
            """
            SELECT id, department_name
            FROM departments
            WHERE is_active = 1
            ORDER BY id
            """
        ).fetchall()

        if len(active_departments) != 12:
            raise RuntimeError(
                "Expected exactly 12 active departments, "
                f"but found {len(active_departments)}."
            )

        # Verify foreign-key integrity before committing.
        foreign_key_errors = cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise RuntimeError(
                "Foreign-key verification failed. "
                "The migration has been cancelled."
            )

        connection.commit()

        print("\nMigration completed successfully.")

        print("\nActive departments:")

        for index, department in enumerate(
            active_departments,
            start=1
        ):
            print(
                f"{index}. {department['department_name']}"
            )

        complaint_count = cursor.execute(
            "SELECT COUNT(*) FROM complaints"
        ).fetchone()[0]

        user_count = cursor.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        history_count = cursor.execute(
            "SELECT COUNT(*) FROM status_history"
        ).fetchone()[0]

        print("\nPreserved database records:")
        print("Users:", user_count)
        print("Complaints:", complaint_count)
        print("Complaint history entries:", history_count)

        print("\nBackup location:")
        print(backup_path)

        print("\nDatabase upgrade completed.")

    except Exception:

        connection.rollback()

        print(
            "\nMigration failed. Database changes were rolled back."
        )

        print(
            "Your original backup is still available at:"
        )

        print(backup_path)

        raise

    finally:
        connection.close()


# --------------------------------------------------
# RUN MIGRATION
# --------------------------------------------------

if __name__ == "__main__":
    upgrade_database()
