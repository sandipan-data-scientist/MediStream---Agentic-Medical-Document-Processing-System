# File: ui/streamlit_app.py

import streamlit as st
import requests
import os

API_URL = os.getenv("MEDISTREAM_API_URL", "http://localhost:8000")

st.set_page_config(page_title="MediStream", layout="centered")

st.title("MediStream")
st.write("Upload a medical document to extract, code, and structure its contents automatically.")

uploaded_file = st.file_uploader(
    "Upload a PDF, image, or text file",
    type=["pdf", "jpg", "jpeg", "png", "txt"]
)

if uploaded_file is not None:
    st.write(f"File received: {uploaded_file.name}")

    if st.button("Run MediStream Pipeline"):

        with st.spinner("Processing document through the agentic pipeline..."):
            response = requests.post(
                f"{API_URL}/process",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            )

        if response.status_code == 200:
            result = response.json()

            st.success("Pipeline completed successfully.")

            st.subheader("Pipeline Summary")
            st.write(f"Reviewer verdict: {result['reviewer_verdict']}")
            st.write(f"Timeline events created: {result['timeline_event_count']}")

            if result["validation_issues"]:
                st.warning("Validation issues found:")
                for issue in result["validation_issues"]:
                    st.write(f"- {issue}")
            else:
                st.write("No validation issues detected.")

            st.subheader("Download Outputs")

            col1, col2 = st.columns(2)

            with col1:
                xml_response = requests.get(
                    f"{API_URL}/download/xml",
                    params={"path": result["xml_path"]}
                )
                if xml_response.status_code == 200:
                    st.download_button(
                        label="Download XML",
                        data=xml_response.content,
                        file_name="medistream_output.xml",
                        mime="application/xml"
                    )

            with col2:
                xlsx_response = requests.get(
                    f"{API_URL}/download/xlsx",
                    params={"path": result["xlsx_path"]}
                )
                if xlsx_response.status_code == 200:
                    st.download_button(
                        label="Download Excel",
                        data=xlsx_response.content,
                        file_name="medistream_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        else:
            st.error(f"Pipeline failed: {response.text}")