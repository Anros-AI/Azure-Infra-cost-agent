import os

# Set DEMO_MODE=true to run without any credentials
# Perfect for committee review and demonstrations
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

if DEMO_MODE:
    print("=" * 50)
    print("DEMO MODE ACTIVE")
    print("Running with mock data - no credentials needed")
    print("Set DEMO_MODE=false to use real AWS and Azure")
    print("=" * 50)
else:
    print("LIVE MODE - Using real AWS Bedrock and Azure API")
