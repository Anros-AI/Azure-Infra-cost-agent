
import streamlit as st
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

st.set_page_config(
    page_title="Azure Cost Agent",
    page_icon="💰",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.header("Azure Credentials")
    st.caption("Leave blank to use demo data")

    region = st.text_input(
        "AWS Region",
        value=os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    )
    sub_id = st.text_input(
        "Azure Subscription ID",
        value=os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    )
    tenant_id = st.text_input(
        "Azure Tenant ID",
        value=os.environ.get("AZURE_TENANT_ID", "")
    )
    client_id = st.text_input(
        "Azure Client ID",
        value=os.environ.get("AZURE_CLIENT_ID", "")
    )
    client_secret = st.text_input(
        "Azure Client Secret",
        type="password",
        value=os.environ.get("AZURE_CLIENT_SECRET", "")
    )

    if st.button("Save Credentials", use_container_width=True):
        os.environ["AWS_DEFAULT_REGION"]    = region
        os.environ["AZURE_SUBSCRIPTION_ID"] = sub_id
        os.environ["AZURE_TENANT_ID"]       = tenant_id
        os.environ["AZURE_CLIENT_ID"]       = client_id
        os.environ["AZURE_CLIENT_SECRET"]   = client_secret
        st.success("Saved!")

    st.markdown("---")
    st.markdown("### Example Questions")
    examples = [
        "Which service costs the most?",
        "Were there any cost spikes?",
        "How can I reduce my Azure costs?",
        "Break down costs by resource group",
        "What is my daily average spend?",
        "Should I use Reserved Instances?",
    ]
    for ex in examples:
        if st.button(ex, key=ex[:20], use_container_width=True):
            st.session_state["prefill"] = ex

    st.markdown("---")
    if st.button("Clear History", use_container_width=True):
        st.session_state.pop("history", None)

# Main title
st.title("💰 Azure Infrastructure Cost Analysis Agent")
st.caption("Powered by Claude on AWS Bedrock · RAG + Tool Calling + Self Reflection")

# Input
prefill = st.session_state.pop("prefill", "")
query   = st.text_area(
    "Ask anything about your Azure costs:",
    value=prefill,
    height=90,
    placeholder="e.g. Which service is costing the most this month?"
)

col1, col2 = st.columns([1, 5])
with col1:
    go = st.button("Analyse", type="primary", use_container_width=True)

# Agent
@st.cache_resource(show_spinner="Loading agent and knowledge base...")
def get_agent():
    from agent.orchestrator import AzureCostAgent
    return AzureCostAgent()

if go and query.strip():
    agent = get_agent()
    with st.spinner("Fetching data, reasoning, and reflecting..."):
        result = agent.run(query)

    if "history" not in st.session_state:
        st.session_state["history"] = []
    st.session_state["history"].insert(0, result)

elif go:
    st.warning("Please type a question first.")

# Display results
for result in st.session_state.get("history", []):
    st.markdown("---")
    st.markdown(f"**Query:** {result['query']}")
    st.markdown("### Answer")
    st.markdown(result["answer"])

    with st.expander("Agent Internals", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Tool Called",       result.get("tool_called", "-"))
        c2.metric("Reflection Score",  f"{result['reflection'].get('score','?')}/10")
        c3.metric("Attempts",          result.get("attempts", 1))

        st.info(f"Reflection: {result['reflection'].get('reason','')}")

        st.markdown("**Knowledge Base Sources:**")
        for src in result.get("kb_sources", []):
            st.markdown(f"- {src}")

        st.markdown("**Raw Tool Output:**")
        st.json(result.get("tool_output", {}))
