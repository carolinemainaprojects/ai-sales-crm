import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="AI Sales CRM",
    page_icon="🤖"
)
st.write("Supabase URL:", st.secrets["SUPABASE_URL"])
st.write("Key starts with:", st.secrets["SUPABASE_KEY"][:15])
# Supabase connection
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# Page title
st.title("🤖 AI Sales CRM")
st.write("Submit your details and our team will get back to you.")

# Lead form
with st.form("lead_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    company = st.text_input("Company")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Submit Lead")

# Submit lead
if submitted:
    if not name or not email or not company or not message:
        st.warning("Please fill in all fields.")
    else:
        try:
            response = supabase.table("leads").insert({
                "name": name,
                "email": email,
                "company": company,
                "message": message
            }).execute()

            st.success("Lead submitted successfully! 🎉")
            st.write(response)

        except Exception as e:
            st.error(f"Supabase error: {e}")
