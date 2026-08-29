import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="RazorPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = "http://127.0.0.1:8000"


def get_api_data(endpoint):
    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()

        return []

    except requests.exceptions.RequestException:
        return []

# ---------- Styling ----------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .main-title {
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 0;
        }

        .subtitle {
            color: #9ca3af;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .card {
            padding: 1.2rem;
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            background: rgba(128,128,128,0.06);
        }

        .card-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }

        .card-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 0.3rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 650;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ⚡ RazorPulse")
    st.caption("AI-Powered Revenue Recovery")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Failed Payments",
            "Recovery",
            "Risk Analysis",
            "Audit Trail",
        ],
    )

    st.divider()

    st.caption("SYSTEM")
    st.success("Backend Online")
    st.caption("RazorPulse v0.1.0")


# ---------- Header ----------
st.markdown(
    '<div class="main-title">Revenue Recovery Dashboard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Monitor failed payments, revenue risk, AI recommendations, "
    "and recovery performance."
    "</div>",
    unsafe_allow_html=True,
)


# ==========================================================
# OVERVIEW
# ==========================================================

if page == "Overview":

    # ---------- KPI Cards ----------
    st.markdown(
        '<div class="section-title">Financial Overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="card">
                <div class="card-label">Revenue at Risk</div>
                <div class="card-value">₹4.25L</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <div class="card-label">Failed Payments</div>
                <div class="card-value">127</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="card">
                <div class="card-label">High-Risk Payments</div>
                <div class="card-value">31</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="card">
                <div class="card-label">Recovery Rate</div>
                <div class="card-value">68%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- Charts ----------
    st.markdown(
        '<div class="section-title">Risk & Revenue Intelligence</div>',
        unsafe_allow_html=True,
    )

    chart_col, risk_col = st.columns([2, 1])

    with chart_col:
        st.markdown("#### Revenue at Risk Trend")

        trend_data = pd.DataFrame(
            {
                "Day": [
                    "Mon",
                    "Tue",
                    "Wed",
                    "Thu",
                    "Fri",
                    "Sat",
                    "Sun",
                ],
                "Revenue at Risk": [
                    280000,
                    315000,
                    290000,
                    360000,
                    390000,
                    410000,
                    425000,
                ],
            }
        )

        st.line_chart(
            trend_data.set_index("Day"),
            height=280,
        )

    with risk_col:
        st.markdown("#### Risk Distribution")

        risk_data = pd.DataFrame(
            {
                "Risk Level": ["High", "Medium", "Low"],
                "Payments": [31, 52, 44],
            }
        )

        st.bar_chart(
            risk_data.set_index("Risk Level"),
            height=280,
        )

    # ---------- Failed Payments ----------
    st.markdown(
        '<div class="section-title">Recent Failed Payments</div>',
        unsafe_allow_html=True,
    )

    payments = pd.DataFrame(
        {
            "Customer": [
                "Customer A",
                "Customer B",
                "Customer C",
                "Customer D",
                "Customer E",
            ],
            "Amount": [
                "₹25,000",
                "₹12,500",
                "₹8,000",
                "₹32,000",
                "₹18,500",
            ],
            "Failure Reason": [
                "Insufficient funds",
                "Card expired",
                "Payment declined",
                "Insufficient funds",
                "Unknown failure",
            ],
            "Risk": [
                "HIGH",
                "HIGH",
                "MEDIUM",
                "HIGH",
                "MEDIUM",
            ],
            "Recovery": [
                "Payment Extension",
                "Update Payment Method",
                "Controlled Retry",
                "Payment Extension",
                "Manual Review",
            ],
        }
    )
    st.dataframe(
    payments,
    width="stretch",
    hide_index=True,
    )

    # ---------- AI Insight ----------
    st.markdown(
        '<div class="section-title">AI Recovery Insight</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Most high-risk failures are currently associated with "
        "insufficient funds. RazorPulse can prioritize payment "
        "extensions for these cases while keeping recovery decisions "
        "within deterministic policy guardrails."
    )


# ==========================================================
# FAILED PAYMENTS
# ==========================================================

elif page == "Failed Payments":

    st.title("Failed Payments")
    st.caption("Monitor and investigate failed payment attempts.")

    st.warning(
        "Live payment data will be connected to the FastAPI backend "
        "in the next phase."
    )


# ==========================================================
# RECOVERY
# ==========================================================

elif page == "Recovery":

    st.title("Recovery Activity")
    st.caption("Track AI-assisted recovery decisions.")

    st.info(
        "Recovery attempts, strategies, confidence scores, "
        "and outcomes will appear here."
    )


# ==========================================================
# RISK ANALYSIS
# ==========================================================

elif page == "Risk Analysis":

    st.subheader("Risk Analysis")
    st.caption(
        "AI-assisted revenue risk assessment for payment attempts."
    )

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/risk-analysis",
            timeout=5,
        )

        if response.status_code == 200:

            risks = response.json()

            if risks:

                df = pd.DataFrame(risks)

                # ---------- Risk Metrics ----------
                high_risk = len(
                    df[df["risk_level"].str.upper() == "HIGH"]
                )

                medium_risk = len(
                    df[df["risk_level"].str.upper() == "MEDIUM"]
                )

                low_risk = len(
                    df[df["risk_level"].str.upper() == "LOW"]
                )

                total_revenue_at_risk = df[
                    "revenue_at_risk"
                ].sum()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Revenue at Risk",
                        f"₹{total_revenue_at_risk:,.2f}",
                    )

                with col2:
                    st.metric(
                        "High Risk",
                        high_risk,
                    )

                with col3:
                    st.metric(
                        "Medium Risk",
                        medium_risk,
                    )

                with col4:
                    st.metric(
                        "Low Risk",
                        low_risk,
                    )

                st.divider()

                # ---------- Risk Distribution ----------
                st.markdown(
                    "### Risk Distribution"
                )

                risk_counts = pd.DataFrame(
                    {
                        "Risk Level": [
                            "HIGH",
                            "MEDIUM",
                            "LOW",
                        ],
                        "Payments": [
                            high_risk,
                            medium_risk,
                            low_risk,
                        ],
                    }
                )

                st.bar_chart(
                    risk_counts.set_index("Risk Level")
                )

                st.divider()

                # ---------- Detailed Analysis ----------
                st.markdown(
                    "### Payment Risk Details"
                )

                display_df = df[
                    [
                        "payment_id",
                        "invoice_id",
                        "risk_score",
                        "risk_level",
                        "revenue_at_risk",
                        "reason",
                    ]
                ].copy()

                display_df.columns = [
                    "Payment ID",
                    "Invoice ID",
                    "Risk Score",
                    "Risk Level",
                    "Revenue at Risk",
                    "Reason",
                ]

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                )

            else:
                st.info(
                    "No payment risk data available yet."
                )

        else:
            st.error(
                f"Risk API returned status "
                f"{response.status_code}."
            )

    except requests.exceptions.RequestException:
        st.error(
            "Unable to connect to the RazorPulse backend."
        )

