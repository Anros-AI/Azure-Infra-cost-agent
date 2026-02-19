import os
import json
import boto3
from agent.config import DEMO_MODE, AWS_REGION
from agent.rag_retriever import RAGRetriever
from agent.secrets_manager import get_azure_credentials
from agent.secure_logger import get_logger
from tools.azure_cost import (
    get_cost_by_service,
    get_daily_cost_trend,
    get_cost_by_resource_group,
    suggest_optimisations,
)

get_azure_credentials()
logger = get_logger("azure-cost-agent")

TOOL_MAP = {
    "get_cost_by_service":        get_cost_by_service,
    "get_daily_cost_trend":       get_daily_cost_trend,
    "get_cost_by_resource_group": get_cost_by_resource_group,
    "suggest_optimisations":      suggest_optimisations,
}

TOOL_DESCRIPTIONS = """
Available tools pick the ONE that best answers the user question:
1. get_cost_by_service() - Use when user asks which service costs most or total spend.
2. get_daily_cost_trend() - Use when user asks about spikes anomalies or trends.
3. get_cost_by_resource_group() - Use when user asks about cost per team or environment.
4. suggest_optimisations(cost_data) - Use when user asks how to reduce cost or save money.
"""


class AzureCostAgent:

    MAX_RETRIES = 2

    def __init__(self):
        self.use_mock = DEMO_MODE
        if not DEMO_MODE:
            try:
                self.bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
                print("Using Claude 3 Haiku on AWS Bedrock")
            except Exception as e:
                print(f"AWS connection failed: {e}")
                self.use_mock = True
                self.bedrock = None
        else:
            self.bedrock = None
            print("Demo mode active - using mock responses")
        self.rag = RAGRetriever()

    def _mock_response(self, prompt):
        p = prompt.lower()
        if "primary_tool" in p:
            if any(w in p for w in ["spike", "anomaly", "trend", "daily"]):
                return json.dumps({"primary_tool": "get_daily_cost_trend", "secondary_tool": None, "reasoning": "trend query"})
            elif "resource group" in p:
                return json.dumps({"primary_tool": "get_cost_by_resource_group", "secondary_tool": None, "reasoning": "resource group query"})
            elif any(w in p for w in ["reduc", "optim", "sav", "cheaper"]):
                return json.dumps({"primary_tool": "suggest_optimisations", "secondary_tool": None, "reasoning": "optimisation query"})
            else:
                return json.dumps({"primary_tool": "get_cost_by_service", "secondary_tool": None, "reasoning": "default breakdown"})
        elif any(w in p for w in ["score", "rate this", "evaluate"]):
            return json.dumps({"score": 8, "reason": "Good demo answer", "should_retry": False})
        elif any(w in p for w in ["spike", "anomaly", "unusual", "yesterday", "happened"]):
            return (
                "Cost Anomaly Analysis - Last 30 Days:\n\n"
                "2 anomaly days detected above threshold of $195.20:\n\n"
                "- 2026-01-27: $412.50 — 115% above daily average\n"
                "- 2026-02-10: $398.30 — 108% above daily average\n\n"
                "Daily average: $133.34\n\n"
                "Likely causes:\n"
                "- Autoscaling triggered without scale-down policy\n"
                "- Large data transfer or backup job on those days\n\n"
                "Recommendation: Set budget alerts at $200 per day.\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )
        elif any(w in p for w in ["resource group", "team", "environment", "project"]):
            return (
                "Cost by Resource Group - Last 30 Days:\n\n"
                "Total: $3,600.15\n\n"
                "- rg-production:    $2,180.40 (60.6%)\n"
                "- rg-staging:       $620.15   (17.2%)\n"
                "- rg-data-platform: $510.30   (14.2%)\n"
                "- rg-monitoring:    $175.60   (4.9%)\n"
                "- rg-dev:           $113.70   (3.2%)\n\n"
                "rg-production is 60% of total spend.\n"
                "Consider reviewing production resource sizing.\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )
        elif any(w in p for w in ["reduc", "optim", "sav", "cheaper", "cut"]):
            return (
                "Cost Optimisation Recommendations:\n\n"
                "Total potential savings: $979.07 (24.5% of $4,000.15)\n\n"
                "1. Virtual Machines - Switch to Reserved Instances\n"
                "   Current: $980.30 | Save: $294.09 (30%)\n\n"
                "2. AKS - Enable Spot node pools\n"
                "   Current: $1,420.50 | Save: $284.10 (20%)\n\n"
                "3. Azure SQL - Apply Azure Hybrid Benefit\n"
                "   Current: $650.75 | Save: $162.69 (25%)\n\n"
                "4. Blob Storage - Move to Cool or Archive tier\n"
                "   Current: $310.20 | Save: $124.08 (40%)\n\n"
                "5. Azure Monitor - Reduce log retention to 30 days\n"
                "   Current: $175.60 | Save: $52.68 (30%)\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )
        elif any(w in p for w in ["average", "daily", "trend", "per day"]):
            return (
                "Daily Cost Trend - Last 30 Days:\n\n"
                "Total: $4,000.15\n"
                "Daily average: $133.34\n"
                "Lowest day: $112.40\n"
                "Highest day: $412.50 (anomaly)\n\n"
                "Trend: Stable with 2 spike days detected.\n"
                "Costs are 15% higher on weekdays vs weekends.\n\n"
                "Recommendation: Schedule batch jobs on weekends.\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )
        elif any(w in p for w in ["reserved", "instance", "commit"]):
            return (
                "Reserved Instance Analysis:\n\n"
                "Current VM spend: $980.30 per month\n\n"
                "Savings with Reserved Instances:\n"
                "- 1-Year RI: Save 30-40% = $294 to $392 per month\n"
                "- 3-Year RI: Save 55-65% = $539 to $637 per month\n\n"
                "Recommendation: Yes switch to 1-Year Reserved Instances.\n"
                "Your VMs run 24/7 making RIs ideal.\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )
        else:
            return (
                "Azure Cost Breakdown - Last 30 Days:\n\n"
                "Total spend: $4,000.15\n\n"
                "- Azure Kubernetes Service: $1,420.50 (35.5%)\n"
                "- Virtual Machines:          $980.30  (24.5%)\n"
                "- Azure SQL Database:        $650.75  (16.3%)\n"
                "- Azure Blob Storage:        $310.20  (7.8%)\n"
                "- Azure Load Balancer:       $215.00  (5.4%)\n"
                "- Azure Monitor:             $175.60  (4.4%)\n"
                "- Azure App Service:         $145.90  (3.6%)\n"
                "- Other services:            $102.90  (2.6%)\n\n"
                "AKS is your biggest cost at 35.5% of total spend.\n\n"
                "Note: Demo data. Set DEMO_MODE=false for real analysis."
            )

    def _call_claude(self, prompt):
        if self.use_mock:
            return self._mock_response(prompt)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self.bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def run(self, query):
        logger.info(f"New query received: {query[:100]}")
        kb_chunks = self.rag.retrieve(query, top_k=3)
        logger.info(f"Retrieved {len(kb_chunks)} KB chunks")

        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info(f"Reasoning attempt {attempt} of {self.MAX_RETRIES}")
            plan = self._reason(query, kb_chunks)
            logger.info(f"Tool selected: {plan.get('primary_tool')}")
            tool_output = self._execute_plan(plan)
            answer = self._generate_answer(query, kb_chunks, plan, tool_output)
            logger.info(f"Answer generated: {len(answer)} characters")
            reflection = self._reflect(query, answer)
            logger.info(f"Reflection score: {reflection['score']}/10")

            if not reflection["should_retry"] or attempt == self.MAX_RETRIES:
                return {
                    "query":       query,
                    "tool_called": plan.get("primary_tool"),
                    "tool_output": tool_output,
                    "answer":      answer,
                    "kb_sources":  [c["source"] for c in kb_chunks],
                    "reflection":  reflection,
                    "attempts":    attempt,
                }
            logger.warning("Score below threshold - retrying")
        return {}

    def _reason(self, query, kb_chunks):
        kb_text = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in kb_chunks)
        prompt = (
            "You are an Azure FinOps expert AI agent.\n"
            f"User Question: {query}\n"
            f"Relevant Knowledge: {kb_text}\n"
            f"Available Tools: {TOOL_DESCRIPTIONS}\n"
            "Decide which tool to call.\n"
            "If question is about optimisation set primary_tool=get_cost_by_service and secondary_tool=suggest_optimisations.\n"
            "Otherwise set primary_tool only and secondary_tool to null.\n"
            'Respond ONLY with valid JSON no markdown: {"primary_tool": "<tool_name>", "secondary_tool": "<tool_name or null>", "reasoning": "<one sentence why>"}'
        )
        raw = self._call_claude(prompt).strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"primary_tool": "get_cost_by_service", "secondary_tool": None, "reasoning": raw[:200]}

    def _execute_plan(self, plan):
        primary_tool = plan.get("primary_tool")
        if primary_tool == "suggest_optimisations":
            cost_data = get_cost_by_service()
            return {"cost_data": cost_data, "optimisations": suggest_optimisations(cost_data=cost_data)}
        primary_fn  = TOOL_MAP.get(primary_tool, get_cost_by_service)
        primary_out = primary_fn()
        secondary   = plan.get("secondary_tool")
        if secondary == "suggest_optimisations":
            return {"cost_data": primary_out, "optimisations": suggest_optimisations(cost_data=primary_out)}
        return primary_out

    def _generate_answer(self, query, kb_chunks, plan, tool_output):
        if self.use_mock:
            return self._mock_response(query)
        kb_text = "\n\n".join(c["text"] for c in kb_chunks)
        prompt = (
            "You are an Azure FinOps assistant.\n"
            f"User Question: {query}\n"
            f"Knowledge: {kb_text}\n"
            f"Cost Data: {json.dumps(tool_output, indent=2)}\n"
            "Guidelines: Start with key number. Use bullet points. Show savings in USD. Keep under 250 words. Mention demo data if source is mock."
        )
        return self._call_claude(prompt).strip()

    def _reflect(self, query, answer):
        prompt = (
            "Rate this Azure cost analysis response 0-10.\n"
            f"Question: {query}\n"
            f"Answer: {answer}\n"
            "Score: answers question (3pts) + dollar amounts (3pts) + actionable (2pts) + clear (2pts).\n"
            'Respond ONLY with JSON: {"score": 0, "reason": "one sentence", "should_retry": false}'
        )
        raw = self._call_claude(prompt).strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"score": 7, "reason": "parse error", "should_retry": False}