# Azure Infrastructure Cost Analysis Agent

An AI agent that analyses your Azure cloud costs, detects anomalies,
and suggests optimisations using natural language questions.

Built as the final project for the AI Academy Engineering Track.

---

## What It Does

Ask questions like:
- Which Azure service cost the most last month?
- Were there any cost spikes in the last 30 days?
- How can I reduce my Azure infrastructure costs?
- Break down my spend by resource group

The agent:
1. Retrieves relevant knowledge from ChromaDB using RAG
2. Reasons about which tool to call using Claude on AWS Bedrock
3. Fetches real data from Azure Cost Management API
4. Generates a clear actionable answer with specific dollar amounts
5. Self reflects and scores its own answer retrying if quality is low

---

## Tech Stack

- LLM: Claude 3 Haiku on AWS Bedrock
- Embeddings: Amazon Titan Embeddings V2
- Vector Store: ChromaDB local persistent
- Cost Data: Azure Cost Management REST API
- UI: Streamlit
- Container: Docker
- Evaluation: LLM as judge plus keyword matching

---

## Project Structure

- agent/orchestrator.py — Main agentic loop
- agent/rag_retriever.py — ChromaDB and Titan Embeddings RAG
- tools/azure_cost.py — 4 Azure Cost Management tools
- eval/evaluator.py — 8 test cases with LLM as judge
- runbooks/ — 8 Azure cost knowledge base docs
- app.py — Streamlit web UI
- main.py — CLI entry point
- generate_kb.py — Creates knowledge base files
- Dockerfile — Container definition
- architecture.mmd — System diagram

---

## Option 1 - Run with Docker (Recommended)

Build the image:

    docker build -t azure-cost-agent .

Run the container:

    docker run -p 8501:8501 \
      -e AWS_DEFAULT_REGION=us-east-1 \
      -e AWS_ACCESS_KEY_ID=your-access-key \
      -e AWS_SECRET_ACCESS_KEY=your-secret-key \
      -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
      -e AZURE_TENANT_ID=your-tenant-id \
      -e AZURE_CLIENT_ID=your-client-id \
      -e AZURE_CLIENT_SECRET=your-client-secret \
      azure-cost-agent

Open in browser: http://localhost:8501

---

## Option 2 - Run Locally

Clone and install:

    git clone https://github.com/Anros-AI/Azure-Infra-cost-agent.git
    cd Azure-Infra-cost-agent
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Set environment variables:

    export AWS_DEFAULT_REGION=us-east-1
    export AZURE_SUBSCRIPTION_ID=your-subscription-id
    export AZURE_TENANT_ID=your-tenant-id
    export AZURE_CLIENT_ID=your-client-id
    export AZURE_CLIENT_SECRET=your-client-secret

Generate knowledge base:

    python3 generate_kb.py

Run web UI:

    streamlit run app.py

Run CLI:

    python3 main.py

Single query:

    python3 main.py --query "Which service costs the most?"

Run evaluation:

    python3 main.py --eval

---

## Evaluation Results

- Pass Rate: 87.5% (7/8 test cases)
- Tool Accuracy: 87.5%
- Average Quality: 9.2/10
- Average Latency: 7.6s

---

## Assignment Coverage

- Data Preparation: 8 Azure cost knowledge markdown files
- RAG Pipeline: ChromaDB plus Titan Embeddings V2
- Reasoning and Reflection: Self scoring loop with retry
- Tool Calling: 4 tools with real Azure REST API
- Evaluation: 8 test cases LLM as judge scoring

---

## Demo Video

[Add your demo video link here]

---

## LinkedIn Post

Excited to share my AI Academy final project - an Azure Infrastructure
Cost Analysis Agent! The agent connects to Azure Cost Management API,
uses RAG with ChromaDB and Amazon Titan Embeddings to retrieve cost
optimisation knowledge, and lets DevOps engineers ask natural language
questions about their cloud spend. Built with Python and Claude 3 Haiku
on AWS Bedrock. The agent detects cost anomalies, suggests specific
savings with dollar estimates, and self reflects on every answer retrying
if quality is too low. Also containerized with Docker for easy deployment
anywhere. Part of the AI Academy Engineering Track.
AIAcademy DevOps FinOps AWS GenAI Docker

---

## Acknowledgements

Final capstone project for the AI Academy Engineering Track.
