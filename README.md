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

---

## Agentic AI Components

This project implements all core components of a modern AI Agent system.

### 1. Data Preparation and Contextualization
The agent uses 8 domain specific Azure cost knowledge documents
covering Reserved Instances, Spot VMs, Storage tiers, AKS costs,
SQL costs, anomaly detection, monitoring costs, and tagging strategy.
These documents are the grounding knowledge that makes the agent
an expert in Azure FinOps rather than giving generic answers.

### 2. RAG Pipeline — Retrieval Augmented Generation
When a user asks a question the agent does not just send it to the LLM.
It first searches the knowledge base for the most relevant sections
and includes them as context. This grounds the answer in real knowledge.

How it works:
- Documents are chunked into 500 character pieces with 100 character overlap
- Each chunk is converted to a vector using Amazon Titan Embeddings V2
- Vectors are stored in ChromaDB a local persistent vector database
- At query time the question is also converted to a vector
- ChromaDB finds the top 3 most semantically similar chunks
- Those chunks are sent to Claude along with the question

Why this matters:
Without RAG Claude gives generic answers from training data.
With RAG Claude gives specific answers grounded in your knowledge base.

### 3. Autonomous Reasoning
The agent reasons about which tool to call based on the question
and the retrieved knowledge. It does not use hardcoded if-else logic.
Claude reads the question, reads the KB context, reads the available
tools, and decides the best approach. For optimisation questions it
automatically chains two tools together without being told to.

Example reasoning:
- User asks about cost spikes -> agent picks get_daily_cost_trend
- User asks about savings -> agent picks get_cost_by_service first
  then chains suggest_optimisations automatically

### 4. Tool Calling Mechanisms
The agent has 4 tools it can call to take real actions:

get_cost_by_service
  Calls Azure Cost Management REST API and returns total spend
  per service for the last 30 days grouped and sorted by cost.

get_daily_cost_trend
  Fetches daily cost for 30 days and runs statistical anomaly
  detection using mean plus 1.5 standard deviations threshold
  to flag unusual spending days automatically.

get_cost_by_resource_group
  Returns cost broken down by resource group so teams can see
  exactly how much each environment or project is spending.

suggest_optimisations
  Rule based analysis that takes live cost data as input and
  returns specific saving recommendations with estimated USD
  amounts for each service based on Azure best practices.

### 5. Self Reflection and Self Correction
After generating every answer the agent evaluates its own output.
It scores the answer from 0 to 10 based on four criteria:
- Does it directly answer the question (3 points)
- Does it include specific dollar amounts (3 points)
- Are the recommendations actionable (2 points)
- Is it clear and concise (2 points)

If the score is below 6 the agent automatically retries with
refined reasoning up to 2 times. This self correction loop
ensures consistently high quality answers without human intervention.

Current evaluation results:
- Pass rate: 87.5 percent (7 out of 8 test cases)
- Average quality score: 9.2 out of 10
- Tool selection accuracy: 87.5 percent

### 6. Evaluation Framework
The agent includes a formal evaluation suite with 8 test cases
covering all major capabilities. Each test case measures three
independent dimensions to ensure the agent is truly working:

Tool accuracy: Did the agent pick the correct tool for the question
Keyword coverage: Does the answer mention expected domain terms
Quality score: An LLM judge independently scores the answer 0 to 10

All three must pass for a test case to be considered successful.
Results are saved to data/eval_results.json for review.

### 7. Security
The agent implements production grade security practices:

AWS Secrets Manager integration to store Azure credentials
securely with encryption at rest and full audit trail instead
of plain text environment variables.

Secure logging that automatically masks sensitive values like
API keys, tokens, and secrets before they appear in any logs.

Non-root Docker user so the container process runs with minimal
privileges reducing the blast radius of any security incident.

---

## Architecture
```
User Question
      |
      v
Agent Orchestrator (Claude 3 Haiku on AWS Bedrock)
      |
      |--- 1. RAG Retrieve --- ChromaDB --- 8 KB docs
      |
      |--- 2. Reason --- Claude decides which tool to call
      |
      |--- 3. Act --- Execute tool --- Azure Cost API
      |
      |--- 4. Generate Answer --- Combine data and KB
      |
      |--- 5. Self Reflect --- Score 0-10 --- Retry if below 6
```

See architecture.mmd for the full diagram.

---

## Tech Stack

- LLM: Claude 3 Haiku on AWS Bedrock
- Embeddings: Amazon Titan Embeddings V2
- Vector Store: ChromaDB local persistent
- Cost Data: Azure Cost Management REST API
- UI: Streamlit
- Container: Docker
- Security: AWS Secrets Manager plus secure logging
- Evaluation: LLM as judge plus keyword matching

---

## Project Structure

- agent/orchestrator.py — Main agentic loop with 5 step reasoning
- agent/rag_retriever.py — ChromaDB and Titan Embeddings RAG pipeline
- agent/secrets_manager.py — AWS Secrets Manager integration
- agent/secure_logger.py — Secure logging with sensitive data masking
- tools/azure_cost.py — 4 Azure Cost Management tools
- eval/evaluator.py — 8 test cases with LLM as judge scoring
- runbooks/ — 8 Azure cost knowledge base markdown docs
- app.py — Streamlit web UI
- main.py — CLI entry point
- generate_kb.py — Creates knowledge base files
- Dockerfile — Container definition with security hardening
- architecture.mmd — System diagram

---

## Option 1 - Run with Docker (Recommended)

Build the image:

    docker build -t azure-cost-agent .

Run with environment variables:

    docker run -p 8501:8501
      -e AWS_DEFAULT_REGION=us-east-1
      -e AWS_ACCESS_KEY_ID=your-access-key
      -e AWS_SECRET_ACCESS_KEY=your-secret-key
      -e AZURE_SUBSCRIPTION_ID=your-subscription-id
      -e AZURE_TENANT_ID=your-tenant-id
      -e AZURE_CLIENT_ID=your-client-id
      -e AZURE_CLIENT_SECRET=your-client-secret
      azure-cost-agent

Run with AWS Secrets Manager (recommended for production):

    docker run -p 8501:8501
      -e AWS_DEFAULT_REGION=us-east-1
      -e AWS_ACCESS_KEY_ID=your-access-key
      -e AWS_SECRET_ACCESS_KEY=your-secret-key
      -e SECRETS_MANAGER_SECRET_NAME=azure-cost-agent/azure-credentials
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

- Pass Rate: 87.5 percent (7 out of 8 test cases)
- Tool Accuracy: 87.5 percent
- Average Quality: 9.2 out of 10
- Average Latency: 7.6 seconds

---

## Assignment Coverage

- Data Preparation: 8 Azure cost knowledge markdown files
- RAG Pipeline: ChromaDB plus Titan Embeddings V2
- Reasoning and Reflection: Self scoring loop with retry up to 2 times
- Tool Calling: 4 tools calling real Azure Cost Management REST API
- Evaluation: 8 test cases with tool accuracy keyword and LLM judge scoring

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
on AWS Bedrock with Docker containerization and AWS Secrets Manager
for production grade security. The agent detects cost anomalies,
suggests specific savings with dollar estimates, and self reflects
on every answer retrying if quality is too low.
Part of the AI Academy Engineering Track.
AIAcademy DevOps FinOps AWS GenAI Docker

---

## Acknowledgements

Final capstone project for the AI Academy Engineering Track.
