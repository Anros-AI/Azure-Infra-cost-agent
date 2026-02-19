
import os
import json
import boto3

from agent.rag_retriever import RAGRetriever
from tools.azure_cost import (
    get_cost_by_service,
    get_daily_cost_trend,
    get_cost_by_resource_group,
    suggest_optimisations,
)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

TOOL_MAP = {
    "get_cost_by_service":        get_cost_by_service,
    "get_daily_cost_trend":       get_daily_cost_trend,
    "get_cost_by_resource_group": get_cost_by_resource_group,
    "suggest_optimisations":      suggest_optimisations,
}

TOOL_DESCRIPTIONS = """
Available tools - pick the ONE that best answers the user question:

1. get_cost_by_service()
   Use when: user asks which service costs most, cost breakdown, total spend.

2. get_daily_cost_trend()
   Use when: user asks about spikes, anomalies, daily burn rate, trends.

3. get_cost_by_resource_group()
   Use when: user asks about cost per team, environment, or resource group.

4. suggest_optimisations(cost_data)
   Use when: user asks how to reduce cost, save money, optimise spend.
   NOTE: You must call get_cost_by_service() FIRST and pass its result as cost_data.
"""


class AzureCostAgent:

    MAX_RETRIES = 2

    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        self.rag     = RAGRetriever()

    def _call_claude(self, prompt):
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens":        1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self.bedrock.invoke_model(
            modelId        = "anthropic.claude-3-haiku-20240307-v1:0",
            body           = json.dumps(body),
            contentType    = "application/json",
            accept         = "application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def run(self, query):
        print(f"\nQuery: {query}")
        print("=" * 50)

        kb_chunks = self.rag.retrieve(query, top_k=3)
        print(f"Retrieved {len(kb_chunks)} KB chunks")

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"\nReasoning attempt {attempt}...")

            plan       = self._reason(query, kb_chunks)
            print(f"Tool plan: {plan}")

            tool_output = self._execute_plan(plan)
            answer      = self._generate_answer(query, kb_chunks, plan, tool_output)
            print(f"\nDraft answer:\n{answer[:200]}...")

            reflection = self._reflect(query, answer)
            print(f"Reflection score: {reflection['score']}/10")
            print(f"Reflection reason: {reflection['reason']}")

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
            print("Score too low - retrying...")
        return {}

    def _reason(self, query, kb_chunks):
        kb_text = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in kb_chunks)
        prompt  = f"""You are an Azure FinOps expert AI agent.

User Question: {query}

Relevant Knowledge:
{kb_text}

Available Tools:
{TOOL_DESCRIPTIONS}

Decide which tool to call.
If question is about optimisation or saving money use TWO steps:
  primary_tool = get_cost_by_service
  secondary_tool = suggest_optimisations
Otherwise just set primary_tool and set secondary_tool to null.

Respond ONLY with valid JSON no markdown:
{{
  "primary_tool": "<tool_name>",
  "secondary_tool": "<tool_name or null>",
  "reasoning": "<one sentence why>"
}}"""
        raw = self._call_claude(prompt).strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {
                "primary_tool":   "get_cost_by_service",
                "secondary_tool": None,
                "reasoning":      raw[:200],
            }

    def _execute_plan(self, plan):
        primary_tool = plan.get("primary_tool")

        # If agent picks suggest_optimisations directly,
        # we must fetch cost data first automatically
        if primary_tool == "suggest_optimisations":
            cost_data     = get_cost_by_service()
            optimisations = suggest_optimisations(cost_data=cost_data)
            return {"cost_data": cost_data, "optimisations": optimisations}

        primary_fn  = TOOL_MAP.get(primary_tool, get_cost_by_service)
        primary_out = primary_fn()

        secondary = plan.get("secondary_tool")
        if secondary == "suggest_optimisations":
            secondary_out = suggest_optimisations(cost_data=primary_out)
            return {"cost_data": primary_out, "optimisations": secondary_out}

        return primary_out

    def _generate_answer(self, query, kb_chunks, plan, tool_output):
        kb_text = "\n\n".join(c["text"] for c in kb_chunks)
        prompt  = f"""You are an Azure FinOps assistant.
Answer the user question using the cost data and knowledge below.

User Question: {query}

Knowledge Base Context:
{kb_text}

Live Azure Cost Data:
{json.dumps(tool_output, indent=2)}

Guidelines:
- Start with the key number or finding
- Use bullet points for breakdowns
- For anomalies name the exact date and amount
- For optimisations show potential savings in USD
- Keep under 250 words
- If data source is mock mention demo data at the end"""
        return self._call_claude(prompt).strip()

    def _reflect(self, query, answer):
        prompt = f"""Rate this Azure cost analysis response.

Question: {query}

Answer: {answer}

Score on:
- Directly answers the question (3 pts)
- Includes specific dollar amounts (3 pts)
- Actionable recommendations (2 pts)
- Clear and concise (2 pts)

Respond ONLY with JSON no markdown:
{{"score": <0-10>, "reason": "<one sentence>", "should_retry": <true if score < 6 else false>}}"""
        raw = self._call_claude(prompt).strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"score": 7, "reason": "parse error", "should_retry": False}
