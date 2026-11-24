
import json
import sqlite3
import uuid

from database.db_connection import get_connection


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

COMPLAINT_CATEGORIES = [
    "Roads and footpaths",
    "Garbage and sanitation",
    "Street lights and electricity",
    "Water supply",
    "Drainage and sewage",
    "Public health and vector control",
    "Parks, trees and environment",
    "Encroachment and illegal construction",
    "Traffic and parking",
    "Civic administration and property",
    "Others"
]


COMPLAINT_STATUSES = [
    "Pending",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
    "Rejected"
]


# --------------------------------------------------
# CATEGORY TO DEPARTMENT MAPPING
# --------------------------------------------------

CATEGORY_DEPARTMENTS = {
    "Roads and footpaths":
        "Engineering and public works department",

    "Garbage and sanitation":
        "Solid waste management department",

    "Street lights and electricity":
        "Electrical and street lighting department",

    "Water supply":
        "Water supply and hydraulic engineering department",

    "Drainage and sewage":
        "Sewage and stormwater drainage department",

    "Public health and vector control":
        "Public health and vector control department",

    "Parks, trees and environment":
        "Parks, garden and horticulture department",

    "Encroachment and illegal construction":
        "Estate or encroachment removal department",

    "Traffic and parking":
        "Traffic and transportation cell",

    "Civic administration and property":
        "Revenue and taxation department",

    "Others":
        "Engineering and public works department"
}


# --------------------------------------------------
# TRACKING ID GENERATOR
# --------------------------------------------------

def generate_tracking_id():
    """Generate a unique complaint tracking ID."""

    return "CT-" + uuid.uuid4().hex[:10].upper()


# --------------------------------------------------
# DEPARTMENT HELPERS
# --------------------------------------------------

def get_department_name(category):
    """Return the department responsible for a category."""

    return CATEGORY_DEPARTMENTS.get(
        category,
        "Engineering and public works department"
    )


def get_department_id(category):
    """Find the active department responsible for a category."""

    department_name = get_department_name(category)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM departments
            WHERE department_name = ?
            AND is_active = 1
            """,
            (department_name,)
        )

        result = cursor.fetchone()

        return result["id"] if result else None

    finally:
        connection.close()


# --------------------------------------------------
# ADDRESS HELPER
# --------------------------------------------------

def build_full_address(
    issue_location,
    street_locality,
    ward_number,
    municipality,
    district,
    state
):
    """Combine the six structured address fields."""

    address_parts = [
        f"Location: {issue_location}",
        f"Street/Locality: {street_locality}",
        f"Ward: {ward_number}",
        f"Municipality: {municipality}",
        f"District: {district}",
        f"State: {state}"
    ]

    return ", ".join(address_parts)


# --------------------------------------------------
# CREATE COMPLAINT
# --------------------------------------------------

def create_complaint(
    citizen_id,
    title,
    category,
    description,
    issue_location,
    street_locality,
    ward_number,
    municipality,
    district,
    state,
    complainant_name,
    complainant_phone,
    image_paths=None,
    video_path=None
):
    """Create a new complaint."""

    title = (title or "").strip()
    description = (description or "").strip()

    issue_location = (issue_location or "").strip()
    street_locality = (street_locality or "").strip()
    ward_number = (ward_number or "").strip()
    municipality = (municipality or "").strip()
    district = (district or "").strip()
    state = (state or "").strip()

    complainant_name = (complainant_name or "").strip()
    complainant_phone = (complainant_phone or "").strip()

    if not title:
        return False, "Complaint title is required."

    if not description:
        return False, "Complaint description is required."

    if category not in COMPLAINT_CATEGORIES:
        return False, "Invalid complaint category."

    address_fields = {
        "Location of the civic issue": issue_location,
        "Street or locality": street_locality,
        "Ward number": ward_number,
        "Municipality or municipal corporation": municipality,
        "District": district,
        "State": state
    }

    for field_name, value in address_fields.items():
        if not value:
            return False, f"{field_name} is required."

    if not complainant_name:
        return False, "Complainant full name is required."

    if not complainant_phone:
        return False, "Complainant contact number is required."

    phone_digits = "".join(
        character
        for character in complainant_phone
        if character.isdigit()
    )

    if len(phone_digits) < 7 or len(phone_digits) > 15:
        return False, "Please enter a valid contact number."

    if image_paths is None:
        image_paths = []

    if not isinstance(image_paths, list):
        return False, "Invalid photograph information."

    if any(
        not isinstance(path, str) or not path.strip()
        for path in image_paths
    ):
        return False, "Invalid photograph path."

    if video_path is not None:
        if not isinstance(video_path, str) or not video_path.strip():
            return False, "Invalid video path."

    department_id = get_department_id(category)

    if department_id is None:
        return False, "The responsible department was not found."

    full_address = build_full_address(
        issue_location,
        street_locality,
        ward_number,
        municipality,
        district,
        state
    )

    image_paths_json = (
        json.dumps(image_paths)
        if image_paths
        else None
    )

    first_image_path = image_paths[0] if image_paths else None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, role, is_active
            FROM users
            WHERE id = ?
            """,
            (citizen_id,)
        )

        citizen = cursor.fetchone()

        if (
            citizen is None
            or citizen["role"] != "citizen"
            or not citizen["is_active"]
        ):
            return False, "A valid active citizen account is required."

        tracking_id = generate_tracking_id()

        cursor.execute(
            """
            INSERT INTO complaints (
                tracking_id,
                citizen_id,
                department_id,
                title,
                category,
                description,
                address,
                issue_location,
                street_locality,
                ward_number,
                municipality,
                district,
                state,
                complainant_name,
                complainant_phone,
                image_path,
                image_paths,
                video_path,
                latitude,
                longitude,
                status
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                NULL,
                NULL,
                ?
            )
            """,
            (
                tracking_id,
                citizen_id,
                department_id,
                title,
                category,
                description,
                full_address,
                issue_location,
                street_locality,
                ward_number,
                municipality,
                district,
                state,
                complainant_name,
                complainant_phone,
                first_image_path,
                image_paths_json,
                video_path,
                "Pending"
            )
        )

        complaint_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO status_history (
                complaint_id,
                updated_by,
                old_status,
                new_status,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                citizen_id,
                None,
                "Pending",
                "Complaint submitted successfully."
            )
        )

        connection.commit()

        return True, tracking_id

    except sqlite3.Error:
        connection.rollback()
        return False, "Database error while submitting complaint."

    finally:
        connection.close()


