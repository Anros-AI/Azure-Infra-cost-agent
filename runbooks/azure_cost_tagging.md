# Azure Cost Tagging Strategy for DevOps Teams

## Why Tagging Matters
Without tags Azure Cost Management shows costs by resource or service
but cannot answer how much a specific team or project spent last month.

## Recommended Tag Schema
- Environment tag: prod, staging, dev, test
- Team tag: platform, data, frontend, backend
- Project tag: payments-api, ml-pipeline, data-warehouse
- CostCenter tag: CC-1234 for finance chargeback
- Owner tag: engineer email address for accountability

## Enforce Tags via Azure Policy
Create a deny policy that blocks resource creation without required tags.
This ensures all new resources are tagged from day one.

## View Costs by Tag
Azure Portal go to Cost Management then Cost Analysis
then Group By then select Tag then choose Environment or Team.
Export to CSV for monthly chargeback reports to each team.
