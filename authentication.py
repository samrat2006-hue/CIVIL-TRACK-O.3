
import re
import bcrypt
import hashlib
import secrets
import hmac
import unicodedata
import streamlit as st

from datetime import datetime, timedelta, timezone

from database.db_connection import get_connection


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PRIMARY_ADMIN_EMAIL = "gangulyrohit2008@gmail.com"

OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5

OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_REQUESTS_PER_15_MINUTES = 3
OTP_REQUEST_WINDOW_MINUTES = 15


# --------------------------------------------------
# PASSWORD SECURITY
# --------------------------------------------------

def hash_password(password):
    """Convert a password into a secure bcrypt hash."""

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes.")

    salt = bcrypt.gensalt()

    return bcrypt.hashpw(
        password_bytes,
        salt
    ).decode("utf-8")


def verify_password(password, stored_hash):
    """Verify a password against its stored bcrypt hash."""

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )

    except (ValueError, TypeError, AttributeError):
        return False


# --------------------------------------------------
# SECURITY ANSWER PROTECTION
# --------------------------------------------------

def normalize_security_answer(answer):
    """
    Normalize a security answer to make verification
    independent of capitalization and extra spaces.
    """

    answer = unicodedata.normalize("NFKC", answer)

    return " ".join(answer.strip().casefold().split())


def hash_security_answer(answer):
    """
    Hash security answers using bcrypt.

    SHA-256 is applied first so the input to bcrypt
    stays within bcrypt's 72-byte input limit.
    """

    normalized = normalize_security_answer(answer)

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return hash_password(digest)


def verify_security_answer(answer, stored_hash):
    """Verify a submitted security answer."""

    try:
        digest = hashlib.sha256(
            normalize_security_answer(answer).encode("utf-8")
        ).hexdigest()

        return verify_password(digest, stored_hash)

    except (ValueError, TypeError, AttributeError):
        return False


# --------------------------------------------------
# INPUT VALIDATION
# --------------------------------------------------

def validate_email(email):
    """Check whether an email address has a valid format."""

    if not isinstance(email, str):
        return False

    pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    return bool(re.fullmatch(pattern, email.strip()))


def validate_password(password):
    """
    Require at least 8 characters, including:
    - One uppercase letter
    - One lowercase letter
    - One number
    """

    if not isinstance(password, str):
        return False, "Please enter a valid password."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if len(password.encode("utf-8")) > 72:
        return False, "Password is too long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    return True, "Password is valid."


def validate_security_details(question, answer):
    """Validate the security question and answer."""

    if not isinstance(question, str) or not question.strip():
        return False, "Please select a security question."

    if not isinstance(answer, str) or not answer.strip():
        return False, "Please enter your security answer."

    if len(question.strip()) > 250:
        return False, "Security question is too long."

    if len(answer.strip()) > 200:
        return False, "Security answer is too long."

    return True, "Security details are valid."


def normalize_phone(phone):
    """Basic phone number validation and normalization."""

    phone = re.sub(r"[\s()-]", "", str(phone).strip())

    if not phone:
        return ""

    if not re.fullmatch(r"\+?[0-9]{7,15}", phone):
        return None

    return phone


# --------------------------------------------------
# ACCOUNT INSERTION HELPER
# --------------------------------------------------

def _generate_officer_uid(length=8, connection=None):
    """Generate a unique numeric UID with the requested digit count."""

    if not isinstance(length, int) or not 4 <= length <= 18:
        raise ValueError("Officer UID length must be between 4 and 18 digits.")

    owns_connection = connection is None

    if owns_connection:
        connection = get_connection()

    try:
        while True:
            uid = str(secrets.randbelow(10 ** length)).zfill(length)

            row = connection.execute(
                "SELECT id FROM users WHERE officer_uid = ?",
                (uid,)
            ).fetchone()

            if row is None:
                return uid

    finally:
        if owns_connection:
            connection.close()


def _generate_admin_id(connection):
    """Generate a unique eight-character administrator ID."""

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    while True:
        admin_id = "".join(
            secrets.choice(alphabet)
            for _ in range(8)
        )

        row = connection.execute(
            "SELECT id FROM users WHERE admin_id = ?",
            (admin_id,)
        ).fetchone()

        if row is None:
            return admin_id