# --------------------------------------------------
# GET COMPLAINT BY TRACKING ID
# --------------------------------------------------

def get_complaint_by_tracking_id(tracking_id, citizen_id=None):
    """Retrieve a complaint using its tracking ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                c.*,
                u.full_name AS citizen_name,

                d.department_name AS complaint_department_name,
                ad.department_name AS department_name,

                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN users u
                ON c.citizen_id = u.id

            LEFT JOIN departments d
                ON c.department_id = d.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            WHERE c.tracking_id = ?
        """

        parameters = [tracking_id.strip().upper()]

        if citizen_id is not None:
            query += " AND c.citizen_id = ?"
            parameters.append(citizen_id)

        cursor.execute(query, tuple(parameters))

        result = cursor.fetchone()

        return dict(result) if result else None

    finally:
        connection.close()


# --------------------------------------------------
# GET COMPLAINT BY DATABASE ID
# --------------------------------------------------

def get_complaint_by_id(complaint_id):
    """Retrieve a complaint using its database ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                c.*,
                u.full_name AS citizen_name,

                d.department_name AS complaint_department_name,
                ad.department_name AS department_name,

                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN users u
                ON c.citizen_id = u.id

            LEFT JOIN departments d
                ON c.department_id = d.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            WHERE c.id = ?
            """,
            (complaint_id,)
        )

        result = cursor.fetchone()

        return dict(result) if result else None

    finally:
        connection.close()


# --------------------------------------------------
# CITIZEN COMPLAINT HISTORY
# --------------------------------------------------

def get_complaints_by_citizen(citizen_id):
    """Retrieve all complaints submitted by a citizen."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                c.*,

                d.department_name AS complaint_department_name,
                ad.department_name AS department_name,

                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN departments d
                ON c.department_id = d.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            WHERE c.citizen_id = ?

            ORDER BY c.created_at DESC
            """,
            (citizen_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# GET ALL COMPLAINTS
# --------------------------------------------------

def get_all_complaints(
    status=None,
    category=None,
    department_id=None
):
    """Retrieve complaints with optional filters."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                c.*,
                u.full_name AS citizen_name,

                d.department_name AS complaint_department_name,
                ad.department_name AS department_name,

                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN users u
                ON c.citizen_id = u.id

            LEFT JOIN departments d
                ON c.department_id = d.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            WHERE 1 = 1
        """

        parameters = []

        if status:
            query += " AND c.status = ?"
            parameters.append(status)

        if category:
            query += " AND c.category = ?"
            parameters.append(category)

        if department_id is not None:
            query += " AND c.department_id = ?"
            parameters.append(department_id)

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, tuple(parameters))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# GET ASSIGNED OFFICER COMPLAINTS
# --------------------------------------------------

