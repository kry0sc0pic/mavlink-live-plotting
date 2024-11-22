import asyncio

import streamlit as st
from utils import consumer


st.set_page_config(page_title="stream", layout="wide")

status = st.empty()
connect = st.checkbox("Connect to AutoPilot")
container = st.empty()
if connect:
    asyncio.run(
        consumer(container, status,subplot=[0]))
else:
    container.header("Live Data")
    cols = container.columns(4)
    cols[0].metric("AccX", f"- m/s²")
    cols[0].line_chart([], height=200, width=200)
    cols[1].metric("AccY", f"- m/s²")
    cols[1].line_chart([], height=200, width=200)
    cols[2].metric("AccZ", f"- m/s²")
    cols[2].line_chart([], height=200, width=200)
    cols[3].metric("Magnitude", f"- m/s²")
    cols[3].line_chart([], height=200, width=200)
    status.subheader(f"Disconnected.")