def _insert_user(
    full_name,
    email,
    password,
    role,
    phone="",
    address="",
    department_id=None,
    security_question=None,
    security_answer=None,
    officer_uid_length=8
):
    """Create citizen/officer accounts, assigning officers a unique UID."""

    full_name = str(full_name).strip()
    email = str(email).strip().lower()
    phone = normalize_phone(phone)

    if not full_name:
        return False, "Please enter the full name."

    if not validate_email(email):
        return False, "Please enter a valid email address."

    if phone is None:
        return False, "Please enter a valid phone number."

    password_valid, password_message = validate_password(password)

    if not password_valid:
        return False, password_message

    if role not in ("citizen", "officer"):
        return False, "Invalid account role."

    security_valid, security_message = validate_security_details(
        security_question,
        security_answer
    )

    if not security_valid:
        return False, security_message

    try:
        password_hash = hash_password(password)
        answer_hash = hash_security_answer(security_answer)

    except ValueError as error:
        return False, str(error)

    connection = get_connection()

    try:
        cursor = connection.cursor()
        officer_uid = None

        if role == "officer":

            if department_id is None:
                return False, "An officer must belong to a department."

            if not isinstance(officer_uid_length, int) or not 4 <= officer_uid_length <= 18:
                return False, "Officer UID length must be between 4 and 18 digits."

            cursor.execute(
                "SELECT id FROM departments WHERE id = ?",
                (department_id,)
            )

            if cursor.fetchone() is None:
                return False, "Selected department does not exist."

            officer_uid = _generate_officer_uid(
                officer_uid_length,
                connection
            )

        cursor.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                phone,
                address,
                role,
                department_id,
                security_question,
                security_answer_hash,
                officer_uid,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                full_name,
                email,
                password_hash,
                phone,
                address.strip(),
                role,
                department_id,
                security_question.strip(),
                answer_hash,
                officer_uid
            )
        )

        connection.commit()

        if role == "officer":
            return True, f"Officer account created successfully. Officer UID: {officer_uid}"

        return True, "Citizen account created successfully."

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            return False, "An account with this email or UID already exists. Please try again."

        return False, "Account creation failed. Please try again."

    finally:
        connection.close()


# --------------------------------------------------
# CITIZEN REGISTRATION
# --------------------------------------------------

def register_user(
    full_name,
    email,
    password,
    phone="",
    address="",
    security_question="",
    security_answer=""
):
    """
    Public registration creates citizen accounts only.
    Security question and answer are mandatory.
    """

    return _insert_user(
        full_name=full_name,
        email=email,
        password=password,
        role="citizen",
        phone=phone,
        address=address,
        security_question=security_question,
        security_answer=security_answer
    )


# --------------------------------------------------
# ADMINISTRATOR ACCOUNT CREATION
# --------------------------------------------------

def create_user_account_by_admin(
    full_name,
    email,
    password,
    role,
    phone="",
    address="",
    department_id=None,
    security_question="",
    security_answer="",
    officer_uid_length=8
):
    """Administrators may create citizens and officers, never admins here."""

    current_user = get_current_user()

    if not current_user or current_user.get("role") != "admin":
        return False, "Administrator permission is required."

    if role not in ("citizen", "officer"):
        return False, "Only citizen and officer accounts can be created here."

    return _insert_user(
        full_name=full_name,
        email=email,
        password=password,
        role=role,
        phone=phone,
        address=address,
        department_id=department_id,
        security_question=security_question,
        security_answer=security_answer,
        officer_uid_length=officer_uid_length
    )


