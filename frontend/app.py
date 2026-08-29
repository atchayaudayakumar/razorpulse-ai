import streamlit as st
import pandas as pd
import requests


# ==========================================================
# CONFIGURATION
# ==========================================================

BACKEND_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="RazorPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# STYLING
# ==========================================================

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


# ==========================================================
# SIDEBAR
# ==========================================================

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


# ==========================================================
# HEADER
# ==========================================================

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

    # ---------- Fetch live backend data ----------

    try:
        failed_response = requests.get(
            f"{BACKEND_URL}/api/failed-payments",
            timeout=5,
        )

        recovery_response = requests.get(
            f"{BACKEND_URL}/api/recovery-attempts",
            timeout=5,
        )

        risk_response = requests.get(
            f"{BACKEND_URL}/api/risk-analysis",
            timeout=5,
        )

        if failed_response.status_code != 200:
            raise RuntimeError(
                "Failed Payments API unavailable."
            )

        if recovery_response.status_code != 200:
            raise RuntimeError(
                "Recovery API unavailable."
            )

        if risk_response.status_code != 200:
            raise RuntimeError(
                "Risk Analysis API unavailable."
            )

        failed_payments = failed_response.json()
        recovery_attempts = recovery_response.json()
        risk_data = risk_response.json()

    except (
        requests.exceptions.RequestException,
        RuntimeError,
    ) as exc:

        failed_payments = []
        recovery_attempts = []
        risk_data = []

        st.warning(
            f"Live backend data unavailable: {exc}"
        )

    # ---------- Calculate KPIs ----------

    failed_count = len(
        failed_payments
    )

    high_risk_count = sum(
        1
        for risk in risk_data
        if str(
            risk.get("risk_level", "")
        ).upper()
        == "HIGH"
    )

    revenue_at_risk = sum(
        float(
            risk.get(
                "revenue_at_risk",
                0,
            )
            or 0
        )
        for risk in risk_data
    )

    amount_recovered = sum(
        float(
            recovery.get(
                "amount_recovered",
                0,
            )
            or 0
        )
        for recovery in recovery_attempts
    )

    recovery_rate = (
        (amount_recovered / revenue_at_risk) * 100
        if revenue_at_risk > 0
        else 0
    )

    # ---------- KPI Cards ----------

    # ---------- KPI Cards ----------

    st.markdown(
        '<div class="section-title">'
        "Financial Overview"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">
                    Revenue at Risk
                </div>
                <div class="card-value">
                    ₹{revenue_at_risk:,.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">
                    Failed Payments
                </div>
                <div class="card-value">
                    {failed_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">
                    High-Risk Payments
                </div>
                <div class="card-value">
                    {high_risk_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">
                    Recovery Rate
                </div>
                <div class="card-value">
                    {recovery_rate:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- Risk & Revenue Intelligence ----------

    st.markdown(
        '<div class="section-title">'
        "Risk & Revenue Intelligence"
        "</div>",
        unsafe_allow_html=True,
    )

    chart_col, risk_col = st.columns([2, 1])

    with chart_col:

        st.markdown("#### Revenue at Risk")

        if risk_data:

            revenue_chart = pd.DataFrame(
                {
                    "Payment": range(
                        1,
                        len(risk_data) + 1,
                    ),
                    "Revenue at Risk": [
                        float(
                            item.get(
                                "revenue_at_risk",
                                0,
                            )
                            or 0
                        )
                        for item in risk_data
                    ],
                }
            )

            st.line_chart(
                revenue_chart.set_index(
                    "Payment"
                ),
                height=280,
            )

        else:

            st.info(
                "No risk data available yet."
            )

    with risk_col:

        st.markdown("#### Risk Distribution")

        medium_risk_count = sum(
            1
            for risk in risk_data
            if str(
                risk.get(
                    "risk_level",
                    "",
                )
            ).upper()
            == "MEDIUM"
        )

        low_risk_count = sum(
            1
            for risk in risk_data
            if str(
                risk.get(
                    "risk_level",
                    "",
                )
            ).upper()
            == "LOW"
        )

        risk_distribution = pd.DataFrame(
            {
                "Risk Level": [
                    "High",
                    "Medium",
                    "Low",
                ],
                "Payments": [
                    high_risk_count,
                    medium_risk_count,
                    low_risk_count,
                ],
            }
        )

        st.bar_chart(
            risk_distribution.set_index(
                "Risk Level"
            ),
            height=280,
        )

    # ---------- Recent Failed Payments ----------

    st.markdown(
        '<div class="section-title">'
        "Recent Failed Payments"
        "</div>",
        unsafe_allow_html=True,
    )

    if failed_payments:

        payments_df = pd.DataFrame(
            failed_payments
        )

        payments_df = payments_df.rename(
            columns={
                "payment_id": "Payment ID",
                "invoice_id": "Invoice ID",
                "status": "Status",
                "failure_reason": "Failure Reason",
                "attempted_at": "Attempted At",
            }
        )

        st.dataframe(
            payments_df.head(10),
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No failed payments found in the database."
        )

    # ---------- AI Insight ----------

    st.markdown(
        '<div class="section-title">'
        "AI Recovery Insight"
        "</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "RazorPulse combines deterministic recovery policies "
        "with AI-assisted recommendations. AI suggestions remain "
        "subject to policy guardrails before a recovery strategy "
        "is selected."
    )


# ==========================================================
# FAILED PAYMENTS
# ==========================================================

elif page == "Failed Payments":

    st.title("Failed Payments")

    st.caption(
        "Monitor and investigate failed payment attempts."
    )

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/failed-payments",
            timeout=5,
        )

        if response.status_code == 200:

            payments = response.json()

            if payments:

                df = pd.DataFrame(
                    payments
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Failed Payments",
                        len(df),
                    )

                with col2:
                    st.metric(
                        "Affected Invoices",
                        df["invoice_id"].nunique(),
                    )

                st.divider()

                display_df = df.rename(
                    columns={
                        "payment_id": "Payment ID",
                        "invoice_id": "Invoice ID",
                        "status": "Status",
                        "failure_reason": "Failure Reason",
                        "attempted_at": "Attempted At",
                    }
                )

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                )

            else:

                st.info(
                    "No failed payments found in the database."
                )

        else:

            st.error(
                f"Failed Payments API returned "
                f"status {response.status_code}."
            )

    except requests.exceptions.RequestException:

        st.error(
            "Unable to connect to the RazorPulse backend. "
            "Make sure FastAPI is running on port 8000."
        )


# ==========================================================
# RECOVERY
# ==========================================================

elif page == "Recovery":

    st.title("Recovery Activity")

    st.caption(
        "AI-assisted recovery strategies and recovery outcomes."
    )

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/recovery-attempts",
            timeout=5,
        )

        if response.status_code == 200:

            recoveries = response.json()

            if recoveries:

                df = pd.DataFrame(
                    recoveries
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Recovery Attempts",
                        len(df),
                    )

                with col2:

                    completed = len(
                        df[
                            df["status"]
                            .astype(str)
                            .str.lower()
                            == "completed"
                        ]
                    )

                    st.metric(
                        "Completed",
                        completed,
                    )

                with col3:

                    total_recovered = df[
                        "amount_recovered"
                    ].sum()

                    st.metric(
                        "Amount Recovered",
                        f"₹{total_recovered:,.2f}",
                    )

                st.divider()

                st.markdown(
                    "### Recovery Decisions"
                )

                display_df = df.rename(
                    columns={
                        "recovery_id": "Recovery ID",
                        "invoice_id": "Invoice ID",
                        "amount": "Invoice Amount",
                        "currency": "Currency",
                        "strategy": "Strategy",
                        "status": "Status",
                        "amount_recovered": "Amount Recovered",
                        "notes": "Decision Notes",
                    }
                )

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                )

            else:

                st.info(
                    "No recovery attempts found "
                    "in the database."
                )

        else:

            st.error(
                f"Recovery API returned "
                f"status {response.status_code}."
            )

    except requests.exceptions.RequestException:

        st.error(
            "Unable to connect to the RazorPulse backend. "
            "Make sure FastAPI is running on port 8000."
        )


# ==========================================================
# RISK ANALYSIS
# ==========================================================

elif page == "Risk Analysis":

    st.title("Risk Analysis")

    st.caption(
        "Revenue risk assessment for payment attempts."
    )

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/risk-analysis",
            timeout=5,
        )

        if response.status_code == 200:

            risks = response.json()

            if risks:

                df = pd.DataFrame(
                    risks
                )

                high_risk = len(
                    df[
                        df["risk_level"]
                        .astype(str)
                        .str.upper()
                        == "HIGH"
                    ]
                )

                medium_risk = len(
                    df[
                        df["risk_level"]
                        .astype(str)
                        .str.upper()
                        == "MEDIUM"
                    ]
                )

                low_risk = len(
                    df[
                        df["risk_level"]
                        .astype(str)
                        .str.upper()
                        == "LOW"
                    ]
                )

                total_revenue_at_risk = df[
                    "revenue_at_risk"
                ].sum()

                col1, col2, col3, col4 = st.columns(
                    4
                )

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
                    risk_counts.set_index(
                        "Risk Level"
                    )
                )

                st.divider()

                st.markdown(
                    "### Payment Risk Details"
                )

                display_df = df.rename(
                    columns={
                        "payment_id": "Payment ID",
                        "invoice_id": "Invoice ID",
                        "risk_score": "Risk Score",
                        "risk_level": "Risk Level",
                        "revenue_at_risk": "Revenue at Risk",
                        "reason": "Reason",
                    }
                )

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

                df = pd.DataFrame(
                    logs
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Total Events",
                        len(df),
                    )

                with col2:

                    recovery_decisions = len(
                        df[
                            df["event_type"].isin(
                                [
                                    "RECOVERY_DECISION",
                                    "AI_RECOVERY_DECISION",
                                ]
                            )
                        ]
                    )

                    st.metric(
                        "Recovery Decisions",
                        recovery_decisions,
                    )

                with col3:

                    st.metric(
                        "Entities Tracked",
                        df["entity_id"].nunique(),
                    )

                st.divider()

                st.markdown(
                    "### Recent Events"
                )

                display_df = df.rename(
                    columns={
                        "created_at": "Time",
                        "event_type": "Event",
                        "entity_type": "Entity Type",
                        "entity_id": "Entity ID",
                        "message": "Message",
                    }
                )

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
                f"Audit API returned "
                f"status {response.status_code}."
            )

    except requests.exceptions.RequestException:

        st.error(
            "Unable to connect to the RazorPulse backend. "
            "Make sure FastAPI is running on port 8000."
        )
