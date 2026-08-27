import streamlit as st
from supabase import create_client
from google import genai
import resend
import json

# -------------------------
# Page configuration
# -------------------------

st.set_page_config(
    page_title="AI Sales CRM",
    page_icon="🤖",
    layout="wide"
)

# -------------------------
# Connections
# -------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

resend.api_key = st.secrets["RESEND_API_KEY"]

# -------------------------
# Header
# -------------------------

st.title("🤖 AI Sales CRM")
st.write(
    "AI-powered lead qualification, scoring, and sales notifications."
)

# -------------------------
# Lead Submission Form
# -------------------------

st.header("📝 Submit a New Lead")

with st.form("lead_form"):

    name = st.text_input("Name")
    email = st.text_input("Email")
    company = st.text_input("Company")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Submit Lead")

# -------------------------
# Process Lead
# -------------------------

if submitted:

    if not name or not email or not company or not message:

        st.warning("Please fill in all fields.")

    else:

        try:

            # -------------------------
            # AI Qualification
            # -------------------------

            prompt = f"""
You are an AI sales qualification assistant.

Analyze this sales lead:

Name: {name}
Email: {email}
Company: {company}
Message: {message}

Return ONLY valid JSON in exactly this format:

{{
    "score": 0,
    "priority": "Low",
    "qualified": false,
    "ai_reason": "short explanation"
}}

Rules:

- score must be between 0 and 100
- priority must be Low, Medium, or High
- qualified must be true or false
- ai_reason must briefly explain the decision
"""

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            ai_result = json.loads(response.text)

            score = int(ai_result["score"])
            priority = ai_result["priority"]
            qualified = bool(ai_result["qualified"])
            ai_reason = ai_result["ai_reason"]

            # -------------------------
            # Save Lead
            # -------------------------

            insert_response = (
                supabase
                .table("leads")
                .insert({
                    "name": name,
                    "email": email,
                    "company": company,
                    "message": message,
                    "status": "new",
                    "priority": priority,
                    "score": score,
                    "ai_reason": ai_reason,
                    "qualified": qualified,
                    "notification_sent": False
                })
                .execute()
            )

            # Get the exact lead ID
            lead_id = insert_response.data[0]["id"]

            # -------------------------
            # Email Notification
            # -------------------------

            notification_sent = False

            if priority == "High":

                resend.Emails.send({

                    "from": "AI Sales CRM <onboarding@resend.dev>",

                    "to": [
                        st.secrets["SALES_TEAM_EMAIL"]
                    ],

                    "subject": f"🔥 High-Priority Lead: {company}",

                    "html": f"""
                    <h2>🔥 New High-Priority Lead</h2>

                    <p><strong>Name:</strong> {name}</p>

                    <p><strong>Email:</strong> {email}</p>

                    <p><strong>Company:</strong> {company}</p>

                    <p><strong>Lead Score:</strong> {score}/100</p>

                    <p><strong>Priority:</strong> {priority}</p>

                    <p>
                    <strong>Qualified:</strong>
                    {"Yes" if qualified else "No"}
                    </p>

                    <h3>Lead Message</h3>

                    <p>{message}</p>

                    <h3>AI Reason</h3>

                    <p>{ai_reason}</p>

                    <p>
                    Please follow up with this lead as soon as possible.
                    </p>
                    """
                })

                notification_sent = True

            # -------------------------
            # Update Exact Lead
            # -------------------------

            if notification_sent:

                supabase.table("leads").update({
                    "notification_sent": True
                }).eq(
                    "id",
                    lead_id
                ).execute()

            # -------------------------
            # Display AI Result
            # -------------------------

            st.success(
                "Lead submitted successfully! 🎉"
            )

            st.subheader("🤖 AI Qualification")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Lead Score",
                    f"{score}/100"
                )

            with col2:

                st.metric(
                    "Priority",
                    priority
                )

            with col3:

                st.metric(
                    "Qualified",
                    "Yes" if qualified else "No"
                )

            st.info(
                f"🧠 **AI Reason:** {ai_reason}"
            )

            if notification_sent:

                st.success(
                    "📧 High-priority notification sent!"
                )

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =========================================================
# CRM DASHBOARD
# =========================================================