def create_staff_account(
    full_name,
    email,
    password,
    role,
    department_id=None,
    phone="",
    security_question="",
    security_answer="",
    officer_uid_length=8
):
    """Create officers for any admin; create admins only for primary admin."""

    current_user = get_current_user()

    if not current_user or current_user.get("role") != "admin":
        return False, "Administrator permission is required."

    if role == "officer":
        return _insert_user(
            full_name=full_name,
            email=email,
            password=password,
            role="officer",
            phone=phone,
            department_id=department_id,
            security_question=security_question,
            security_answer=security_answer,
            officer_uid_length=officer_uid_length
        )

    if role != "admin":
        return False, "Invalid account role."

    if not current_user.get("is_primary_admin"):
        return False, "Only the Primary Administrator can create administrator accounts."

    full_name = str(full_name).strip()
    email = str(email).strip().lower()
    normalized_phone = normalize_phone(phone)

    if not full_name:
        return False, "Please enter the administrator's name."

    if not validate_email(email):
        return False, "Please enter a valid email address."

    if normalized_phone is None:
        return False, "Please enter a valid phone number."

    password_valid, password_message = validate_password(password)

    if not password_valid:
        return False, password_message

    try:
        password_hash = hash_password(password)

    except ValueError as error:
        return False, str(error)

    connection = get_connection()

    try:
        cursor = connection.cursor()
        admin_id = _generate_admin_id(connection)

        cursor.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                phone,
                role,
                admin_id,
                is_primary_admin,
                is_active
            )
            VALUES (?, ?, ?, ?, 'admin', ?, 0, 1)
            """,
            (
                full_name,
                email,
                password_hash,
                normalized_phone,
                admin_id
            )
        )

        connection.commit()

        return True, f"Administrator account created successfully. Admin ID: {admin_id}"

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            return False, "This email address is already registered."

        return False, "Unable to create administrator account."

    finally:
        connection.close()


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

def authenticate_user(login_identifier, password, role=None):
    """Authenticate citizen by email, officer by UID, and admin by Admin ID."""

    if not isinstance(login_identifier, str) or not isinstance(password, str):
        return None

    identifier = login_identifier.strip()

    if not identifier or not password:
        return None

    if role == "citizen":
        lookup_column = "email"
        identifier = identifier.lower()

    elif role == "officer":
        lookup_column = "officer_uid"

    elif role == "admin":
        lookup_column = "admin_id"
        identifier = identifier.upper()

    else:
        lookup_column = "email"
        identifier = identifier.lower()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT
                id,
                full_name,
                email,
                password_hash,
                phone,
                address,
                role,
                department_id,
                is_active,
                admin_id,
                officer_uid,
                is_primary_admin
            FROM users
            WHERE {lookup_column} = ?
            LIMIT 1
            """,
            (identifier,)
        )

        user = cursor.fetchone()

        if user is None:
            return None

        user = dict(user)

        if not user.get("is_active"):
            return None

        if role and user.get("role") != role:
            return None

        if verify_password(password, user["password_hash"]):
            user.pop("password_hash", None)

            user["is_primary_admin"] = bool(
                user.get("is_primary_admin")
            )

            return user

        return None

    finally:
        connection.close()


# --------------------------------------------------
# SECURITY QUESTION RECOVERY
# --------------------------------------------------

def get_password_recovery_question(email, role):
    """
    Return the security question for a citizen or officer.
    Admin accounts are not eligible for this recovery flow.
    """

    if role not in ("citizen", "officer"):
        return False, "Security-question recovery is unavailable."

    if not isinstance(email, str) or not validate_email(email):
        return False, "Please enter a valid registered email address."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT security_question
            FROM users
            WHERE email = ?
              AND role = ?
              AND is_active = 1
            """,
            (email.strip().lower(), role)
        )

        user = cursor.fetchone()

        if user is None or not user["security_question"]:
            return False, "Recovery details are unavailable for this account."

        return True, user["security_question"]

    finally:
        connection.close()


def reset_password_with_security_answer(
    email,
    role,
    security_answer,
    new_password
):
    """Reset a citizen or officer password using the security answer."""

    if role not in ("citizen", "officer"):
        return False, "This recovery method is unavailable."

    password_valid, password_message = validate_password(new_password)

    if not password_valid:
        return False, password_message

    if not security_answer or not security_answer.strip():
        return False, "Please enter your security answer."

    email = email.strip().lower()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, security_answer_hash
            FROM users
            WHERE email = ?
              AND role = ?
              AND is_active = 1
            """,
            (email, role)
        )

        user = cursor.fetchone()

        if (
            user is None
            or not user["security_answer_hash"]
            or not verify_security_answer(
                security_answer,
                user["security_answer_hash"]
            )
        ):
            return False, "The recovery details could not be verified."

        new_hash = hash_password(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (new_hash, user["id"])
        )

        cursor.execute(
            """
            UPDATE password_reset_otps
            SET used = 1
            WHERE user_id = ?
              AND used = 0
            """,
            (user["id"],)
        )

        connection.commit()

        return True, "Password reset successful. Please log in again."

    except Exception:
        connection.rollback()
        return False, "Password reset failed. Please try again."

    finally:
        connection.close()


