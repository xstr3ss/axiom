import streamlit as st
import subprocess
import os
from qdrant_client import QdrantClient

# --- Configuration ---
st.set_page_config(page_title="Fable Mission Control", page_icon="🤖", layout="wide")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

def get_qdrant_client():
    try:
        return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    except Exception:
        return None

def get_log_tail(filepath, lines=30):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return "".join(f.readlines()[-lines:])
    return f"No log found at {filepath} yet. Fable hasn't run this task."

# --- UI Layout ---
st.title("🤖 Fable Mission Control")
st.markdown("Monitor Fable's autonomous brain, view live operations, and trigger manual overrides safely.")

# --- System Health Metrics ---
client = get_qdrant_client()
memory_count = "OFFLINE"
if client:
    try:
        memory_count = client.count(collection_name="fable_ast_memory").count
    except Exception:
        memory_count = "Collection not found"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Brain Size (Learned Experiences)", memory_count)
with col2:
    st.metric("Vector Database", "ONLINE" if client else "OFFLINE")
with col3:
    st.metric("Operating Mode", "Fully Autonomous")

st.divider()

# --- Interactive Tabs ---
tab1, tab2, tab3 = st.tabs(["🎛️ Control Panel", "🧠 Memory Explorer", "📜 Live System Logs"])

with tab1:
    st.subheader("Manual Overrides")
    st.write("Click these buttons to force Fable to run a task right now instead of waiting for the background timer.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 Force Global Harvester Sync"):
            st.info("Triggering harvester in the background...")
            subprocess.Popen(["python", "harvester.py"])
            st.success("Harvester started! Check the logs tab in a few minutes.")
            
    with col_b:
        if st.button("🕵️ Force Security & Tech Debt Patrol"):
            st.info("Triggering codebase patrol...")
            subprocess.Popen(["python", "proactive.py"])
            st.success("Patrol started! Fable will open a GitHub PR if it finds anything.")

with tab2:
    st.subheader("What does Fable remember?")
    if client and isinstance(memory_count, int) and memory_count > 0:
        if st.button("Fetch Latest Learned Behaviors"):
            records = client.scroll(collection_name="fable_ast_memory", limit=5)[0]
            for record in records:
                with st.expander(f"Memory: {record.payload.get('signature', 'Unknown')}"):
                    st.write("**Tags:**", ", ".join(record.payload.get('tags', [])))
                    st.write("**Memory Type:**", record.payload.get('type', 'episodic'))
                    st.text_area("Context/Problem", record.payload.get('context', ''), height=100)
    else:
        st.warning("Qdrant is offline or Fable's memory is completely empty.")

with tab3:
    st.subheader("Background Daemon Logs")
    
    log_sel = st.selectbox("Choose a log to view:", ["Autonomous Sync Log", "Proactive Patrol Log"])
    
    if log_sel == "Autonomous Sync Log":
        st.code(get_log_tail("/tmp/fable-sync.log", lines=50), language="bash")
    else:
        st.code(get_log_tail("/tmp/fable-patrol.log", lines=50), language="bash")
        
    if st.button("🔄 Refresh Logs"):
        st.rerun()
