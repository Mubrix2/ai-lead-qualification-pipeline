# frontend/app.py
import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Lead Qualification Demo",
    page_icon="🎯",
    layout="centered",
)

st.title("🎯 AI Lead Qualification System")
st.caption("Submit a lead and see AI scoring in real time")

with st.form("lead_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="Emeka Obi")
    with col2:
        email = st.text_input("Email *", placeholder="emeka@company.com")

    col3, col4 = st.columns(2)
    with col3:
        company = st.text_input("Company", placeholder="TechCorp Nigeria")
    with col4:
        phone = st.text_input("Phone", placeholder="+234...")

    message = st.text_area(
        "Message *",
        height=120,
        placeholder="Tell us about your project, timeline, and what you need...",
    )

    submitted = st.form_submit_button(
        "Submit Lead",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not name or not email or not message:
        st.error("Name, email, and message are required")
    else:
        with st.spinner("AI is qualifying this lead..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/leads/qualify",
                    json={
                        "name": name,
                        "email": email,
                        "company": company,
                        "phone": phone,
                        "message": message,
                        "source": "Demo Form",
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                grade_colours = {
                    "HOT": "🔥",
                    "WARM": "🌡️",
                    "COLD": "❄️",
                }
                emoji = grade_colours.get(data["grade"], "📊")

                st.divider()
                st.markdown(f"## {emoji} Lead Grade: {data['grade']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("AI Score", f"{data['score']}/100")
                with col2:
                    st.metric(
                        "Slack Notified",
                        "Yes" if data["slack_notified"] else "No",
                    )

                st.markdown("**AI Reasoning:**")
                st.info(data["reasoning"])

                st.markdown("**Recommended Action:**")
                st.success(data["recommended_action"])

                st.caption(f"Saved to Airtable: {data['airtable_record_id']}")

            except Exception as e:
                st.error(f"Error: {str(e)}")