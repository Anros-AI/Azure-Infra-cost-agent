
import os, json, datetime, requests
from typing import Optional

def _get_token():
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    if not all([tenant_id, client_id, client_secret]):
        return None
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://management.azure.com/.default",
    }
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_cost_by_service(subscription_id=None):
    sub_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    token = _get_token()
    if token and sub_id:
        today = datetime.date.today()
        from_date = (today - datetime.timedelta(days=30)).isoformat()
        to_date = today.isoformat()
        url = f"https://management.azure.com/subscriptions/{sub_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": from_date, "to": to_date},
            "dataset": {
                "granularity": "None",
                "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        resp = requests.post(url, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        raw = resp.json()
        columns = [c["name"] for c in raw["properties"]["columns"]]
        services = []
        for row in raw["properties"]["rows"]:
            record = dict(zip(columns, row))
            services.append({"service": record.get("ServiceName", "Unknown"), "cost_usd": round(float(record.get("Cost", 0)), 2)})
        services.sort(key=lambda x: x["cost_usd"], reverse=True)
        return {"source": "azure_api", "period": f"{from_date} to {to_date}", "total_usd": round(sum(s["cost_usd"] for s in services), 2), "services": services[:15]}
    return _mock_cost_by_service()

def _mock_cost_by_service():
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=30)).isoformat()
    services = [
        {"service": "Azure Kubernetes Service", "cost_usd": 1420.50},
        {"service": "Virtual Machines", "cost_usd": 980.30},
        {"service": "Azure SQL Database", "cost_usd": 650.75},
        {"service": "Azure Blob Storage", "cost_usd": 310.20},
        {"service": "Azure Load Balancer", "cost_usd": 215.00},
        {"service": "Azure Monitor", "cost_usd": 175.60},
        {"service": "Azure App Service", "cost_usd": 145.90},
        {"service": "Azure Key Vault", "cost_usd": 42.30},
        {"service": "Azure Container Registry", "cost_usd": 38.10},
        {"service": "Azure Virtual Network", "cost_usd": 21.50},
    ]
    return {"source": "mock", "period": f"{from_date} to {today.isoformat()}", "total_usd": round(sum(s["cost_usd"] for s in services), 2), "services": services}

def get_daily_cost_trend(subscription_id=None):
    sub_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    token = _get_token()
    if token and sub_id:
        today = datetime.date.today()
        from_date = (today - datetime.timedelta(days=30)).isoformat()
        to_date = today.isoformat()
        url = f"https://management.azure.com/subscriptions/{sub_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": from_date, "to": to_date},
            "dataset": {"granularity": "Daily", "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}}},
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        resp = requests.post(url, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        raw = resp.json()
        cols = [c["name"] for c in raw["properties"]["columns"]]
        daily = []
        for row in raw["properties"]["rows"]:
            rec = dict(zip(cols, row))
            daily.append({"date": str(rec.get("UsageDate", ""))[:10], "cost_usd": round(float(rec.get("Cost", 0)), 2)})
    else:
        daily = _mock_daily_trend()
    return _annotate_anomalies(daily)

def _mock_daily_trend():
    import random, math
    random.seed(42)
    today = datetime.date.today()
    daily = []
    for i in range(30):
        day = today - datetime.timedelta(days=29 - i)
        base = 130 + 20 * math.sin(i / 7)
        spike = 280 if i in (7, 21) else 0
        cost = round(base + random.uniform(-10, 10) + spike, 2)
        daily.append({"date": day.isoformat(), "cost_usd": cost})
    return daily

def _annotate_anomalies(daily):
    costs = [d["cost_usd"] for d in daily]
    mean = sum(costs) / len(costs)
    variance = sum((c - mean) ** 2 for c in costs) / len(costs)
    std = variance ** 0.5
    threshold = mean + 1.5 * std
    anomalies = []
    for d in daily:
        d["anomaly"] = d["cost_usd"] > threshold
        if d["anomaly"]:
            anomalies.append(d)
    return {"source": "azure_api" if _get_token() else "mock", "daily": daily, "mean_daily_usd": round(mean, 2), "std_dev_usd": round(std, 2), "anomaly_threshold_usd": round(threshold, 2), "anomaly_days": anomalies, "total_usd": round(sum(costs), 2)}

def get_cost_by_resource_group(subscription_id=None):
    sub_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    token = _get_token()
    if token and sub_id:
        today = datetime.date.today()
        from_date = (today - datetime.timedelta(days=30)).isoformat()
        to_date = today.isoformat()
        url = f"https://management.azure.com/subscriptions/{sub_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": from_date, "to": to_date},
            "dataset": {"granularity": "None", "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}}, "grouping": [{"type": "Dimension", "name": "ResourceGroupName"}]},
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        resp = requests.post(url, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        raw = resp.json()
        cols = [c["name"] for c in raw["properties"]["columns"]]
        groups = []
        for row in raw["properties"]["rows"]:
            rec = dict(zip(cols, row))
            groups.append({"resource_group": rec.get("ResourceGroupName", "Unknown"), "cost_usd": round(float(rec.get("Cost", 0)), 2)})
        groups.sort(key=lambda x: x["cost_usd"], reverse=True)
        return {"source": "azure_api", "period": f"{from_date} to {to_date}", "resource_groups": groups, "total_usd": round(sum(g["cost_usd"] for g in groups), 2)}
    today = datetime.date.today()
    groups = [
        {"resource_group": "rg-production", "cost_usd": 2180.40},
        {"resource_group": "rg-staging", "cost_usd": 620.15},
        {"resource_group": "rg-data-platform", "cost_usd": 510.30},
        {"resource_group": "rg-monitoring", "cost_usd": 175.60},
        {"resource_group": "rg-dev", "cost_usd": 113.70},
    ]
    return {"source": "mock", "period": f"{(today - datetime.timedelta(days=30)).isoformat()} to {today.isoformat()}", "resource_groups": groups, "total_usd": round(sum(g["cost_usd"] for g in groups), 2)}

def suggest_optimisations(cost_data):
    services = {s["service"]: s["cost_usd"] for s in cost_data.get("services", [])}
    total = cost_data.get("total_usd", 0)
    tips = []
    potential = 0.0
    rules = [
        ("Virtual Machines", 0.30, "Switch to Reserved Instances 1-year for stable VMs saves 30-40%"),
        ("Azure Kubernetes Service", 0.20, "Enable Cluster Autoscaler and use Spot node pools saves 60-80%"),
        ("Azure SQL Database", 0.25, "Use Azure Hybrid Benefit if you have SQL Server licenses saves 25%"),
        ("Azure Blob Storage", 0.40, "Move infrequently accessed blobs to Cool or Archive tier saves 40-70%"),
        ("Azure Monitor", 0.30, "Reduce log retention and filter noisy logs at source saves 20-40%"),
        ("Azure App Service", 0.20, "Consolidate to fewer App Service Plans or use consumption based Functions"),
        ("Azure Load Balancer", 0.15, "Review unused load balancer rules and remove unused ones"),
    ]
    for service, saving_pct, tip in rules:
        if service in services and services[service] > 50:
            saving = round(services[service] * saving_pct, 2)
            tips.append({"service": service, "current_cost": services[service], "tip": tip, "est_saving_usd": saving})
            potential += saving
    tips.sort(key=lambda x: x["est_saving_usd"], reverse=True)
    return {"total_spend_usd": total, "potential_savings_usd": round(potential, 2), "savings_pct_of_total": round(potential / total * 100, 1) if total else 0, "recommendations": tips}
