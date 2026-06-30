import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Tactical Config", page_icon="⚙️")
st.title("⚙️ Tactical Config Editor")

st.markdown("""
Edit your underlying mathematical role weights here. 
The system uses these weights to score how well a player fits a specific tactical archetype.
Changes made here will be saved instantly to the backend configuration.
""")

@st.cache_data
def fetch_config():
    try:
        res = requests.get(f"{API_URL}/config/roles")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching config: {e}")
        return None

config = fetch_config()

if config:
    # Separate metadata from roles
    metadata = config.get("_metadata", {})
    roles_only = {k: v for k, v in config.items() if k != "_metadata"}
    
    st.subheader("Model Metadata")
    st.write(f"**Version**: {metadata.get('version', 'Unknown')}")
    st.write(f"**FM Patch**: {metadata.get('fm_patch', 'Unknown')}")
    st.write(f"**Description**: {metadata.get('description', '')}")
    
    st.divider()
    
    # We edit roles one by one to keep the UI clean
    selected_role = st.selectbox("Select Role to Edit", list(roles_only.keys()))
    
    if selected_role:
        role_data = roles_only[selected_role]
        
        # Convert to DataFrame for st.data_editor
        df = pd.DataFrame(list(role_data.items()), columns=["Attribute", "Weight"])
        
        st.write(f"Editing weights for **{selected_role}**")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        if st.button("Save Changes to Backend"):
            with st.spinner("Saving..."):
                # Convert back to dict
                new_role_data = {row["Attribute"]: row["Weight"] for _, row in edited_df.iterrows() if row["Attribute"]}
                
                # Update our config dictionary
                config[selected_role] = new_role_data
                
                try:
                    res = requests.put(f"{API_URL}/config/roles", json=config)
                    res.raise_for_status()
                    st.success("Weights successfully updated!")
                    # Clear cache to fetch new data next time
                    st.cache_data.clear()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to update config: {e}")
