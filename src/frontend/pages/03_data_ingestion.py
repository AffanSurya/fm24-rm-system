import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Data Ingestion", page_icon="📥")
st.title("📥 Data Ingestion")

st.markdown("""
Upload your FM24 Custom View exports (`.html` or `.rtf`) here.
The backend will parse them in the background, normalize attributes, and fit the similarity models automatically.
""")

uploaded_files = st.file_uploader("Choose HTML/RTF files", accept_multiple_files=True, type=["html", "htm", "rtf"])

if st.button("Run Ingestion Pipeline"):
    if not uploaded_files:
        st.warning("Please upload at least one file.")
    else:
        with st.spinner("Uploading and triggering background pipeline..."):
            try:
                files_payload = []
                for f in uploaded_files:
                    files_payload.append(('files', (f.name, f.getvalue(), 'text/html' if 'htm' in f.name else 'text/rtf')))
                    
                res = requests.post(f"{API_URL}/ingest", files=files_payload)
                res.raise_for_status()
                st.success("Files successfully sent to backend! Pipeline is running.")
                st.info("The global state will automatically reload once the task finishes.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to API: {e}")