# --------------------------------------------------
# EMAIL OTP GENERATION
# --------------------------------------------------

def generate_password_reset_otp(
    identifier,
    role,
    delivery_method="email"
):
    """
    Generate a short-lived email OTP for a citizen or officer.

    Only email delivery is supported. The delivery_method parameter
    is retained for compatibility with existing callers, but
    non-email delivery methods are rejected.

    Returns:
        (True, otp, registered_email)
        (False, None, None)
    """

    if role not in ("citizen", "officer"):
        return False, None, None

    if delivery_method != "email":
        return False, None, None

    if not isinstance(identifier, str):
        return False, None, None

    identifier = identifier.strip().lower()

    if not validate_email(identifier):
        return False, None, None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, email
            FROM users
            WHERE email = ?
              AND role = ?
              AND is_active = 1
            LIMIT 1
            """,
            (identifier, role)
        )

        user = cursor.fetchone()

        if user is None:
            return False, None, None

        user_id = user["id"]

        now = datetime.now(timezone.utc)

        request_window_start = (
            now - timedelta(minutes=OTP_REQUEST_WINDOW_MINUTES)
        )

        # Retrieve recent email OTP requests.
        cursor.execute(
            """
            SELECT created_at
            FROM password_reset_otps
            WHERE user_id = ?
              AND purpose = 'password_reset'
              AND delivery_method = 'email'
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,)
        )

        recent_requests = cursor.fetchall()
        valid_recent_requests = []

        for request in recent_requests:

            created_at_value = request["created_at"]

            if not created_at_value:
                continue

            try:
                created_at = datetime.fromisoformat(
                    created_at_value
                )

                if created_at.tzinfo is None:
                    created_at = created_at.replace(
                        tzinfo=timezone.utc
                    )

                if created_at >= request_window_start:
                    valid_recent_requests.append(created_at)

            except (ValueError, TypeError):
                continue

        # Enforce resend cooldown.
        if valid_recent_requests:

            latest_request = max(valid_recent_requests)

            seconds_since_last_request = (
                now - latest_request
            ).total_seconds()

            if seconds_since_last_request < OTP_RESEND_COOLDOWN_SECONDS:
                return False, None, None

        # Enforce maximum requests within 15 minutes.
        if len(valid_recent_requests) >= OTP_MAX_REQUESTS_PER_15_MINUTES:
            return False, None, None

        # Invalidate previous unused email OTPs.
        cursor.execute(
            """
            UPDATE password_reset_otps
            SET used = 1
            WHERE user_id = ?
              AND purpose = 'password_reset'
              AND delivery_method = 'email'
              AND used = 0
            """,
            (user_id,)
        )

        otp = (
            f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"
        )

        otp_hash = hash_password(otp)

        expiry = now + timedelta(
            minutes=OTP_VALIDITY_MINUTES
        )

        cursor.execute(
            """
            INSERT INTO password_reset_otps (
                user_id,
                purpose,
                otp_hash,
                expires_at,
                attempts,
                used,
                delivery_method
            )
            VALUES (?, 'password_reset', ?, ?, 0, 0, 'email')
            """,
            (
                user_id,
                otp_hash,
                expiry.isoformat()
            )
        )

        connection.commit()

        return True, otp, user["email"]

    except Exception:
        connection.rollback()
        return False, None, None

    finally:
        connection.close()


# --------------------------------------------------
# EMAIL OTP VERIFICATION AND PASSWORD RESET
# --------------------------------------------------

