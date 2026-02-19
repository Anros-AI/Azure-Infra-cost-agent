# Azure SQL Database Cost Optimisation

## Pricing Models
- DTU model: Simple predictable load with bundled compute and storage
- vCore model: Flexible scaling with licensing benefit support
- Serverless model: Intermittent workloads with auto-pause when idle
- Elastic Pool: Multiple databases sharing resources for variable load

## Azure Hybrid Benefit for SQL
If you own SQL Server licenses with Software Assurance you can save up to 55%.
Enable this in the Azure portal under the SQL Database configuration.

## Serverless for Dev and Test Databases
Auto-pause triggers after a set inactivity period like 1 hour.
This reduces dev database costs by 60-80% compared to always-on pricing.

## Right Sizing
If average utilisation is below 40% downsize to the next lower tier.
Review Query Performance Insight to find actual usage patterns.