st.divider()

st.header("📊 Sales CRM Dashboard")

try:

    leads_response = (
        supabase
        .table("leads")
        .select("*")
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    leads = leads_response.data

    if leads:

        # -------------------------
        # Metrics
        # -------------------------

        total_leads = len(leads)

        high_priority = sum(
            1
            for lead in leads
            if lead.get("priority") == "High"
        )

        medium_priority = sum(
            1
            for lead in leads
            if lead.get("priority") == "Medium"
        )

        low_priority = sum(
            1
            for lead in leads
            if lead.get("priority") == "Low"
        )

        qualified_leads = sum(
            1
            for lead in leads
            if lead.get("qualified") is True
        )

        notifications_sent = sum(
            1
            for lead in leads
            if lead.get("notification_sent") is True
        )

        scores = [
            lead.get("score", 0)
            for lead in leads
            if lead.get("score") is not None
        ]

        average_score = (
            round(
                sum(scores) / len(scores),
                1
            )
            if scores
            else 0
        )

        # -------------------------
        # Main Metrics
        # -------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Leads",
            total_leads
        )

        col2.metric(
            "🔥 High Priority",
            high_priority
        )

        col3.metric(
            "✅ Qualified",
            qualified_leads
        )

        col4.metric(
            "📈 Avg Score",
            average_score
        )

        st.divider()

        # -------------------------
        # Priority Overview
        # -------------------------

        st.subheader("🎯 Lead Priority Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "🔥 High",
            high_priority
        )

        col2.metric(
            "🟡 Medium",
            medium_priority
        )

        col3.metric(
            "🟢 Low",
            low_priority
        )

        st.write(
            f"📧 **Notifications Sent:** "
            f"{notifications_sent}"
        )

        st.divider()

        # -------------------------
        # Filter
        # -------------------------

        st.subheader("🔎 Filter Leads")

        priority_filter = st.selectbox(
            "Select priority",
            [
                "All",
                "High",
                "Medium",
                "Low"
            ]
        )

        if priority_filter == "All":

            filtered_leads = leads

        else:

            filtered_leads = [
                lead
                for lead in leads
                if lead.get("priority")
                == priority_filter
            ]

        st.write(
            f"Showing **{len(filtered_leads)}** lead(s)"
        )

        # -------------------------
        # Lead Cards
        # -------------------------

        for lead in filtered_leads:

            lead_priority = lead.get(
                "priority",
                "Unknown"
            )

            if lead_priority == "High":

                priority_icon = "🔥"

            elif lead_priority == "Medium":

                priority_icon = "🟡"

            else:

                priority_icon = "🟢"

            lead_name = lead.get(
                "name",
                "Unknown"
            )

            lead_company = lead.get(
                "company",
                "Unknown"
            )

            lead_score = lead.get(
                "score",
                0
            )

            with st.expander(
                f"{priority_icon} "
                f"{lead_name} — "
                f"{lead_company} — "
                f"{lead_score}/100"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**📧 Email:** "
                        f"{lead.get('email', '')}"
                    )

                    st.write(
                        f"**🎯 Priority:** "
                        f"{lead_priority}"
                    )

                    st.write(
                        f"**📊 Score:** "
                        f"{lead_score}/100"
                    )

                with col2:

                    qualified_status = (
                        "Yes ✅"
                        if lead.get("qualified")
                        else "No ❌"
                    )

                    notification_status = (
                        "Sent 📧"
                        if lead.get(
                            "notification_sent"
                        )
                        else "Not sent"
                    )

                    st.write(
                        f"**Qualified:** "
                        f"{qualified_status}"
                    )

                    st.write(
                        f"**Notification:** "
                        f"{notification_status}"
                    )

                st.write(
                    "### 💬 Lead Message"
                )

                st.write(
                    lead.get(
                        "message",
                        ""
                    )
                )

                st.write(
                    "### 🧠 AI Reason"
                )

                st.info(
                    lead.get(
                        "ai_reason",
                        "No AI reasoning available."
                    )
                )

    else:

        st.info(
            "No leads have been submitted yet."
        )

except Exception as e:

    st.error(
        f"Dashboard error: {e}"
            )
                
