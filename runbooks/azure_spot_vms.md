# Azure Spot VMs and Preemptible Workloads

## What Are Spot VMs
Spot VMs use Azure unused compute capacity at 60-90% discount.
Azure can evict them with 30-second notice when capacity is needed.

## Ideal Workloads
- Batch processing jobs
- CI/CD build agents
- Dev and test environments
- AKS non-production node pools
- Data processing pipelines

## Expected Savings
- AKS workloads: 60-80% on spot nodes vs regular nodes
- Best combined with cluster autoscaler for maximum savings
