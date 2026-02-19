import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Fall Detection Dashboard", page_icon="", layout="wide")

st.title("Team 17: Fall Detection Live Dashboard")
st.write("Monitoring Edge Devices in real-time...")

try:
    #fetch data from fog container and specified address
    response = requests.get("http://fog:8000/alerts", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        alerts = data.get("alerts", [])
        
        st.metric(label="Total Critical Alerts Processed", value=data.get("total_alerts", 0))
        
        if alerts:
            st.success("Live Data Streaming...")
            df = pd.DataFrame(alerts)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Waiting for falls to be detected. No alerts received yet.")
            
    else:
        st.warning(f"Fog Node returned an unexpected status: {response.status_code}")
        
except Exception as e:
    st.error("Could not connect to the Fog node.")