def complete_password_reset_with_otp(
    identifier,
    role,
    otp,
    new_password,
    delivery_method="email"
):
    """Verify an email OTP and reset a citizen/officer password."""

    if role not in ("citizen", "officer"):
        return False, "OTP recovery is unavailable."

    if delivery_method != "email":
        return False, "Only email OTP verification is supported."

    password_valid, password_message = validate_password(
        new_password
    )

    if not password_valid:
        return False, password_message

    if not isinstance(otp, str) or not re.fullmatch(r"\d{6}", otp):
        return False, "Please enter the six-digit verification code."

    if not isinstance(identifier, str):
        return False, "Please enter your registered email address."

    identifier = identifier.strip().lower()

    if not validate_email(identifier):
        return False, "Please enter a valid registered email address."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                o.id AS otp_id,
                o.user_id,
                o.otp_hash,
                o.expires_at,
                o.attempts,
                o.used
            FROM password_reset_otps o
            INNER JOIN users u
                ON u.id = o.user_id
            WHERE u.email = ?
              AND u.role = ?
              AND u.is_active = 1
              AND o.purpose = 'password_reset'
              AND o.delivery_method = 'email'
              AND o.used = 0
            ORDER BY o.created_at DESC, o.id DESC
            LIMIT 1
            """,
            (identifier, role)
        )

        record = cursor.fetchone()

        if record is None:
            return False, "The verification code is invalid or expired."

        # Maximum attempts check.
        if record["attempts"] >= OTP_MAX_ATTEMPTS:

            cursor.execute(
                """
                UPDATE password_reset_otps
                SET used = 1
                WHERE id = ?
                """,
                (record["otp_id"],)
            )

            connection.commit()

            return False, "Too many attempts. Please request a new code."

        # Expiry check.
        expiry = datetime.fromisoformat(
            record["expires_at"]
        )

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        if expiry <= datetime.now(timezone.utc):

            cursor.execute(
                """
                UPDATE password_reset_otps
                SET used = 1
                WHERE id = ?
                """,
                (record["otp_id"],)
            )

            connection.commit()

            return False, "The verification code has expired. Please request a new one."

        # Verify submitted OTP.
        if not verify_password(otp, record["otp_hash"]):

            cursor.execute(
                """
                UPDATE password_reset_otps
                SET attempts = attempts + 1,
                    used = CASE
                        WHEN attempts + 1 >= ?
                        THEN 1
                        ELSE used
                    END
                WHERE id = ?
                """,
                (
                    OTP_MAX_ATTEMPTS,
                    record["otp_id"]
                )
            )

            connection.commit()

            return False, "The verification code is incorrect."

        # Correct OTP: update password.
        new_hash = hash_password(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                new_hash,
                record["user_id"]
            )
        )

        # Invalidate every outstanding password-reset OTP.
        cursor.execute(
            """
            UPDATE password_reset_otps
            SET used = 1
            WHERE user_id = ?
              AND purpose = 'password_reset'
              AND used = 0
            """,
            (record["user_id"],)
        )

        connection.commit()

        return True, "Password reset successful. Please log in."

    except Exception:
        connection.rollback()
        return False, "Password reset failed. Please try again."

    finally:
        connection.close()


# --------------------------------------------------
# SESSION MANAGEMENT
# --------------------------------------------------

def login_user(user):
    """Store authenticated user details in Streamlit session."""

    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["user_id"] = user["id"]
    st.session_state["user_role"] = user["role"]


def logout_user():
    """Clear the current user's authentication session."""

    keys = [
        "authenticated",
        "user",
        "user_id",
        "user_role"
    ]

    for key in keys:
        st.session_state.pop(key, None)


def is_authenticated():
    """Check whether a user is logged in."""

    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("user") is not None
    )


def get_current_user():
    """Return the currently authenticated user."""

    if not is_authenticated():
        return None

    return st.session_state.get("user")


def is_primary_administrator():
    """Return whether the signed-in administrator is the primary admin."""

    user = get_current_user()

    return bool(
        user
        and user.get("role") == "admin"
        and user.get("is_primary_admin")
    )


