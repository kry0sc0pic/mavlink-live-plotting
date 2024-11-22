import asyncio

import streamlit as st
from utils import consumer


st.set_page_config(page_title="stream", layout="wide")

status = st.empty()
connect = st.checkbox("Connect to AutoPilot")
container = st.empty()
if connect:
    asyncio.run(
        consumer(container, status, subplot=[3]))
else:
    container.header("Live Data")
    cols = container.columns(4)

    cols[0].metric("MagX", f"- mG")
    cols[0].line_chart([], height=200, width=200)
    cols[1].metric("MagY", f"- mG")
    cols[1].line_chart([], height=200, width=200)
    cols[2].metric("MagZ", f"- mG")
    cols[2].line_chart([], height=200, width=200)
    cols[3].metric("Magnitude", f"- mG")
    cols[3].line_chart([], height=200, width=200)

    
    status.subheader(f"Disconnected.")