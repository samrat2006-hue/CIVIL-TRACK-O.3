
import streamlit as st

from database.create_tables import create_tables

from modules.authentication import (
    register_user,
    authenticate_user,
    login_user,
    logout_user,
    is_authenticated,
    get_current_user,
    get_password_recovery_question,
    reset_password_with_security_answer,
    generate_password_reset_otp,
    complete_password_reset_with_otp,
)

from modules.email_service import send_password_reset_email
from modules.theme import apply_theme

# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CivicTrack | Public Grievance Management",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

create_tables()
apply_theme()


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

def render_home():

    st.markdown(
        """
        <div class="civic-hero">
            <div class="civic-hero-tag">
                SMART PUBLIC GRIEVANCE MANAGEMENT SYSTEM
            </div>
            <h1>Your City. Your Voice. Our Responsibility.</h1>
            <p>
                CivicTrack connects citizens, municipal officers and
                administrators through one transparent platform.
                Report public problems, monitor progress and help
                build better-managed communities.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="civic-section-title">Choose Your Portal</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):

            st.markdown(
                """
                <div class="civic-card-icon">👤</div>
                <div class="civic-card-title">Citizen Portal</div>
                <div class="civic-card-description">
                    Report civic problems, upload photographs,
                    track complaints and monitor their progress.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Citizen Login",
                type="primary",
                key="citizen_login_home",
                use_container_width=True,
            ):
                st.switch_page(PAGE_CITIZEN_LOGIN)

            if st.button(
                "Citizen Registration",
                key="citizen_register_home",
                use_container_width=True,
            ):
                st.switch_page(PAGE_CITIZEN_REGISTER)

    with col2:
        with st.container(border=True):

            st.markdown(
                """
                <div class="civic-card-icon">🧑‍💼</div>
                <div class="civic-card-title">
                    Government / Municipal Officer
                </div>
                <div class="civic-card-description">
                    Access assigned complaints, investigate issues,
                    add remarks and update resolution status.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Officer Login",
                type="primary",
                key="officer_login_home",
                use_container_width=True,
            ):
                st.switch_page(PAGE_OFFICER_LOGIN)

            st.caption(
                "Officer accounts are created by the administrator."
            )

    with col3:
        with st.container(border=True):

            st.markdown(
                """
                <div class="civic-card-icon">🛡️</div>
                <div class="civic-card-title">
                    Administrator Portal
                </div>
                <div class="civic-card-description">
                    Manage users, departments, officer accounts
                    and complaint assignments.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Administrator Login",
                type="primary",
                key="admin_login_home",
                use_container_width=True,
            ):
                st.switch_page(PAGE_ADMIN_LOGIN)

            st.caption(
                "Administrator accounts are managed securely."
            )

    st.markdown(
        '<div class="civic-section-title">Platform Overview</div>',
        unsafe_allow_html=True,
    )

    stats = st.columns(4)

    overview = [
        ("User Roles", "3"),
        ("Complaint Categories", "More than 10"),
        ("Complaint Tracking", "24/7"),
        ("Complaint Management", "Integrated"),
    ]

    for column, item in zip(stats, overview):
        with column:
            st.markdown(
                f"""
                <div class="civic-stat-card">
                    <div class="civic-stat-label">{item[0]}</div>
                    <div class="civic-stat-value">{item[1]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="civic-section-title">What CivicTrack Offers</div>',
        unsafe_allow_html=True,
    )

    features = [
        (
            "📝",
            "Complaint Reporting",
            "Submit civic complaints with descriptions, categories "
            "and complete issue address information."
        ),
        (
            "📸",
            "Complaint Evidence Upload",
            "Attach multiple photographs and a short video "
            "to provide supporting evidence."
        ),
        (
            "🔎",
            "Complaint Tracking",
            "Use a unique tracking ID to check complaint status "
            "and review its status history."
        ),
        (
            "🧑‍💼",
            "Officer Management",
            "Authorized officers can access assigned complaints, "
            "investigate issues and add remarks."
        ),
        (
            "🛡️",
            "Administration",
            "Administrators can manage users, departments, "
            "officer accounts and complaint assignments."
        ),
        (
            "📋",
            "Resolution and Rejection Management",
            "Record complaint decisions, provide rejection reasons "
            "and communicate resolution information."
        ),
    ]

    feature_columns = st.columns(3)

    for index, feature in enumerate(features):
        with feature_columns[index % 3]:
            st.markdown(
                f"""
                <div class="civic-card">
                    <div class="civic-card-icon">{feature[0]}</div>
                    <div class="civic-card-title">{feature[1]}</div>
                    <div class="civic-card-description">
                        {feature[2]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="civic-section-title">How It Works</div>',
        unsafe_allow_html=True,
    )

    steps = [
        ("01", "Report", "Citizens submit public complaints."),
        ("02", "Review", "Complaints are reviewed and assigned."),
        ("03", "Resolve", "Officers investigate and take action."),
        ("04", "Track", "Citizens follow the latest updates."),
    ]

    step_columns = st.columns(4)

    for index, step in enumerate(steps):
        with step_columns[index]:
            st.markdown(
                f"""
                <div class="civic-card">
                    <div class="civic-card-icon">{step[0]}</div>
                    <div class="civic-card-title">{step[1]}</div>
                    <div class="civic-card-description">
                        {step[2]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="civic-section-title">'
        'Supported Complaint Categories</div>',
        unsafe_allow_html=True,
    )

    categories = [
        "🚧 Roads and footpaths",
        "🗑️ Garbage and sanitation",
        "💡 Street lights and electricity",
        "🚰 Water supply",
        "🌧️ Drainage and sewage",
        "🏥 Public health and vector control",
        "🌳 Parks, trees and environment",
        "🏗️ Encroachment and illegal construction",
        "🚦 Traffic and parking",
        "🏢 Civic administration and property",
    ]

    category_columns = st.columns(3)

    for index, category in enumerate(categories):
        with category_columns[index % 3]:
            st.info(category)

    st.markdown(
        """
        <div class="civic-more">And many more!</div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# ABOUT PAGE
# --------------------------------------------------

def render_about():

    st.title("About CivicTrack")

    st.write(
        """
        CivicTrack is a web-based Smart Public Grievance Management
        System developed to make communication between citizens
        and municipal authorities more accessible, organized and
        transparent.

        The platform provides a centralized digital environment
        where citizens can report problems affecting their
        neighbourhoods and communities without depending entirely
        on traditional complaint-submission processes.

        From damaged roads and water supply problems to sanitation,
        drainage, street lighting and other public infrastructure
        issues, CivicTrack provides a structured way to bring civic
        problems to the attention of the concerned authorities.

        Every submitted complaint receives a unique tracking ID.
        Citizens can use this ID to follow the progress of their
        complaints and view available status updates, officer
        remarks, rejection information and resolution details.

        CivicTrack also provides dedicated portals for municipal
        officers and administrators. Officers can access complaints
        assigned to them, review the submitted information, examine
        supporting photographs and videos, update complaint statuses
        and provide remarks. Administrators can manage citizen and
        officer accounts, maintain departments and coordinate
        complaint assignments.

        The system supports structured complaint information,
        including the location of the civic issue, street or locality,
        ward number, municipality, district and state. Citizens can
        also attach multiple photographs and a short video to help
        explain the reported problem.

        By bringing complaint submission, assignment, monitoring
        and resolution-related communication together in one
        platform, CivicTrack aims to encourage public participation,
        improve administrative coordination and support greater
        accountability in civic service management.

        **Our vision is to help create better-connected communities
        where citizens can raise their concerns and public
        authorities can manage them through an organized digital
        process.**
        """
    )

    st.divider()

    st.subheader("Our Three User Roles")

    roles = [
        (
            "👤 Citizen",
            "Register an account, report civic problems, upload "
            "supporting photographs and videos, view complaint "
            "history and track complaint progress using a unique ID."
        ),
        (
            "🧑‍💼 Government / Municipal Officer",
            "Access complaints assigned by the administrator, "
            "review complaint information, investigate civic issues, "
            "update statuses, add remarks and record resolutions."
        ),
        (
            "🛡️ Administrator",
            "Manage citizen and officer accounts, create officer "
            "accounts, manage departments, assign complaints and "
            "coordinate the overall complaint management process."
        ),
    ]

    for title, description in roles:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(description)

    st.divider()

    st.subheader("Technology Stack")

    technology_sections = [
        (
            "Programming and Application Development",
            ["Python", "Streamlit", "HTML and CSS"],
        ),
        (
            "Database and Data Management",
            ["SQL", "SQLite3", "Pandas", "JSON"],
        ),
        (
            "User Interface and Data Presentation",
            [
                "Streamlit Components",
                "Streamlit Session State",
                "Plotly",
                "Custom CSS",
            ],
        ),
        (
            "Security and Authentication",
            [
                "bcrypt",
                "Role-Based Authentication",
                "Security Question Verification",
            ],
        ),
        (
            "Media and File Management",
            [
                "Pillow",
                "imageio-ffmpeg",
                "Pathlib",
                "File and Directory Management",
            ],
        ),
        (
            "Python Standard Libraries",
            ["datetime", "os", "json", "sqlite3"],
        ),
    ]

    for section_title, technologies in technology_sections:

        with st.container(border=True):

            st.markdown(f"### {section_title}")

            for technology in technologies:
                st.markdown(f"- **{technology}**")


# --------------------------------------------------
# PASSWORD RECOVERY HELPERS
# --------------------------------------------------

def clear_otp_recovery_state(required_role):

    keys = [
        f"{required_role}_email_otp_pending",
        f"{required_role}_email_otp_identifier",
    ]

    for key in keys:
        st.session_state.pop(key, None)


def request_recovery_otp(required_role, identifier):

    identifier = identifier.strip()

    if not identifier:
        st.error("Please enter your registered email address.")
        return

    success, otp, destination = generate_password_reset_otp(
        identifier=identifier,
        role=required_role,
        delivery_method="email",
    )

    if not success:
        st.error(
            "Unable to generate an OTP. Please verify your registered "
            "email address, account status and retry limits."
        )
        return

    delivery_success, delivery_message = send_password_reset_email(
        recipient_email=destination,
        otp=otp,
    )

    if delivery_success:

        st.session_state[
            f"{required_role}_email_otp_pending"
        ] = True

        st.session_state[
            f"{required_role}_email_otp_identifier"
        ] = identifier

        st.success(delivery_message)

        st.info(
            "Check your registered email inbox, including the "
            "spam or junk folder."
        )

    else:
        st.error(delivery_message)


def verify_recovery_otp(required_role, otp, new_password,
                        confirm_password):

    pending_key = f"{required_role}_email_otp_pending"
    identifier_key = f"{required_role}_email_otp_identifier"

    if not st.session_state.get(pending_key, False):
        st.error("Please request an email OTP first.")
        return

    identifier = st.session_state.get(identifier_key)

    if not identifier:
        st.error("Recovery session not found. Please request a new OTP.")
        return

    if not otp.strip():
        st.error("Please enter the OTP.")
        return

    if not new_password:
        st.error("Please enter your new password.")
        return

    if new_password != confirm_password:
        st.error("The passwords do not match.")
        return

    success, message = complete_password_reset_with_otp(
        identifier=identifier,
        role=required_role,
        otp=otp.strip(),
        new_password=new_password,
        delivery_method="email",
    )

    if success:

        st.success(message)

        clear_otp_recovery_state(required_role)

        st.session_state.pop(
            f"{required_role}_recovery_question",
            None,
        )

        st.session_state.pop(
            f"{required_role}_recovery_question_loaded",
            None,
        )

        st.info(
            "Your password has been reset successfully. "
            "You can now return to the login page."
        )

    else:
        st.error(message)


# --------------------------------------------------
# PASSWORD RECOVERY
# --------------------------------------------------

def render_forgot_password(required_role):

    role_titles = {
        "citizen": "Citizen",
        "officer": "Officer",
    }

    st.title(f"🔑 {role_titles[required_role]} Password Recovery")

    st.write(
        "Choose one of the following methods to recover your account."
    )

    st.divider()

    recovery_method = st.radio(
        "Select your preferred recovery method",
        options=[
            "Email OTP Verification",
            "Security Question",
        ],
        index=0,
        key=f"{required_role}_recovery_method",
    )

    st.divider()

    # --------------------------------------------------
    # METHOD 1: EMAIL OTP
    # --------------------------------------------------

    if recovery_method == "Email OTP Verification":

        st.subheader("📧 Email OTP Verification")

        st.write(
            "Enter the email address registered with your "
            "CivicTrack account."
        )

        email = st.text_input(
            "Registered Email Address",
            key=f"{required_role}_email_otp_address",
        )

        if st.button(
            "Send Email OTP",
            key=f"{required_role}_send_email_otp",
            use_container_width=True,
        ):

            request_recovery_otp(
                required_role,
                email,
            )

        pending = st.session_state.get(
            f"{required_role}_email_otp_pending",
            False,
        )

        if pending:

            st.divider()
            st.markdown("### Verify Email OTP")

            with st.form(
                f"{required_role}_email_otp_verification_form"
            ):

                otp = st.text_input(
                    "Enter 6-digit Email OTP",
                    max_chars=6,
                    placeholder="Enter OTP",
                )

                new_password = st.text_input(
                    "New Password",
                    type="password",
                )

                confirm_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                )

                submitted = st.form_submit_button(
                    "Verify OTP and Reset Password",
                    use_container_width=True,
                )

            if submitted:

                verify_recovery_otp(
                    required_role,
                    otp,
                    new_password,
                    confirm_password,
                )

    # --------------------------------------------------
    # METHOD 2: SECURITY QUESTION
    # --------------------------------------------------

    elif recovery_method == "Security Question":

        st.subheader("🛡️ Security Question Verification")

        st.write(
            "Use the security question you selected during "
            "registration or account creation."
        )

        email_key = f"{required_role}_security_recovery_email"
        question_key = f"{required_role}_recovery_question"
        loaded_key = f"{required_role}_recovery_question_loaded"

        email = st.text_input(
            "Registered Email Address",
            key=email_key,
        )

        if st.button(
            "Find My Security Question",
            key=f"{required_role}_find_question",
            use_container_width=True,
        ):

            st.session_state.pop(question_key, None)
            st.session_state[loaded_key] = False

            if not email.strip():

                st.error(
                    "Please enter your registered email address."
                )

            else:

                success, result = get_password_recovery_question(
                    email,
                    required_role,
                )

                if success:

                    st.session_state[question_key] = result
                    st.session_state[loaded_key] = True

                    st.success(
                        "Your security question has been retrieved."
                    )

                else:

                    st.session_state.pop(question_key, None)
                    st.session_state[loaded_key] = False

                    st.error(result)

        if st.session_state.get(loaded_key, False):

            question = st.session_state.get(question_key)

            if question:

                st.markdown("### Your Security Question")

                st.info(question)

                with st.form(
                    f"{required_role}_security_password_reset_form"
                ):

                    security_answer = st.text_input(
                        "Your Security Answer",
                        type="password",
                    )

                    new_password = st.text_input(
                        "New Password",
                        type="password",
                    )

                    confirm_password = st.text_input(
                        "Confirm New Password",
                        type="password",
                    )

                    submitted = st.form_submit_button(
                        "Reset Password",
                        use_container_width=True,
                    )

                if submitted:

                    if not security_answer.strip():

                        st.error(
                            "Please enter your security answer."
                        )

                    elif not new_password:

                        st.error(
                            "Please enter a new password."
                        )

                    elif new_password != confirm_password:

                        st.error(
                            "The passwords do not match."
                        )

                    else:

                        success, message = (
                            reset_password_with_security_answer(
                                email=email,
                                role=required_role,
                                security_answer=security_answer,
                                new_password=new_password,
                            )
                        )

                        if success:

                            st.success(message)

                            st.session_state.pop(
                                question_key,
                                None,
                            )

                            st.session_state.pop(
                                loaded_key,
                                None,
                            )

                            st.info(
                                "Your password has been reset. "
                                "You can now return to the login page."
                            )

                        else:

                            st.error(message)

    st.divider()

    login_pages = {
        "citizen": PAGE_CITIZEN_LOGIN,
        "officer": PAGE_OFFICER_LOGIN,
    }

    if st.button(
        "← Back to Login",
        key=f"{required_role}_recovery_back",
        use_container_width=True,
    ):

        st.switch_page(login_pages[required_role])


# --------------------------------------------------
# ROLE-SPECIFIC LOGIN
# --------------------------------------------------

def render_login(required_role):

    role_titles = {
        "citizen": "Citizen",
        "officer": "Government / Municipal Officer",
        "admin": "Administrator",
    }

    login_labels = {
        "citizen": "Registered Email Address",
        "officer": "Officer UID",
        "admin": "Admin ID",
    }

    login_placeholders = {
        "citizen": "Enter your registered email address",
        "officer": "Enter your numeric Officer UID",
        "admin": "Enter your Admin ID",
    }

    st.title(f"🔐 {role_titles[required_role]} Login")

    if required_role == "citizen":
        st.write("Enter your registered email address and password.")
    elif required_role == "officer":
        st.write(
            "Enter the unique Officer UID assigned by your "
            "administrator and your password."
        )
    else:
        st.write("Enter your administrator ID and password.")
        st.caption("Primary Administrator ID: PRI/2026")

    identifier = st.text_input(
        login_labels[required_role],
        placeholder=login_placeholders[required_role],
        key=f"{required_role}_login_identifier",
    )

    password = st.text_input(
        "Password",
        type="password",
        key=f"{required_role}_login_password",
    )

    if required_role in ("citizen", "officer"):

        left_space, recovery_column = st.columns([7, 2])

        with recovery_column:

            if st.button(
                "Forgot Password?",
                key=f"{required_role}_forgot_password",
                type="secondary",
                use_container_width=False,
            ):

                recovery_pages = {
                    "citizen": PAGE_CITIZEN_RECOVERY,
                    "officer": PAGE_OFFICER_RECOVERY,
                }

                st.switch_page(recovery_pages[required_role])

    submitted = st.button(
        "Login",
        key=f"{required_role}_login_submit",
        use_container_width=True,
        type="primary",
    )

    if submitted:

        if not identifier.strip() or not password:
            st.error("Please enter both your login ID and password.")
            return

        account = authenticate_user(
            identifier.strip(),
            password,
            role=required_role,
        )

        if account is None:
            st.error(
                f"Invalid {login_labels[required_role]} or password, "
                "or your account is inactive. Please check your details."
            )
            return

        login_user(account)

        dashboard_pages = {
            "citizen": PAGE_CITIZEN_DASHBOARD,
            "officer": PAGE_OFFICER_DASHBOARD,
            "admin": PAGE_ADMIN_DASHBOARD,
        }

        st.switch_page(dashboard_pages[required_role])


# --------------------------------------------------
# CITIZEN REGISTRATION
# --------------------------------------------------

def render_citizen_registration():

    st.title("📝 Citizen Registration")

    st.write(
        "Create your citizen account to report public issues "
        "and track complaints."
    )

    security_questions = [
        "What was the name of your first school?",
        "What is the name of your childhood best friend?",
        "What was the name of your first pet?",
        "In which city were you born?",
        "What is your favourite childhood teacher's name?",
    ]

    with st.form("citizen_registration_form"):

        full_name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        address = st.text_area("Address")

        password = st.text_input(
            "Create Password",
            type="password",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
        )

        st.markdown("### Account Recovery Security")

        st.caption(
            "Choose a question and provide an answer you can "
            "remember. Your answer will be stored as a secure hash."
        )

        security_question = st.selectbox(
            "Choose a Security Question",
            security_questions,
        )

        security_answer = st.text_input(
            "Your Security Answer",
            type="password",
        )

        confirm_security_answer = st.text_input(
            "Confirm Security Answer",
            type="password",
        )

        submitted = st.form_submit_button(
            "Create Citizen Account",
            use_container_width=True,
        )

    if submitted:

        if (
            not full_name.strip()
            or not email.strip()
            or not password
            or not security_answer.strip()
        ):

            st.error(
                "Please complete all required fields."
            )

        elif password != confirm_password:

            st.error(
                "The passwords do not match."
            )

        elif (
            security_answer.strip()
            != confirm_security_answer.strip()
        ):

            st.error(
                "The security answers do not match."
            )

        else:

            success, message = register_user(
                full_name=full_name,
                email=email,
                password=password,
                phone=phone,
                address=address,
                security_question=security_question,
                security_answer=security_answer,
            )

            if success:

                st.success(message)

                st.info(
                    "Your citizen account is ready. "
                    "Please use the Citizen Login portal."
                )

            else:

                st.error(message)


# --------------------------------------------------
# PAGE REGISTRATION
# --------------------------------------------------

PAGE_HOME = st.Page(
    render_home,
    title="Home",
    icon="🏙️",
    default=True,
    url_path="home",
)

PAGE_ABOUT = st.Page(
    render_about,
    title="About CivicTrack",
    icon="ℹ️",
    url_path="about",
)

PAGE_CITIZEN_LOGIN = st.Page(
    lambda: render_login("citizen"),
    title="Citizen Login",
    icon="👤",
    url_path="citizen-login",
)

PAGE_OFFICER_LOGIN = st.Page(
    lambda: render_login("officer"),
    title="Officer Login",
    icon="🧑‍💼",
    url_path="officer-login",
)

PAGE_ADMIN_LOGIN = st.Page(
    lambda: render_login("admin"),
    title="Administrator Login",
    icon="🛡️",
    url_path="administrator-login",
)

PAGE_CITIZEN_REGISTER = st.Page(
    render_citizen_registration,
    title="Citizen Registration",
    icon="📝",
    url_path="citizen-registration",
)

PAGE_CITIZEN_RECOVERY = st.Page(
    lambda: render_forgot_password("citizen"),
    title="Citizen Password Recovery",
    icon="🔑",
    url_path="citizen-password-recovery",
)

PAGE_OFFICER_RECOVERY = st.Page(
    lambda: render_forgot_password("officer"),
    title="Officer Password Recovery",
    icon="🔑",
    url_path="officer-password-recovery",
)

PAGE_CITIZEN_DASHBOARD = st.Page(
    "pages/citizen_dashboard.py",
    title="Citizen Dashboard",
    icon="👤",
    url_path="citizen-dashboard",
)

PAGE_REPORT_COMPLAINT = st.Page(
    "pages/report_complaint.py",
    title="Report a Complaint",
    icon="📝",
    url_path="report-complaint",
)

PAGE_TRACK_COMPLAINT = st.Page(
    "pages/track_complaint.py",
    title="Track a Complaint",
    icon="🔎",
    url_path="track-complaint",
)

PAGE_OFFICER_DASHBOARD = st.Page(
    "pages/officer_dashboard.py",
    title="Officer Dashboard",
    icon="🧑‍💼",
    url_path="officer-dashboard",
)

PAGE_ADMIN_DASHBOARD = st.Page(
    "pages/admin_dashboard.py",
    title="Admin Dashboard",
    icon="🛡️",
    url_path="admin-dashboard",
)


# --------------------------------------------------
# REGISTER ALL PAGES WITH STREAMLIT
# --------------------------------------------------

navigation = st.navigation(
    [
        PAGE_HOME,
        PAGE_ABOUT,
        PAGE_CITIZEN_LOGIN,
        PAGE_OFFICER_LOGIN,
        PAGE_ADMIN_LOGIN,
        PAGE_CITIZEN_REGISTER,
        PAGE_CITIZEN_RECOVERY,
        PAGE_OFFICER_RECOVERY,
        PAGE_CITIZEN_DASHBOARD,
        PAGE_REPORT_COMPLAINT,
        PAGE_TRACK_COMPLAINT,
        PAGE_OFFICER_DASHBOARD,
        PAGE_ADMIN_DASHBOARD,
    ],
    position="hidden",
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="civic-brand">Civic<span>Track</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="civic-subtitle">
            SMART PUBLIC GRIEVANCE MANAGEMENT
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    authenticated = is_authenticated()

    current_user = (
        get_current_user()
        if authenticated
        else None
    )

    if authenticated:

        st.success(
            f"Logged in as {current_user['full_name']}"
        )

        st.caption(
            f"Role: {current_user['role'].capitalize()}"
        )

        st.divider()

        st.subheader("Your Dashboard")

        role = current_user["role"]

        if role == "citizen":

            if st.button(
                "👤 Citizen Dashboard",
                use_container_width=True,
            ):
                st.switch_page(PAGE_CITIZEN_DASHBOARD)

            if st.button(
                "📝 Report Complaint",
                use_container_width=True,
            ):
                st.switch_page(PAGE_REPORT_COMPLAINT)

            if st.button(
                "🔎 Track Complaint",
                use_container_width=True,
            ):
                st.switch_page(PAGE_TRACK_COMPLAINT)

        elif role == "officer":

            if st.button(
                "🧑‍💼 Officer Dashboard",
                use_container_width=True,
            ):
                st.switch_page(PAGE_OFFICER_DASHBOARD)

        elif role == "admin":

            if st.button(
                "🛡️ Admin Dashboard",
                use_container_width=True,
            ):
                st.switch_page(PAGE_ADMIN_DASHBOARD)

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
        ):

            logout_user()
            st.rerun()

    else:

        if st.button(
            "🏠 Home",
            use_container_width=True,
        ):
            st.switch_page(PAGE_HOME)

        if st.button(
            "ℹ️ About CivicTrack",
            use_container_width=True,
        ):
            st.switch_page(PAGE_ABOUT)

    st.divider()

    st.caption(
        "Making public services more transparent, "
        "accessible and accountable."
    )

    st.caption(
        "CivicTrack Prototype | Version 2.1"
    )


# --------------------------------------------------
# RUN THE SELECTED PAGE
# --------------------------------------------------

navigation.run()


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div class="civic-footer">
        CivicTrack — Smart Public Grievance Management System<br>
        A software project prototype built with Python and Streamlit.
    </div>
    """,
    unsafe_allow_html=True,
)
