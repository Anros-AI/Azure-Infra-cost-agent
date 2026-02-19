# Azure Monitor and Log Analytics Cost Reduction

## Why Azure Monitor Is Expensive
Log Analytics charges per GB ingested. Large Kubernetes clusters
can generate hundreds of GB per day in container logs.

## Ways to Reduce Log Ingestion
- Filter noisy logs at source by excluding system namespaces
- Set a daily data cap in Log Analytics workspace settings
- Reduce retention period from 90 days to 30 days for debug logs
- Use Basic Logs tier for high volume infrequently queried tables
- Enable adaptive sampling for Application Insights

## Expected Savings
Optimised logging results in 30-50% reduction in Azure Monitor costs.