def get_officer_complaints(officer_id):
    """Retrieve complaints assigned to a particular officer."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                c.*,
                u.full_name AS citizen_name,

                d.department_name AS complaint_department_name,
                ad.department_name AS department_name,

                o.full_name AS officer_name

            FROM complaints c

            LEFT JOIN users u
                ON c.citizen_id = u.id

            LEFT JOIN users o
                ON c.assigned_officer_id = o.id

            LEFT JOIN departments d
                ON c.department_id = d.id

            LEFT JOIN departments ad
                ON o.department_id = ad.id

            WHERE c.assigned_officer_id = ?

            ORDER BY c.created_at DESC
            """,
            (officer_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# GET DEPARTMENTS
# --------------------------------------------------

def get_all_departments():
    """Retrieve active departments only."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM departments
            WHERE is_active = 1
            ORDER BY department_name
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# GET OFFICERS
# --------------------------------------------------

def get_department_officers(department_id=None):
    """
    Retrieve active officers.

    If department_id is supplied, filter by department.
    If omitted, return all active officers.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                id,
                full_name,
                email,
                department_id

            FROM users

            WHERE role = 'officer'
            AND is_active = 1
        """

        parameters = []

        if department_id is not None:
            query += " AND department_id = ?"
            parameters.append(department_id)

        query += " ORDER BY full_name"

        cursor.execute(query, tuple(parameters))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# ASSIGN COMPLAINT
# --------------------------------------------------

def assign_complaint(complaint_id, officer_id):
    """
    Assign a complaint to an active officer.

    Only administrators can assign complaints.
    The officer's registered department is displayed
    through the complaint retrieval functions.
    """

    from modules.authentication import get_current_user

    current_user = get_current_user()

    if not current_user or current_user["role"] != "admin":
        return False, "Administrator permission is required."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                status,
                assigned_officer_id
            FROM complaints
            WHERE id = ?
            """,
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        if complaint["status"] in ("Resolved", "Rejected"):
            return False, "Closed complaints cannot be assigned."

        if complaint["assigned_officer_id"] is not None:
            return False, "This complaint has already been assigned."

        if complaint["status"] not in ("Pending", "Under Review"):
            return False, "This complaint is not awaiting assignment."

        cursor.execute(
            """
            SELECT
                id,
                department_id
            FROM users
            WHERE id = ?
            AND role = 'officer'
            AND is_active = 1
            """,
            (officer_id,)
        )

        officer = cursor.fetchone()

        if officer is None:
            return False, "Active officer not found."

        if officer["department_id"] is None:
            return False, "The selected officer has no assigned department."

        old_status = complaint["status"]
        new_status = "Assigned"

        cursor.execute(
            """
            UPDATE complaints
            SET assigned_officer_id = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (officer_id, new_status, complaint_id)
        )

        cursor.execute(
            """
            INSERT INTO status_history (
                complaint_id,
                updated_by,
                old_status,
                new_status,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                current_user["id"],
                old_status,
                new_status,
                "Complaint assigned to an officer."
            )
        )

        connection.commit()

        return True, "Officer successfully assigned to this complaint."

    except sqlite3.Error:
        connection.rollback()
        return False, "Unable to assign complaint."

    finally:
        connection.close()


# --------------------------------------------------
# REJECT COMPLAINT
# --------------------------------------------------

def reject_complaint(complaint_id, rejection_reason):
    """
    Reject a complaint permanently.

    Administrator:
        Can reject a complaint before it is assigned.

    Officer:
        Can reject only a complaint assigned to them.

    The rejection reason and rejecting user's ID are
    stored in status_history. The reason is also stored
    in complaints.officer_remarks.

    Rejected complaints cannot be processed again.
    """

    from modules.authentication import get_current_user

    current_user = get_current_user()

    if not current_user:
        return False, "Please log in first."

    role = current_user.get("role")

    if role not in ("admin", "officer"):
        return False, "You do not have permission to reject complaints."

    rejection_reason = (rejection_reason or "").strip()

    if not rejection_reason:
        return False, "A rejection reason is required."

    if len(rejection_reason) < 5:
        return False, "Please provide a more detailed rejection reason."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                status,
                assigned_officer_id
            FROM complaints
            WHERE id = ?
            """,
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        if complaint["status"] in ("Resolved", "Rejected"):
            return False, "This complaint is already closed."

        # ------------------------------------------
        # ADMINISTRATOR REJECTION
        # ------------------------------------------

        if role == "admin":

            if complaint["assigned_officer_id"] is not None:
                return False, (
                    "The complaint has already been assigned. "
                    "Only its assigned officer can reject it."
                )

            if complaint["status"] not in ("Pending", "Under Review"):
                return False, (
                    "The administrator can reject only complaints "
                    "awaiting review or assignment."
                )

        # ------------------------------------------
        # OFFICER REJECTION
        # ------------------------------------------

        elif role == "officer":

            if complaint["assigned_officer_id"] != current_user["id"]:
                return False, (
                    "You can reject only complaints assigned to you."
                )

            if complaint["status"] not in (
                "Assigned",
                "Under Review",
                "In Progress"
            ):
                return False, (
                    "This complaint is not currently eligible "
                    "for officer rejection."
                )

        old_status = complaint["status"]

        cursor.execute(
            """
            UPDATE complaints
            SET status = 'Rejected',
                officer_remarks = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (rejection_reason, complaint_id)
        )

        cursor.execute(
            """
            INSERT INTO status_history (
                complaint_id,
                updated_by,
                old_status,
                new_status,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                current_user["id"],
                old_status,
                "Rejected",
                f"Rejected by {role.capitalize()}: {rejection_reason}"
            )
        )

        connection.commit()

        return True, "Complaint rejected successfully."

    except sqlite3.Error:
        connection.rollback()
        return False, "Unable to reject complaint."

    finally:
        connection.close()


# --------------------------------------------------
# UPDATE COMPLAINT STATUS
# --------------------------------------------------

def update_complaint_status(
    complaint_id,
    new_status,
    remarks="",
    resolution_details=""
):
    """
    Update complaint status.

    Administrators can update any eligible complaint.
    Officers can update only their assigned complaints.

    Rejection must use reject_complaint() so that a
    rejection reason and audit history are always recorded.
    """

    from modules.authentication import get_current_user

    current_user = get_current_user()

    if not current_user:
        return False, "Please log in first."

    if new_status not in COMPLAINT_STATUSES:
        return False, "Invalid complaint status."

    if new_status == "Rejected":
        return False, (
            "Use the dedicated rejection option and provide "
            "a rejection reason."
        )

    role = current_user["role"]

    if role not in ("admin", "officer"):
        return False, "You do not have permission to update complaints."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                assigned_officer_id,
                status,
                department_id
            FROM complaints
            WHERE id = ?
            """,
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        if role == "officer":
            if complaint["assigned_officer_id"] != current_user["id"]:
                return False, "This complaint is not assigned to you."

        if complaint["status"] in ("Resolved", "Rejected"):
            return False, "This complaint is already closed."

        if new_status == "Resolved" and not resolution_details.strip():
            return False, "Please provide resolution details."

        old_status = complaint["status"]

        cursor.execute(
            """
            UPDATE complaints

            SET status = ?,
                officer_remarks = ?,
                resolution_details = ?,
                updated_at = CURRENT_TIMESTAMP,
                resolved_at = CASE
                    WHEN ? = 'Resolved' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END

            WHERE id = ?
            """,
            (
                new_status,
                remarks.strip(),
                resolution_details.strip(),
                new_status,
                complaint_id
            )
        )

        cursor.execute(
            """
            INSERT INTO status_history (
                complaint_id,
                updated_by,
                old_status,
                new_status,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                current_user["id"],
                old_status,
                new_status,
                remarks.strip() or resolution_details.strip()
            )
        )

        connection.commit()

        return True, "Complaint status updated successfully."

    except sqlite3.Error:
        connection.rollback()
        return False, "Unable to update complaint status."

    finally:
        connection.close()


# --------------------------------------------------
# COMPLAINT STATUS HISTORY
# --------------------------------------------------

def get_status_history(complaint_id):
    """Retrieve the complete status history of a complaint."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                h.*,
                u.full_name AS updated_by_name,
                u.role AS updated_by_role

            FROM status_history h

            LEFT JOIN users u
                ON h.updated_by = u.id

            WHERE h.complaint_id = ?

            ORDER BY h.updated_at ASC, h.id ASC
            """,
            (complaint_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()
