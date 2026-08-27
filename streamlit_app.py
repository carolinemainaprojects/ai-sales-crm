import streamlit as st
from supabase import create_client
from google import genai
import resend
import json

st.set_page_config(
    page_title="AI Sales CRM",
    page_icon="🤖"
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
# Page
# -------------------------

st.title("🤖 AI Sales CRM")
st.write("Submit your details and our AI will qualify your lead.")

# -------------------------
# Lead form
# -------------------------

with st.form("lead_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    company = st.text_input("Company")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Submit Lead")

# -------------------------
# Process lead
# -------------------------

if submitted:

    if not name or not email or not company or not message:
        st.warning("Please fill in all fields.")

    else:

        try:
            # -------------------------
            # AI qualification
            # -------------------------

            prompt = f"""
You are an AI sales qualification assistant.

Analyze this sales lead:

Name: {name}
Email: {email}
Company: {company}
Message: {message}

Return ONLY valid JSON in this exact format:

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
- ai_reason should briefly explain the decision
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
            # Save lead to Supabase
            # -------------------------

            result = supabase.table("leads").insert({
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
            }).execute()

            # -------------------------
            # Send notification
            # -------------------------

            notification_sent = False

            if priority == "High":

                resend.Emails.send({
                    "from": "AI Sales CRM <onboarding@resend.dev>",
                    "to": [st.secrets["SALES_TEAM_EMAIL"]],
                    "subject": f"🔥 High-Priority Lead: {company}",
                    "html": f"""
                    <h2>🔥 New High-Priority Lead</h2>

                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Company:</strong> {company}</p>

                    <p><strong>Lead Score:</strong> {score}/100</p>
                    <p><strong>Qualified:</strong> {"Yes" if qualified else "No"}</p>

                    <h3>Lead Message</h3>
                    <p>{message}</p>

                    <h3>AI Reason</h3>
                    <p>{ai_reason}</p>

                    <p>Please follow up with this lead as soon as possible.</p>
                    """
                })

                notification_sent = True

            # -------------------------
            # Update notification status
            # -------------------------

            if notification_sent:

                supabase.table("leads").update({
                    "notification_sent": True
                }).eq("email", email).execute()

            # -------------------------
            # Display results
            # -------------------------

            st.success("Lead submitted successfully! 🎉")

            st.subheader("🤖 AI Qualification")

            st.write(f"**Score:** {score}/100")
            st.write(f"**Priority:** {priority}")
            st.write(
                f"**Qualified:** {'Yes' if qualified else 'No'}"
            )
            st.write(f"**AI Reason:** {ai_reason}")

            if notification_sent:
                st.success("📧 High-priority notification sent!")

        except Exception as e:
            st.error(f"Error: {e}")
