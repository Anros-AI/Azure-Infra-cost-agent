
import os
import json
import time
import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

TEST_CASES = [
    {
        "id": "TC-01",
        "category": "breakdown",
        "query": "Which Azure service cost the most last month?",
        "expected_tool": "get_cost_by_service",
        "expected_keywords": ["AKS", "Kubernetes", "cost", "USD"],
    },
    {
        "id": "TC-02",
        "category": "anomaly",
        "query": "Were there any cost spikes in the last 30 days?",
        "expected_tool": "get_daily_cost_trend",
        "expected_keywords": ["spike", "anomaly", "USD", "date"],
    },
    {
        "id": "TC-03",
        "category": "optimisation",
        "query": "How can I reduce my Azure infrastructure costs?",
        "expected_tool": "suggest_optimisations",
        "expected_keywords": ["saving", "Reserved", "Spot", "USD"],
    },
    {
        "id": "TC-04",
        "category": "breakdown",
        "query": "Break down Azure costs by resource group.",
        "expected_tool": "get_cost_by_resource_group",
        "expected_keywords": ["rg-", "production", "USD"],
    },
    {
        "id": "TC-05",
        "category": "trend",
        "query": "What is my daily average Azure spend?",
        "expected_tool": "get_daily_cost_trend",
        "expected_keywords": ["daily", "average", "USD"],
    },
    {
        "id": "TC-06",
        "category": "optimisation",
        "query": "Should I switch to Reserved Instances for my VMs?",
        "expected_tool": "get_cost_by_service",
        "expected_keywords": ["Reserved", "VM", "saving", "USD"],
    },
    {
        "id": "TC-07",
        "category": "breakdown",
        "query": "What is my total Azure spend this month?",
        "expected_tool": "get_cost_by_service",
        "expected_keywords": ["total", "USD", "month"],
    },
    {
        "id": "TC-08",
        "category": "anomaly",
        "query": "Which day had the highest Azure bill last month?",
        "expected_tool": "get_daily_cost_trend",
        "expected_keywords": ["highest", "day", "USD"],
    },
]


class Evaluator:

    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=REGION)

    def _call_claude(self, prompt):
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self.bedrock.invoke_model(
            modelId     = "anthropic.claude-3-haiku-20240307-v1:0",
            body        = json.dumps(body),
            contentType = "application/json",
            accept      = "application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _judge_quality(self, query, answer):
        prompt = f"""Rate this Azure cost analysis answer from 0 to 10.
Question: {query}
Answer: {answer}
Criteria: answers question (3pts), has dollar amounts (3pts), actionable (2pts), clear (2pts).
Respond ONLY with JSON no markdown: {{"score":<0-10>,"reason":"<one sentence>"}}"""
        raw = self._call_claude(prompt).strip()
        raw = raw.replace("```json","").replace("```","").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"score": 5, "reason": "parse error"}

    def run(self, agent_fn):
        print("\n" + "="*50)
        print("EVALUATION — 8 Azure Cost Queries")
        print("="*50)

        results = []
        for tc in TEST_CASES:
            print(f"\nRunning {tc['id']} [{tc['category']}]")
            print(f"Query: {tc['query'][:55]}...")
            t0 = time.time()
            try:
                out     = agent_fn(tc["query"])
                latency = round(time.time() - t0, 2)
                answer  = out.get("answer", "")
                tool    = out.get("tool_called", "")

                tool_correct = tool == tc["expected_tool"]
                kw_hits      = sum(1 for kw in tc["expected_keywords"] if kw.lower() in answer.lower())
                quality      = self._judge_quality(tc["query"], answer)
                refl_score   = out.get("reflection", {}).get("score", 0)

                passed = (
                    tool_correct
                    and kw_hits / len(tc["expected_keywords"]) >= 0.4
                    and quality["score"] >= 6
                )

                results.append({
                    "id":            tc["id"],
                    "category":      tc["category"],
                    "tool_correct":  tool_correct,
                    "kw_hits":       kw_hits,
                    "kw_total":      len(tc["expected_keywords"]),
                    "quality_score": quality["score"],
                    "quality_reason":quality["reason"],
                    "refl_score":    refl_score,
                    "latency":       latency,
                    "passed":        passed,
                })

                status = "PASS" if passed else "FAIL"
                print(f"   {status} | tool={tool_correct} | kw={kw_hits}/{len(tc['expected_keywords'])} | quality={quality['score']}/10 | {latency}s")

            except Exception as e:
                print(f"   ERROR: {e}")
                results.append({
                    "id": tc["id"], "category": tc["category"],
                    "tool_correct": False, "kw_hits": 0,
                    "kw_total": len(tc["expected_keywords"]),
                    "quality_score": 0, "quality_reason": str(e),
                    "refl_score": 0, "latency": 0, "passed": False,
                })

        total  = len(results)
        passed = sum(1 for r in results if r["passed"])
        summary = {
            "total":             total,
            "passed":            passed,
            "failed":            total - passed,
            "pass_rate_pct":     round(passed / total * 100, 1),
            "tool_accuracy_pct": round(sum(r["tool_correct"] for r in results) / total * 100, 1),
            "avg_quality":       round(sum(r["quality_score"] for r in results) / total, 1),
            "avg_latency_sec":   round(sum(r["latency"] for r in results) / total, 1),
            "results":           results,
        }

        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        print(f"Pass rate      : {passed}/{total} ({summary['pass_rate_pct']}%)")
        print(f"Tool accuracy  : {summary['tool_accuracy_pct']}%")
        print(f"Avg quality    : {summary['avg_quality']}/10")
        print(f"Avg latency    : {summary['avg_latency_sec']}s")

        os.makedirs("data", exist_ok=True)
        with open("data/eval_results.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("\nSaved results to data/eval_results.json")
        return summary
