# Detecting and Responding to Azure Cost Anomalies

## What Causes Cost Spikes
- Runaway autoscaling with missing scale-down policy
- Data egress surge from large file transfers or DDoS
- Accidental deployment of large SKU VMs
- Forgotten dev and test resources left running overnight
- Storage snapshot accumulation over time

## How to Detect Anomalies
- Compare daily spend to rolling 7-day average
- Alert when daily cost exceeds mean plus 2 standard deviations
- Use Azure Cost Management built-in anomaly detection

## Responding to a Spike
1. Go to Cost Analysis and filter by the spike date
2. Group by Resource to find the culprit resource
3. Group by Meter to identify exact usage type
4. Check Activity Log for deployments made that day
5. Set budget alerts to get notified before next spike
