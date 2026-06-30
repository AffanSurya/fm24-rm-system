import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Squad Matrix", page_icon="📋", layout="wide")
st.title("📋 Squad Matrix")

team_name = st.text_input("Enter your Team Name (e.g. Arsenal)", value="")

if st.button("Analyze Squad") and team_name:
    with st.spinner("Crunching numbers..."):
        try:
            # Get Retention
            ret_res = requests.get(f"{API_URL}/squad/retention", params={"team_name": team_name})
            ret_res.raise_for_status()
            retention_data = ret_res.json()
            
            st.header("Retention Matrix")
            if not retention_data:
                st.warning("No data returned. Did you ingest data and spell the team name correctly?")
            else:
                df = pd.DataFrame(retention_data)
                
                # Style the retention signal
                def color_signal(val):
                    color = 'green' if val == 'Keep' else 'red' if val == 'Sell' else 'orange'
                    return f'color: {color}'
                    
                st.dataframe(df.style.applymap(color_signal, subset=['retention_signal']), use_container_width=True)
                
            # Get Depth (Hardcoding Gegenpress for now, can make it dynamic later)
            st.header("Squad Depth (Gegenpress)")
            depth_res = requests.get(f"{API_URL}/squad/depth", params={"team_name": team_name, "target_tactic": "Gegenpress"})
            depth_res.raise_for_status()
            depth_data = depth_res.json()
            
            for group, data in depth_data.items():
                st.subheader(group.capitalize())
                st.write(f"Depth Status: **{data['depth_status']}**")
                if data["players"]:
                    df_d = pd.DataFrame(data["players"])
                    st.dataframe(df_d, use_container_width=True)
                else:
                    st.info("No players in this positional group.")
                    
        except requests.exceptions.HTTPError as e:
            detail = e.response.json().get("detail", str(e)) if e.response is not None else str(e)
            st.warning(f"API Error: {detail}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {e}")