def get_user_role():
    """Return the current user's role."""

    user = get_current_user()

    if user:
        return user.get("role")

    return None


# --------------------------------------------------
# ROLE-BASED ACCESS
# --------------------------------------------------

def has_role(required_role):
    """Check whether the logged-in user has a given role."""

    if not is_authenticated():
        return False

    return get_user_role() == required_role


def require_role(required_role):
    """Stop access to a page without the required role."""

    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()

    if not has_role(required_role):
        st.error("You do not have permission to access this page.")
        st.stop()


# --------------------------------------------------
# USER MANAGEMENT
# --------------------------------------------------

def get_all_users():
    """Return account records needed by the administrator dashboard."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.full_name,
                u.email,
                u.phone,
                u.address,
                u.role,
                u.is_active,
                u.created_at,
                u.admin_id,
                u.officer_uid,
                u.is_primary_admin,
                d.department_name
            FROM users u
            LEFT JOIN departments d
                ON u.department_id = d.id
            ORDER BY u.created_at DESC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def update_user_status(user_id, is_active):
    """Apply role-aware account activation permissions."""

    current_user = get_current_user()

    if not current_user or current_user.get("role") != "admin":
        return False, "Administrator permission is required."

    try:
        user_id = int(user_id)

    except (TypeError, ValueError):
        return False, "Invalid user ID."

    if user_id == int(current_user["id"]):
        return False, "You cannot deactivate your own account."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        target = cursor.execute(
            """
            SELECT id, role, is_primary_admin
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if target is None:
            return False, "User not found."

        if target["role"] == "admin":

            if target["is_primary_admin"]:
                return False, "The Primary Administrator cannot be deactivated."

            if not current_user.get("is_primary_admin"):
                return False, "Only the Primary Administrator can manage administrator accounts."

        cursor.execute(
            """
            UPDATE users
            SET is_active = ?
            WHERE id = ?
            """,
            (
                1 if is_active else 0,
                user_id
            )
        )

        connection.commit()

        return True, "User account updated successfully."

    except Exception:
        connection.rollback()
        return False, "Unable to update the account."

    finally:
        connection.close()


def delete_user_account(user_id):
    """Delete citizens/officers for any admin; other admins only for primary."""

    current_user = get_current_user()

    if not current_user or current_user.get("role") != "admin":
        return False, "Administrator permission is required."

    try:
        user_id = int(user_id)

    except (TypeError, ValueError):
        return False, "Invalid user ID."

    if user_id == int(current_user["id"]):
        return False, "You cannot delete your own account."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        target = cursor.execute(
            """
            SELECT id, role, is_primary_admin
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if target is None:
            return False, "User not found."

        if target["is_primary_admin"]:
            return False, "The Primary Administrator cannot be deleted."

        if target["role"] == "admin" and not current_user.get("is_primary_admin"):
            return False, "Only the Primary Administrator can delete administrator accounts."

        if target["role"] not in ("citizen", "officer", "admin"):
            return False, "Invalid account type."

        if target["role"] == "citizen":

            cursor.execute(
                """
                DELETE FROM status_history
                WHERE complaint_id IN (
                    SELECT id
                    FROM complaints
                    WHERE citizen_id = ?
                )
                """,
                (user_id,)
            )

            cursor.execute(
                """
                DELETE FROM complaints
                WHERE citizen_id = ?
                """,
                (user_id,)
            )

        elif target["role"] == "officer":

            cursor.execute(
                """
                UPDATE status_history
                SET updated_by = NULL
                WHERE updated_by = ?
                """,
                (user_id,)
            )

            cursor.execute(
                """
                UPDATE complaints
                SET assigned_officer_id = NULL,
                    status = 'Pending',
                    updated_at = CURRENT_TIMESTAMP
                WHERE assigned_officer_id = ?
                """,
                (user_id,)
            )

        cursor.execute(
            """
            DELETE FROM password_reset_otps
            WHERE user_id = ?
            """,
            (user_id,)
        )

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()

        return True, f"{target['role'].capitalize()} account deleted successfully."

    except Exception:
        connection.rollback()
        return False, "Unable to delete this account. No changes were saved."

    finally:
        connection.close()
