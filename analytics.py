
import pandas as pd

from database.db_connection import get_connection


# --------------------------------------------------
# FETCH COMPLAINT DATA
# --------------------------------------------------

def get_complaint_dataframe():
    """Retrieve complaint data with assigned department and officer."""

    connection = get_connection()

    try:
        return pd.read_sql_query(
            """
            SELECT
                c.id,
                c.tracking_id,
                c.title,
                c.category,
                c.status,
                c.address,
                c.created_at,
                c.updated_at,
                c.resolved_at,

                ad.department_name AS department_name,
                cd.department_name AS complaint_department_name,
                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN departments cd
                ON c.department_id = cd.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            ORDER BY c.created_at DESC
            """,
            connection
        )

    finally:
        connection.close()


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

def get_dashboard_summary():
    """Calculate overall complaint statistics."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_complaints,

                SUM(CASE
                    WHEN status = 'Pending'
                    THEN 1 ELSE 0
                END) AS pending,

                SUM(CASE
                    WHEN status = 'Under Review'
                    THEN 1 ELSE 0
                END) AS under_review,

                SUM(CASE
                    WHEN status = 'Assigned'
                    THEN 1 ELSE 0
                END) AS assigned,

                SUM(CASE
                    WHEN status = 'In Progress'
                    THEN 1 ELSE 0
                END) AS in_progress,

                SUM(CASE
                    WHEN status = 'Resolved'
                    THEN 1 ELSE 0
                END) AS resolved,

                SUM(CASE
                    WHEN status = 'Rejected'
                    THEN 1 ELSE 0
                END) AS rejected

            FROM complaints
        """)

        row = cursor.fetchone()
        result = dict(row)

        return {
            key: value or 0
            for key, value in result.items()
        }

    finally:
        connection.close()


# --------------------------------------------------
# CATEGORY STATISTICS
# --------------------------------------------------

def get_category_statistics():
    """Count complaints in each category."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                category,
                COUNT(*) AS total

            FROM complaints

            GROUP BY category

            ORDER BY total DESC
        """)

        return pd.DataFrame(
            [dict(row) for row in cursor.fetchall()]
        )

    finally:
        connection.close()


# --------------------------------------------------
# STATUS STATISTICS
# --------------------------------------------------

def get_status_statistics():
    """Count complaints by status."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total

            FROM complaints

            GROUP BY status

            ORDER BY total DESC
        """)

        return pd.DataFrame(
            [dict(row) for row in cursor.fetchall()]
        )

    finally:
        connection.close()


# --------------------------------------------------
# DEPARTMENT STATISTICS
# --------------------------------------------------

def get_department_statistics():
    """Calculate complaint workload by assigned officer department."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.department_name,

                COUNT(c.id) AS total_complaints,

                SUM(CASE
                    WHEN c.status = 'Pending'
                    THEN 1 ELSE 0
                END) AS pending,

                SUM(CASE
                    WHEN c.status = 'In Progress'
                    THEN 1 ELSE 0
                END) AS in_progress,

                SUM(CASE
                    WHEN c.status = 'Resolved'
                    THEN 1 ELSE 0
                END) AS resolved

            FROM departments d

            LEFT JOIN users o
                ON d.id = o.department_id
                AND o.role = 'officer'

            LEFT JOIN complaints c
                ON c.assigned_officer_id = o.id

            GROUP BY d.id, d.department_name

            ORDER BY total_complaints DESC
        """)

        records = [
            dict(row)
            for row in cursor.fetchall()
        ]

        dataframe = pd.DataFrame(records)

        if not dataframe.empty:
            count_columns = [
                "total_complaints",
                "pending",
                "in_progress",
                "resolved"
            ]

            dataframe[count_columns] = (
                dataframe[count_columns]
                .fillna(0)
                .astype(int)
            )

        return dataframe

    finally:
        connection.close()


# --------------------------------------------------
# MONTHLY COMPLAINT STATISTICS
# --------------------------------------------------

def get_monthly_statistics():
    """Calculate complaints submitted per month."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', created_at) AS month,
                COUNT(*) AS total

            FROM complaints

            WHERE created_at IS NOT NULL

            GROUP BY strftime('%Y-%m', created_at)

            ORDER BY month ASC
        """)

        return pd.DataFrame(
            [dict(row) for row in cursor.fetchall()]
        )

    finally:
        connection.close()


# --------------------------------------------------
# RESOLUTION STATISTICS
# --------------------------------------------------

def get_resolution_statistics():
    """Calculate average complaint resolution time in hours."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS resolved_complaints,

                AVG(
                    (julianday(resolved_at) -
                     julianday(created_at)) * 24
                ) AS average_resolution_hours

            FROM complaints

            WHERE status = 'Resolved'
            AND resolved_at IS NOT NULL
        """)

        result = dict(cursor.fetchone())

        return {
            "resolved_complaints": (
                result["resolved_complaints"] or 0
            ),
            "average_resolution_hours": (
                round(result["average_resolution_hours"], 2)
                if result["average_resolution_hours"] is not None
                else 0
            )
        }

    finally:
        connection.close()


# --------------------------------------------------
# EXPORT COMPLAINT DATA
# --------------------------------------------------

def export_complaints_csv():
    """Return complaint records in CSV format."""

    dataframe = get_complaint_dataframe()

    return dataframe.to_csv(index=False).encode("utf-8")


# --------------------------------------------------
# TESTING
# --------------------------------------------------

if __name__ == "__main__":

    print("\nCIVICTRACK ANALYTICS ENGINE")
    print("=" * 40)

    summary = get_dashboard_summary()

    print("\nComplaint Summary:")

    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    print("\nResolution Statistics:")
    print(get_resolution_statistics())

    print("\nDepartment Statistics:")
    print(get_department_statistics().to_string(index=False))

    print("\nAnalytics engine initialized successfully.")
