# Azure Kubernetes Service AKS Cost Optimisation

## AKS Billing Components
- Node VMs are largest cost typically 60-70% of total AKS spend
- Load Balancers charged per rule and data processed
- Persistent Volumes on Azure Disks or Azure Files
- Egress bandwidth charges

## Key Optimisations
- Enable Cluster Autoscaler to automatically scale down idle nodes saving 20-40%
- Use Spot node pools for batch and non-critical workloads saving 60-80%
- Set proper resource requests and limits to avoid node over-provisioning
- Scale dev clusters to zero nodes outside working hours
- Use B-series burstable VMs for low-traffic services

## Cluster Autoscaler Command
az aks update --enable-cluster-autoscaler --min-count 1 --max-count 10