# ==========================================================
# AUDIT TRAIL
# ==========================================================
elif page == "Audit Trail":

    st.title("Audit Trail")
    st.caption(
        "Track RazorPulse decisions, recovery actions, "
        "and system events."
    )

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/audit-logs",
            timeout=5,
        )

        if response.status_code == 200:

            logs = response.json()

            if logs:
                df = pd.DataFrame(logs)

                # ---------- Audit Metrics ----------
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Total Events",
                        len(df),
                    )

                with col2:
                    st.metric(
                        "Recovery Decisions",
                        len(
                            df[
                                df["event_type"]
                                == "RECOVERY_DECISION"
                            ]
                        ),
                    )

                with col3:
                    st.metric(
                        "Entities Tracked",
                        df["entity_id"].nunique(),
                    )

                st.divider()

                # ---------- Event Timeline ----------
                st.markdown("### Recent Events")

                display_df = df[
                    [
                        "created_at",
                        "event_type",
                        "entity_type",
                        "entity_id",
                        "message",
                    ]
                ].copy()

                display_df.columns = [
                    "Time",
                    "Event",
                    "Entity Type",
                    "Entity ID",
                    "Message",
                ]

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                )

            else:
                st.info(
                    "No audit events have been recorded yet."
                )

        else:
            st.error(
                f"Audit API returned status "
                f"{response.status_code}."
            )

    except requests.exceptions.RequestException:
        st.error(
            "Unable to connect to the RazorPulse backend. "
            "Make sure FastAPI is running on port 8000."
        )