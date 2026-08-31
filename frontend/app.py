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

    gross_revenue_at_risk = revenue_at_risk

    outstanding_revenue_risk = max(
        gross_revenue_at_risk - amount_recovered,
        0,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">
                    Gross Revenue at Risk
                </div>
                <div class="card-value">
                    ₹{gross_revenue_at_risk:,.2f}
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
                    Outstanding Revenue Risk
                </div>
                <div class="card-value">
                    ₹{outstanding_revenue_risk:,.2f}
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
                    Revenue Recovered
                </div>
                <div class="card-value">
                    ₹{amount_recovered:,.2f}
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

# ==========================================================
# RECOVERY
# ==========================================================

# ==========================================================
# RECOVERY
# ==========================================================

elif page == "Recovery":

    st.title("Recovery Activity")

    st.caption(
        "Create AI-assisted or deterministic recovery decisions "
        "and record their outcomes."
    )

    # ------------------------------------------------------
    # CREATE RECOVERY DECISION
    # ------------------------------------------------------

    st.markdown("### Create Recovery Decision")

    try:

        failed_response = requests.get(
            f"{BACKEND_URL}/api/failed-payments",
            timeout=5,
        )

        if failed_response.status_code != 200:

            st.error(
                f"Failed Payments API returned "
                f"status {failed_response.status_code}."
            )

        else:

            failed_payments = failed_response.json()

            if not failed_payments:

                st.info(
                    "No failed payments are available for recovery."
                )

            else:

                payment_options = {
                    payment["payment_id"]: payment
                    for payment in failed_payments
                }

                selected_payment_id = st.selectbox(
                    "Select Failed Payment",
                    list(payment_options.keys()),
                )

                selected_payment = payment_options[
                    selected_payment_id
                ]

                st.markdown(
                    f"""
                    <div class="card">
                        <div class="card-label">
                            Selected Payment
                        </div>
                        <div class="card-value">
                            {selected_payment_id}
                        </div>
                        <div>
                            Invoice:
                            <strong>
                                {selected_payment.get("invoice_id", "-")}
                            </strong>
                        </div>
                        <div>
                            Failure Reason:
                            <strong>
                                {selected_payment.get(
                                    "failure_reason",
                                    "Unknown"
                                )}
                            </strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")

                recovery_mode = st.radio(
                    "Recovery Mode",
                    [
                        "Deterministic",
                        "AI-Assisted",
                    ],
                    horizontal=True,
                )

                mode = (
                    "ai"
                    if recovery_mode == "AI-Assisted"
                    else "deterministic"
                )

                if st.button(
                    "Create Recovery",
                    type="primary",
                    use_container_width=True,
                ):

                    try:

                        response = requests.post(
                            f"{BACKEND_URL}/api/recovery/"
                            f"{selected_payment_id}",
                            json={
                                "mode": mode,
                            },
                            timeout=30,
                        )

                        if response.status_code == 200:

                            result = response.json()

                            # Keep the newly created recovery ID
                            # available for the outcome section.
                            st.session_state[
                                "latest_recovery"
                            ] = result

                            st.success(
                                "Recovery decision created successfully."
                            )

                        else:

                            try:
                                error_detail = response.json().get(
                                    "detail",
                                    response.text,
                                )
                            except ValueError:
                                error_detail = response.text

                            st.error(
                                f"Recovery request failed "
                                f"({response.status_code}): "
                                f"{error_detail}"
                            )

                    except requests.exceptions.RequestException:

                        st.error(
                            "Unable to connect to the RazorPulse backend. "
                            "Make sure FastAPI is running on port 8000."
                        )

    except requests.exceptions.RequestException:

        st.error(
            "Unable to connect to the RazorPulse backend. "
            "Make sure FastAPI is running on port 8000."
        )

    # ------------------------------------------------------
    # LATEST RECOVERY DECISION
    # ------------------------------------------------------

    latest_recovery = st.session_state.get(
        "latest_recovery"
    )

    if latest_recovery:

        st.divider()

        st.markdown("### Recovery Decision")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Recovery ID",
                latest_recovery.get(
                    "recovery_id",
                    "-",
                ),
            )

        with col2:

            st.metric(
                "Strategy",
                latest_recovery.get(
                    "strategy",
                    "-",
                ),
            )

        with col3:

            st.metric(
                "Status",
                latest_recovery.get(
                    "status",
                    "-",
                ).upper(),
            )

        st.markdown("#### Decision Notes")

        st.info(
            latest_recovery.get(
                "notes",
                "No decision notes available.",
            )
        )

        # --------------------------------------------------
        # RECORD OUTCOME
        # --------------------------------------------------

        st.markdown("### Record Recovery Outcome")

        outcome_status = st.selectbox(
            "Outcome",
            [
                "completed",
                "failed",
                "manual_review",
            ],
        )

        invoice_amount = float(
            selected_payment.get(
                "amount",
                0,
            )
            or 0
        )

        amount_recovered = st.number_input(
            "Amount Recovered",
            min_value=0.0,
            max_value=invoice_amount if invoice_amount > 0 else None,
            value=0.0,
            step=100.0,
        )

        outcome_notes = st.text_area(
            "Outcome Notes",
            placeholder=(
                "Describe what happened during recovery..."
            ),
        )

        if st.button(
            "Save Recovery Outcome",
            type="primary",
            use_container_width=True,
        ):

            recovery_id = latest_recovery.get(
                "recovery_id"
            )

            try:

                response = requests.post(
                    f"{BACKEND_URL}/api/recovery/"
                    f"{recovery_id}/outcome",
                    params={
                        "status": outcome_status,
                        "amount_recovered": amount_recovered,
                        "notes": outcome_notes,
                    },
                    timeout=10,
                )

                if response.status_code == 200:

                    outcome = response.json()

                    # Update the stored recovery information
                    # so the UI reflects the latest state.
                    st.session_state[
                        "latest_recovery"
                    ] = outcome

                    st.success(
                        "Recovery outcome recorded successfully."
                    )

                    st.markdown(
                        "#### Recorded Outcome"
                    )

                    result_col1, result_col2, result_col3 = (
                        st.columns(3)
                    )

                    with result_col1:

                        st.metric(
                            "Status",
                            outcome.get(
                                "status",
                                "-",
                            ).upper(),
                        )

                    with result_col2:

                        st.metric(
                            "Amount Recovered",
                            f"₹{float(outcome.get('amount_recovered', 0) or 0):,.2f}",
                        )

                    with result_col3:

                        st.metric(
                            "Recovery ID",
                            outcome.get(
                                "recovery_id",
                                "-",
                            ),
                        )

                else:

                    try:
                        error_detail = response.json().get(
                            "detail",
                            response.text,
                        )
                    except ValueError:
                        error_detail = response.text

                    st.error(
                        f"Outcome update failed "
                        f"({response.status_code}): "
                        f"{error_detail}"
                    )

            except requests.exceptions.RequestException:

                st.error(
                    "Unable to connect to the RazorPulse backend. "
                    "Make sure FastAPI is running on port 8000."
                )

        with st.expander("View Latest API Response"):

            st.json(
                st.session_state.get(
                    "latest_recovery",
                    {},
                )
            )

    # ------------------------------------------------------
    # RECOVERY HISTORY
    # ------------------------------------------------------

    st.divider()

    st.markdown("### Recovery History")

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

# ==========================================================
# AUDIT TRAIL
# ==========================================================

elif page == "Audit Trail":

    st.title("Audit Trail")

    st.caption(
        "Track recovery decisions, AI recommendations, "
        "guardrail decisions, and recovery outcomes."
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

                # --------------------------------------------------
                # Summary metrics
                # --------------------------------------------------

                total_events = len(df)

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

                recovery_outcomes = len(
                    df[
                        df["event_type"]
                        == "RECOVERY_OUTCOME"
                    ]
                )

                entities_tracked = df[
                    "entity_id"
                ].nunique()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Total Events",
                        total_events,
                    )

                with col2:
                    st.metric(
                        "Recovery Decisions",
                        recovery_decisions,
                    )

                with col3:
                    st.metric(
                        "Recovery Outcomes",
                        recovery_outcomes,
                    )

                with col4:
                    st.metric(
                        "Invoices Tracked",
                        entities_tracked,
                    )

                st.divider()

                # --------------------------------------------------
                # Human-readable event labels
                # --------------------------------------------------

                event_labels = {
                    "RECOVERY_DECISION": "Recovery Decision",
                    "AI_RECOVERY_DECISION": "AI Recovery Decision",
                    "RECOVERY_OUTCOME": "Recovery Outcome",
                }

                display_df = df.copy()

                display_df["Event"] = (
                    display_df["event_type"]
                    .map(event_labels)
                    .fillna(display_df["event_type"])
                )

                display_df["Entity"] = (
                    display_df["entity_type"]
                    .astype(str)
                    .str.title()
                )

                display_df["Details"] = (
                    display_df["message"]
                    .astype(str)
                    .str.replace(
                        "â‚¹",
                        "₹",
                        regex=False,
                    )
                )

                display_df["Time"] = pd.to_datetime(
                    display_df["created_at"],
                    errors="coerce",
                ).dt.strftime(
                    "%d %b %Y, %H:%M"
                )

                display_df["Entity ID"] = (
                    display_df["entity_id"]
                )

                # --------------------------------------------------
                # Event filter
                # --------------------------------------------------

                st.markdown(
                    "### Decision History"
                )

                filter_options = [
                    "All Events",
                    "Recovery Decisions",
                    "AI Decisions",
                    "Recovery Outcomes",
                ]

                selected_filter = st.selectbox(
                    "Filter Events",
                    filter_options,
                )

                filtered_df = display_df

                if selected_filter == "Recovery Decisions":

                    filtered_df = display_df[
                        display_df["event_type"]
                        == "RECOVERY_DECISION"
                    ]

                elif selected_filter == "AI Decisions":

                    filtered_df = display_df[
                        display_df["event_type"]
                        == "AI_RECOVERY_DECISION"
                    ]

                elif selected_filter == "Recovery Outcomes":

                    filtered_df = display_df[
                        display_df["event_type"]
                        == "RECOVERY_OUTCOME"
                    ]

                # --------------------------------------------------
                # Main audit table
                # --------------------------------------------------

                audit_table = filtered_df[
                    [
                        "Time",
                        "Event",
                        "Entity",
                        "Entity ID",
                        "Details",
                    ]
                ]

                st.dataframe(
                    audit_table,
                    width="stretch",
                    hide_index=True,
                )

                # --------------------------------------------------
                # Recovery lifecycle explanation
                # --------------------------------------------------

                st.markdown(
                    "### RazorPulse Recovery Lifecycle"
                )

                st.info(
                    "Payment failure → Risk analysis → "
                    "AI recommendation → Deterministic guardrail → "
                    "Recovery decision → Recovery outcome → Audit trail"
                )

                # --------------------------------------------------
                # Latest recovery activity
                # --------------------------------------------------

                outcome_df = display_df[
                    display_df["event_type"]
                    == "RECOVERY_OUTCOME"
                ]

                if not outcome_df.empty:

                    st.markdown(
                        "### Latest Recovery Outcomes"
                    )

                    latest_outcomes = outcome_df[
                        [
                            "Time",
                            "Entity ID",
                            "Details",
                        ]
                    ].head(5)

                    st.dataframe(
                        latest_outcomes,
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