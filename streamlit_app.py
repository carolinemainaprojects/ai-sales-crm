import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="AI Sales CRM",
    page_icon="🤖"
)

# Connect to Supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.title("🤖 AI Sales CRM")
st.write("Submit your details and our team will get back to you.")

with st.form("lead_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    company = st.text_input("Company")
    message = st.text_area("How can we help you?")

    submitted = st.form_submit_button("Submit Lead")

    if submitted:
        if not name or not email or not message:
            st.warning("Please fill in your name, email, and message.")
        else:
            try:
                supabase.table("leads").insert({
                    "name": name,
                    "email": email,
                    "company": company,
                    "message": message
                }).execute()

                st.success("Thank you! Your lead has been submitted.")

            except Exception as e:
                st.error("Something went wrong. Please try again.")
