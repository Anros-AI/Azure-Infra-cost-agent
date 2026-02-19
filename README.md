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

## Architecture
```
User Question
      |
      v
Agent Orchestrator (Claude 3 Haiku on AWS Bedrock)
      |
      |--- RAG Retriever --- ChromaDB --- 8 Azure Cost KB docs
      |
      |--- Tool: get_cost_by_service        Azure Cost Management API
      |--- Tool: get_daily_cost_trend       Anomaly detection
      |--- Tool: get_cost_by_resource_group Per team cost
      |--- Tool: suggest_optimisations      Savings recommendations
      |
      v
Self Reflection (scores answer 0-10, retries if below 6)
```

See architecture.mmd for the full diagram.

---

## Tech Stack

| Component      | Technology                        |
|---------------|-----------------------------------|
| LLM           | Claude 3 Haiku on AWS Bedrock     |
| Embeddings    | Amazon Titan Embeddings V2        |
| Vector Store  | ChromaDB local persistent         |
| Cost Data     | Azure Cost Management REST API    |
| UI            | Streamlit                         |
| Evaluation    | LLM as judge plus keyword matching|

---

## Project Structure
```
azure-cost-agent/
├── agent/
│   ├── orchestrator.py      Main agentic loop
│   └── rag_retriever.py     ChromaDB and Titan Embeddings RAG
├── tools/
│   └── azure_cost.py        4 Azure Cost Management tools
├── eval/
│   └── evaluator.py         8 test cases with LLM as judge
├── runbooks/                8 Azure cost knowledge base docs
├── data/                    ChromaDB storage and eval results
├── app.py                   Streamlit web UI
├── main.py                  CLI entry point
├── generate_kb.py           Creates knowledge base files
├── architecture.mmd         System diagram
├── requirements.txt
└── README.md
```

---

## Setup and Run

### 1. Clone and Install
```bash
git clone https://github.com/YOUR_USERNAME/azure-cost-agent.git
cd azure-cost-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export AWS_DEFAULT_REGION=us-east-1

# Optional - agent uses mock data without these
export AZURE_SUBSCRIPTION_ID=your-subscription-id
export AZURE_TENANT_ID=your-tenant-id
export AZURE_CLIENT_ID=your-client-id
export AZURE_CLIENT_SECRET=your-client-secret
```

### 3. Generate Knowledge Base
```bash
python3 generate_kb.py
```

### 4. Run

Web UI:
```bash
streamlit run app.py
```

CLI interactive:
```bash
python3 main.py
```

Single query:
```bash
python3 main.py --query "Which service costs the most?"
```

Evaluation:
```bash
python3 main.py --eval
```

---

## Tools

| Tool | What It Returns |
|------|----------------|
| get_cost_by_service | Cost per Azure service last 30 days |
| get_daily_cost_trend | Daily spend with anomaly flags |
| get_cost_by_resource_group | Cost per resource group |
| suggest_optimisations | Savings recommendations with USD estimates |

---

## Evaluation

8 test cases measuring:
- Tool accuracy: did agent pick the right tool
- Keyword coverage: does answer mention expected terms
- Quality score: LLM as judge scores 0 to 10
- Latency: seconds per query

Results saved to data/eval_results.json

---

## Assignment Coverage

| Requirement | Implementation |
|------------|----------------|
| Data Preparation | 8 Azure cost knowledge markdown files |
| RAG Pipeline | ChromaDB plus Titan Embeddings V2 |
| Reasoning and Reflection | Self scoring loop with retry |
| Tool Calling | 4 tools with real Azure REST API |
| Evaluation | 8 test cases LLM as judge scoring |

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
if quality is too low. Part of the AI Academy Engineering Track.
AIAcademy DevOps FinOps AWS GenAI

---

## Acknowledgements

Final capstone project for the AI Academy Engineering Track.
