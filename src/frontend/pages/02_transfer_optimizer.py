import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Transfer Optimizer", page_icon="💰", layout="wide")
st.title("💰 Pareto Transfer Optimizer")

# Config Sidebar
st.sidebar.header("Optimization Constraints")
team_name = st.sidebar.text_input("Your Team Name", value="Arsenal")
target_role = st.sidebar.selectbox("Target Role", ["Advanced Forward", "Deep Lying Playmaker", "Sweeper Keeper"])
target_pos_group = st.sidebar.selectbox("Position Group", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
max_transfer = st.sidebar.number_input("Max Transfer Budget (€)", value=40000000, step=1000000)
max_wage = st.sidebar.number_input("Max Annual Wage (€)", value=5000000, step=500000)

if st.button("Find Pareto Optimal Targets"):
    with st.spinner("Calculating Multi-Objective Optimization..."):
        payload = {
            "target_role": target_role,
            "target_position_group": target_pos_group,
            "budget": {
                "max_transfer": max_transfer,
                "max_wage": max_wage
            },
            "weights": {"fit": 1.0, "value": 1.0, "investment": 1.0}
        }
        
        try:
            res = requests.post(f"{API_URL}/transfers/recommend", params={"team_name": team_name}, json=payload)
            res.raise_for_status()
            data = res.json()
            
            # Display Winners
            st.header("🏆 The Pareto Winners")
            col1, col2, col3 = st.columns(3)
            
            def render_card(col, title, player):
                with col:
                    st.subheader(title)
                    if player:
                        st.markdown(f"**{player.get('name')}** ({player.get('age')})")
                        st.markdown(f"**Club**: {player.get('club')}")
                        st.markdown(f"**Cost**: €{player.get('amortized_cost', 0)/1000000:.2f}M")
                        st.markdown(f"**Role Score**: {player.get('role_score', 0):.1f}")
                        st.markdown(f"**Trajectory**: {player.get('value_trajectory')}")
                    else:
                        st.write("No candidate found.")
                        
            render_card(col1, "Best Fit", data.get("best_fit"))
            render_card(col2, "Best Value", data.get("best_value"))
            render_card(col3, "Best Investment", data.get("best_investment"))
            
            st.divider()
            
            # Scatter Plot
            st.header("📈 Pareto Frontier Plot")
            all_candidates = data.get("all_feasible_candidates", [])
            if all_candidates:
                df = pd.DataFrame(all_candidates)
                
                fig = px.scatter(
                    df,
                    x="amortized_cost",
                    y="role_score",
                    color="value_trajectory",
                    hover_name="name",
                    hover_data=["age", "wage_annual", "club"],
                    title=f"Cost vs Fit for {target_role}",
                    labels={"amortized_cost": "Amortized Cost (€)", "role_score": "Role Fit Score"}
                )
                
                # Invert X axis so lower cost is on the right, meaning top-right is Pareto optimal
                fig.update_xaxes(autorange="reversed")
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df[["name", "age", "club", "role_score", "amortized_cost", "value_trajectory"]], use_container_width=True)
            else:
                st.warning("No feasible candidates found under these budget constraints.")
                
        except requests.exceptions.HTTPError as e:
            detail = e.response.json().get("detail", str(e)) if e.response is not None else str(e)
            st.warning(f"API Error: {detail}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {e}")
