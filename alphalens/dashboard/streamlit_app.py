"""
Streamlit dashboard for monitoring and control.

Run with: streamlit run alphalens/dashboard/streamlit_app.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Alphalens Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("🤖 Alphalens Autonomous Trading System")
st.markdown("---")


def get_status():
    """Get system status from API."""
    try:
        response = requests.get(f"{API_URL}/status")
        return response.json() if response.status_code == 200 else None
    except:
        return None


def get_performance():
    """Get performance metrics from API."""
    try:
        response = requests.get(f"{API_URL}/performance")
        return response.json() if response.status_code == 200 else None
    except:
        return None


def get_learning_summary():
    """Get learning summary from API."""
    try:
        response = requests.get(f"{API_URL}/memory/learning-summary")
        return response.json() if response.status_code == 200 else None
    except:
        return None


# Sidebar
with st.sidebar:
    st.header("⚙️ Control Panel")

    # System status
    status = get_status()

    if status:
        st.success("✅ System Online")

        if status["is_running"]:
            st.info("🔄 Orchestrator Running")
        elif status["is_paused"]:
            st.warning("⏸️ System Paused")
        else:
            st.info("💤 System Idle")

    else:
        st.error("❌ System Offline")

    st.markdown("---")

    # Control buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Start"):
            try:
                requests.post(f"{API_URL}/start")
                st.success("Started!")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("⏸️ Pause"):
            try:
                requests.post(f"{API_URL}/pause")
                st.success("Paused!")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("🛑 Emergency Stop", type="primary"):
        try:
            requests.post(f"{API_URL}/emergency-stop")
            st.error("Emergency Stop Activated!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)

# Main content
if status:
    # Overview metrics
    st.header("📊 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Stage", status.get("current_stage", "Unknown"))

    with col2:
        st.metric("Iteration", status.get("iteration", 0))

    with col3:
        performance = get_performance()
        if performance:
            st.metric("Total Trades", performance.get("total_trades", 0))

    with col4:
        if performance:
            st.metric("Successful Factors", performance.get("successful_factors", 0))

    st.markdown("---")

    # Performance section
    st.header("💰 Performance")

    if performance:
        col1, col2, col3 = st.columns(3)

        portfolio = performance.get("portfolio", {})

        with col1:
            total_value = portfolio.get("total_value", 1_000_000)
            st.metric("Portfolio Value", f"${total_value:,.2f}")

        with col2:
            cash = portfolio.get("cash", 0)
            st.metric("Cash", f"${cash:,.2f}")

        with col3:
            equity = total_value - cash
            st.metric("Equity", f"${equity:,.2f}")

    st.markdown("---")

    # Learning summary
    st.header("🧠 Learning Summary")

    learning = get_learning_summary()
    if learning:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Strategies Tested", learning.get("total_strategies_tested", 0))

        with col2:
            success_rate = learning.get("success_rate", 0)
            st.metric("Success Rate", f"{success_rate:.1%}")

        with col3:
            avg_sharpe = learning.get("avg_successful_sharpe_ratio")
            if avg_sharpe:
                st.metric("Avg Sharpe Ratio", f"{avg_sharpe:.2f}")

    st.markdown("---")

    # Agents status
    st.header("🤖 Agents Status")

    agents_status = status.get("agents", {})
    agent_data = []

    for agent_name, agent_info in agents_status.items():
        agent_data.append({
            "Agent": agent_name.replace("_", " ").title(),
            "Status": agent_info.get("status", "unknown"),
            "Actions": agent_info.get("actions_logged", 0)
        })

    if agent_data:
        df = pd.DataFrame(agent_data)
        st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # Recent factors
    st.header("🎯 Successful Factors")

    try:
        response = requests.get(f"{API_URL}/factors/successful?limit=5")
        if response.status_code == 200:
            factors = response.json().get("factors", [])

            if factors:
                for factor in factors:
                    with st.expander(f"📈 {factor.get('description', 'Unknown Factor')}"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            sharpe = factor.get("sharpe_ratio")
                            if sharpe:
                                st.metric("Sharpe Ratio", f"{sharpe:.2f}")

                        with col2:
                            ic = factor.get("information_coefficient")
                            if ic:
                                st.metric("IC", f"{ic:.4f}")

                        with col3:
                            st.metric("Confidence", f"{factor.get('confidence_score', 0):.1%}")
            else:
                st.info("No successful factors yet")
    except Exception as e:
        st.error(f"Could not load factors: {e}")

    st.markdown("---")

    # Risk events
    st.header("⚠️ Recent Risk Events")

    try:
        response = requests.get(f"{API_URL}/risk/events?limit=10")
        if response.status_code == 200:
            events = response.json().get("events", [])

            if events:
                event_data = []
                for event in events:
                    event_data.append({
                        "Time": event.get("occurred_at", "")[:19],
                        "Type": event.get("event_type", ""),
                        "Severity": event.get("severity", ""),
                        "Description": event.get("description", "")[:50] + "..."
                    })

                df = pd.DataFrame(event_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("No risk events - system healthy!")
    except Exception as e:
        st.error(f"Could not load risk events: {e}")

else:
    st.error("❌ Cannot connect to API server")
    st.info("Make sure the API server is running: `python -m alphalens.dashboard.api`")

# Auto-refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()
