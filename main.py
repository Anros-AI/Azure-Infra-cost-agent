
import argparse
import os
import sys

def check():
    if not os.environ.get("AWS_DEFAULT_REGION"):
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

def interactive():
    from agent.orchestrator import AzureCostAgent
    agent = AzureCostAgent()
    print("\n Azure Cost Analysis Agent")
    print("Type your question or type exit to quit\n")
    while True:
        try:
            q = input("Question > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit", ""):
            break
        r = agent.run(q)
        print("\n" + "="*50)
        print(r["answer"])
        print(f"\nScore: {r['reflection']['score']}/10 | Tool: {r['tool_called']}\n")

def single(query):
    from agent.orchestrator import AzureCostAgent
    r = AzureCostAgent().run(query)
    print("\n" + r["answer"])

def run_eval():
    from agent.orchestrator import AzureCostAgent
    from eval.evaluator import Evaluator
    agent = AzureCostAgent()
    Evaluator().run(agent.run)

if __name__ == "__main__":
    check()
    p = argparse.ArgumentParser()
    p.add_argument("--query", type=str)
    p.add_argument("--eval",  action="store_true")
    args = p.parse_args()

    if args.eval:
        run_eval()
    elif args.query:
        single(args.query)
    else:
        interactive()
