import boto3
import json
import os

def get_azure_credentials():
    secret_name = os.environ.get(
        "SECRETS_MANAGER_SECRET_NAME",
        "azure-cost-agent/azure-credentials"
    )
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    if os.environ.get("AZURE_SUBSCRIPTION_ID"):
        print("Using credentials from environment variables")
        return {
            "AZURE_SUBSCRIPTION_ID": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "AZURE_TENANT_ID":       os.environ.get("AZURE_TENANT_ID"),
            "AZURE_CLIENT_ID":       os.environ.get("AZURE_CLIENT_ID"),
            "AZURE_CLIENT_SECRET":   os.environ.get("AZURE_CLIENT_SECRET"),
        }

    try:
        print(f"Fetching credentials from Secrets Manager: {secret_name}")
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response["SecretString"])
        for key, value in secrets.items():
            os.environ[key] = value
            print(f"Loaded secret: {key}")
        return secrets
    except Exception as e:
        print(f"Could not fetch from Secrets Manager: {e}")
        print("Continuing with mock data")
        return {}
