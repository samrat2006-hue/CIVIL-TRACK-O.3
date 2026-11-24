import streamlit as st


def apply_theme():
    """Apply CivicTrack's shared, public-service visual theme."""

    st.markdown(
        """
        <style>
        :root {
            --ct-orange: #fbe4c7;
            --ct-page: #fff9f7;
            --ct-cream: #fff3ee;
            --ct-button-orange: #fbe4c7;
            --ct-button-hover: #f4cfa5;
            --ct-surface-orange: #fff2e5;
            --ct-brown: #593b2d;
            --ct-brown-soft: #80604c;
            --ct-green: #286347;
            --ct-green-dark: #1d5038;
            --ct-sage: #e3efe3;
            --ct-blue: #285f91;
            --ct-cyan: #dff2f2;
            --ct-cyan-ink: #176b73;
            --ct-pink: #f8e5e9;
            --ct-white: #ffffff;
            --ct-border: #e8cdb0;
            --ct-shadow: 0 8px 24px rgba(89, 59, 45, 0.08);
        }

        html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", Arial, sans-serif;
        }

        .stApp {
            background: var(--ct-page);
            color: var(--ct-brown);
        }

        [data-testid="stAppViewContainer"] {
            background: var(--ct-page);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 249, 247, 0.96);
        }

        [data-testid="stMain"] > div {
            padding-top: 1.7rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: var(--ct-cream);
            border-right: 1px solid var(--ct-border);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] small {
            color: var(--ct-brown-soft);
        }

        h1, h2, h3, h4, h5, h6,
        [data-testid="stHeading"] {
            color: var(--ct-brown) !important;
            letter-spacing: -0.025em;
        }

        h1 { font-weight: 800 !important; }
        h2, h3 { font-weight: 750 !important; }

        p, li, label, [data-testid="stMarkdownContainer"] {
            color: var(--ct-brown);
        }

        a { color: var(--ct-blue) !important; }
        a:hover { color: var(--ct-green) !important; }

        .civic-brand {
            color: var(--ct-brown);
            font-size: 30px;
            font-weight: 850;
            letter-spacing: -1.2px;
            line-height: 1.1;
        }

        .civic-brand span { color: var(--ct-green); }

        .civic-subtitle {
            color: var(--ct-brown-soft);
            font-size: 10px;
            font-weight: 750;
            letter-spacing: 1.15px;
            line-height: 1.55;
            margin: 7px 0 18px;
        }

        .civic-hero {
            position: relative;
            overflow: hidden;
            padding: clamp(28px, 5vw, 52px);
            border: 1px solid var(--ct-border);
            border-radius: 22px;
            margin: 0 0 30px;
            background: linear-gradient(120deg, #fbe4c7 0%, #f8dfbd 100%);
            box-shadow: 0 18px 38px rgba(89, 59, 45, 0.16);
        }

        .civic-hero::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            right: -75px;
            bottom: -150px;
            border: 1px solid var(--ct-pink);
            border-radius: 50%;
            opacity: 0.55;
            box-shadow: 0 0 0 26px rgba(248, 229, 233, 0.10),
                        0 0 0 54px rgba(248, 229, 233, 0.055);
            pointer-events: none;
        }

        .civic-hero h1 {
            max-width: 780px;
            color: var(--ct-brown) !important;
            font-size: clamp(30px, 4.4vw, 48px);
            font-weight: 800;
            line-height: 1.13;
            margin: 13px 0 12px;
        }

        .civic-hero p {
            max-width: 760px;
            color: var(--ct-brown) !important;
            font-size: 16px;
            line-height: 1.75;
            margin-bottom: 0;
        }

        .civic-hero-tag {
            color: var(--ct-green-dark) !important;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.6px;
            text-transform: uppercase;
        }

        .civic-section-title {
            color: var(--ct-brown);
            font-size: clamp(20px, 2.3vw, 25px);
            font-weight: 800;
            letter-spacing: -0.4px;
            margin: 29px 0 15px;
        }

        .civic-card,
        .civic-stat-card,
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--ct-surface-orange);
            border: 1px solid var(--ct-border) !important;
            border-radius: 16px;
            box-shadow: var(--ct-shadow);
        }

        .civic-card {
            box-sizing: border-box;
            min-height: 174px;
            margin: 0 0 14px;
            padding: 21px;
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        .civic-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(89, 59, 45, 0.13);
        }

        .civic-card-icon {
            color: var(--ct-green);
            font-size: 29px;
            line-height: 1.2;
            margin-bottom: 12px;
        }

        .civic-card-title {
            color: var(--ct-brown);
            font-size: 17px;
            font-weight: 750;
            line-height: 1.35;
            margin-bottom: 8px;
        }

        .civic-card-description {
            color: var(--ct-brown-soft);
            font-size: 13px;
            line-height: 1.65;
        }

        .civic-stat-card {
            min-height: 104px;
            padding: 18px 20px;
        }

        .civic-stat-label {
            color: var(--ct-brown-soft);
            font-size: 12px;
            font-weight: 650;
        }

        .civic-stat-value {
            color: var(--ct-green);
            font-size: clamp(21px, 2.5vw, 28px);
            font-weight: 800;
            margin-top: 9px;
        }

        .civic-more {
            color: var(--ct-cyan-ink);
            font-size: 16px;
            font-weight: 750;
            padding: 12px;
            text-align: center;
        }

        .civic-footer {
            border-top: 1px solid var(--ct-border);
            color: var(--ct-brown-soft);
            font-size: 12px;
            line-height: 1.7;
            margin-top: 25px;
            padding: 20px 0 8px;
            text-align: center;
        }

        .dashboard-header {
            background: linear-gradient(120deg, #fbe4c7, #f8dfbd);
            border: 1px solid var(--ct-border);
            border-radius: 19px;
            box-shadow: var(--ct-shadow);
            color: var(--ct-brown);
            margin-bottom: 22px;
            padding: 26px 30px;
        }

        .dashboard-header h1 {
            color: var(--ct-brown) !important;
            font-size: clamp(26px, 3vw, 34px);
            margin: 0 0 8px;
        }

        .dashboard-header p {
            color: var(--ct-brown) !important;
            margin: 0;
        }

        .stat-card {
            background: var(--ct-surface-orange);
            border: 1px solid var(--ct-border);
            border-radius: 15px;
            box-shadow: var(--ct-shadow);
            min-height: 105px;
            padding: 19px;
        }

        .stat-label { color: var(--ct-brown-soft); font-size: 13px; }
        .stat-value {
            color: var(--ct-green);
            font-size: 27px;
            font-weight: 800;
            margin-top: 8px;
        }

        div.stButton > button,
        [data-testid="stFormSubmitButton"] button {
            min-height: 43px;
            border: 1px solid #d7ad7b !important;
            border-radius: 10px;
            background: var(--ct-button-orange) !important;
            color: var(--ct-brown) !important;
            font-weight: 700;
            transition: background 140ms ease, border-color 140ms ease,
                        transform 140ms ease;
        }

        div.stButton > button *,
        [data-testid="stFormSubmitButton"] button * {
            color: inherit !important;
        }

        div.stButton > button[kind="primary"],
        [data-testid="stBaseButton-primary"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--ct-button-orange) !important;
            border-color: #d7ad7b !important;
            color: var(--ct-brown) !important;
        }

        div.stButton > button[kind="primary"] *,
        [data-testid="stBaseButton-primary"] *,
        [data-testid="stFormSubmitButton"] button[kind="primary"] * {
            color: var(--ct-brown) !important;
        }

        div.stButton > button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            background: var(--ct-button-hover) !important;
            border-color: var(--ct-brown-soft) !important;
            color: var(--ct-brown) !important;
            transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"]:hover,
        [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--ct-button-hover) !important;
            border-color: var(--ct-brown-soft) !important;
            color: var(--ct-brown) !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stFileUploader"] section,
        [data-baseweb="select"] > div {
            background: var(--ct-white);
            border-color: #d8c6b3;
            border-radius: 9px;
            color: var(--ct-brown);
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-baseweb="select"] > div:focus-within {
            border-color: var(--ct-blue);
            box-shadow: 0 0 0 1px var(--ct-blue);
        }

        [data-testid="stForm"] {
            background: var(--ct-cream);
            border: 1px solid var(--ct-border);
            border-radius: 16px;
            padding: 20px 22px;
        }

        [data-testid="stMetric"] {
            background: var(--ct-surface-orange);
            border: 1px solid var(--ct-border);
            border-radius: 14px;
            box-shadow: var(--ct-shadow);
            padding: 15px 17px;
        }

        [data-testid="stMetricLabel"] { color: var(--ct-brown-soft); }
        [data-testid="stMetricValue"] { color: var(--ct-green); }

        [data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid var(--ct-border);
        }

        [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
            color: var(--ct-brown);
        }

        [data-testid="stExpander"],
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background: rgba(255, 247, 235, 0.75);
            border-radius: 12px;
        }

        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--ct-green) !important;
            border-bottom-color: var(--ct-green) !important;
        }

        [data-testid="stDataFrame"], [data-testid="stTable"] {
            background: var(--ct-white);
            border: 1px solid var(--ct-border);
            border-radius: 12px;
            overflow: hidden;
        }

        [data-testid="stProgressBar"] > div > div {
            background: var(--ct-green);
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--ct-brown-soft);
        }

        @media (max-width: 700px) {
            [data-testid="stMain"] > div {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }

            .civic-hero { border-radius: 16px; }
            [data-testid="stForm"] { padding: 16px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
