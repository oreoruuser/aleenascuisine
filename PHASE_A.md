# Phase A Handover — Aleena's Cuisine

## Environment & Naming
- **Region**: ap-south-1 for all resources.
- **Stack prefixes**: `aleenascuisine-{env}` (`Env` parameter controls suffix via SAM).
- **Tag baseline**: `Project=aleenascuisine`, `Owner=kevinMathew`, `Env={dev|prod}`, `CostCenter=cseproj` attached in template globals.

### Key ARN Patterns (replace `${ACCOUNT_ID}` with your AWS account number)
- Lambda: `arn:aws:lambda:ap-south-1:${ACCOUNT_ID}:function:aleenascuisine-{env}-app`
- API Gateway: `arn:aws:apigateway:ap-south-1::/restapis/${ServerlessRestApi}/stages/{env}`
- KMS key: `arn:aws:kms:ap-south-1:${ACCOUNT_ID}:key/${KmsKeyId}` with alias above.
- Secrets: `arn:aws:secretsmanager:ap-south-1:${ACCOUNT_ID}:secret:aleenascuisine-{env}/db-xxxxx` and `.../razorpay-xxxxx`
- Aurora cluster: `arn:aws:rds:ap-south-1:${ACCOUNT_ID}:cluster:aleenascuisine-{env}-aurora`
- Images bucket: `arn:aws:s3:::aleenascuisine-{env}-images`, Invoices bucket: `arn:aws:s3:::aleenascuisine-{env}-invoices`

## Security & Secrets
- **CMK alias**: `alias/aleenascuisine-{env}-key` (`KmsKey` resource). Admin principal set via `KeyAdminArn` (default `arn:aws:iam::498192039865:user/kevin-mathew-admin`). Usage principals: `LambdaExecutionRoleArn` and `secretsmanager.amazonaws.com`.
- **Secrets Manager**:
  - `aleenascuisine-{env}/db` — cluster admin credentials (auto-generated, encrypted with CMK).
  - `aleenascuisine-{env}/razorpay` — Razorpay API keys placeholder, CMK-encrypted.
  - Access limited to the Lambda execution role supplied through `LambdaExecutionRoleArn`.

## Networking
- **VPC**: logical id `VPC`, /16 CIDR `10.0.0.0/16`.
- **Subnets**: public (`aleenascuisine-{env}-public-{a|b}`) and private (`aleenascuisine-{env}-private-{a|b}`) spread across AZs from `Fn::GetAZs`.
- **Route/NAT**: single NAT Gateway (beta cost profile) with dedicated route tables.
- **Endpoints**: Interface endpoints for Secrets Manager, RDS, RDS Data, CloudWatch Logs, plus an S3 gateway endpoint, all gated by `EndpointSecurityGroup` allowing inbound 443 only from the Lambda SG.

## Data Layer
- **Aurora Serverless v2**: cluster identifier `aleenascuisine-{env}-aurora`, `EnableHttpEndpoint=true` (Data API enabled). Scaling set to min 0.0 / max 2.0 ACUs per beta decision, retention 7 days, UTC parameter group, Enhanced Monitoring at 60s.
- **Backups**: automated retention, manual snapshot & restore documented below.
- **Monitoring**: CloudWatch dashboard widget on `ServerlessDatabaseCapacity` and alarm `aleenascuisine-{env}-Aurora-ACU-High` (threshold 1.5 ACUs).

## Storage & CDN
- **Buckets**:
  - `aleenascuisine-{env}-images` — public assets via CloudFront OAC (`CloudFrontDistribution`). Lifecycle transitions to Standard-IA (30 d) then Glacier (365 d).
  - `aleenascuisine-{env}-invoices` — private receipts, identical lifecycle policy, no public read.
- **Policies**: Public access block enabled. Bucket policy restricts GET to CloudFront distribution for images.

## Compute & API
- **Lambda**: function name `aleenascuisine-{env}-app`. Execution role supplied externally via `LambdaExecutionRoleArn` (defaults to `arn:aws:iam::498192039865:role/Executioner`) with least-privilege policies maintained outside template.
- **API Gateway**: `aleenascuisine-{env}-api` stage, CORS limited to `ApiAllowedOrigin` (default `http://localhost:3000`). Usage plan throttles at 20 RPS / 60 burst with 100k monthly quota; access logs and X-Ray tracing enabled. `/health` is provided by FastAPI and covered by stage.

## Observability & Cost Controls
- **CloudWatch log groups**: `/aws/lambda/aleenascuisine-{env}-app`, `/aws/api-gateway/aleenascuisine-{env}-api`.
- **Metric filters & alarms**: ERROR/WARNING filters for Lambda logs, alarms for Lambda errors, API 5xx, Aurora ACU, Secrets Manager failures. SNS topic `aleenascuisine-{env}-alarms` emails `matkevin00@gmail.com`.
- **AWS Budgets**: `aleenascuisine-{env}-{Env}-monthly-budget` with ACTUAL spend alerts at 50/80/100% sending to the same email. Dev budget defaults to USD 30 (override `MonthlyBudgetAmount` per env).

## Database Schema & Migrations
- Alembic migration `202511020001_initial_schema.py` creates: `customers`, `cakes`, `inventory`, `orders`, `order_items`, `payments`, `audit_log`. Uses UUID public IDs, DECIMAL(10,2) money fields, UTC timestamps, soft-delete columns, FK constraints, composite indexes, sample seed data.
- Migrations run via `alembic` using Secrets Manager credentials (`DB_SECRET_ARN`, `DB_HOST`, `DB_NAME`).

## Runbook Highlights
1. **Logs & Metrics**
   - Lambda/API logs in CloudWatch log groups above; filter by requestId or ERROR keywords.
   - Dashboard `aleenascuisine-{env}-Dashboard` visualizes Lambda, API, Aurora ACU.
   - X-Ray enabled by default; view service map for latency/cold starts.
2. **Secret Rotation**
   - Rotate DB credentials in Secrets Manager; update Aurora master password automatically via rotation or manual change and ensure Lambda alias uses the same secret ARN.
   - Razorpay secret rotation is manual for now; post-update run integration test through `/payments/create`.
3. **Restore from Snapshot**
   - Take point-in-time snapshot (Aurora console or `rds:CreateDBClusterSnapshot`).
   - Restore to new cluster, update secret with restored endpoint, run smoke tests, then swap endpoints or update Lambda env (`DB_HOST`).
4. **Budget Follow-up**
   - Respond to budget alerts by inspecting Cost Explorer (filtered by tag `Project=aleenascuisine`). Scale down Aurora max ACU or disable non-essential endpoints in dev if costs spike.
5. **Troubleshooting**
   - For API 5xx, correlate CloudWatch alarm with Lambda logs and X-Ray traces.
   - Secrets Manager alarm indicates denied decrypt/get; verify IAM policy on `LambdaExecutionRoleArn` includes the specific secret ARNs.
   - Inventory/order data issues: rerun Alembic migrations or seed using Data API (ensure `rds-data:ExecuteStatement` permissions present).

## Outstanding Notes
- Production CORS origin should override `ApiAllowedOrigin` in `samconfig.toml` (currently placeholder `https://app.aleenascuisine.com`).
- Lambda execution role (`Executioner`) must continue to enforce least privilege (Secrets Manager / RDS Data / S3 scoped to aleenascuisine resources only, CloudWatch logs, KMS decrypt).
- Aurora scaling intentionally capped at 0.0–2.0 ACUs for beta; revisit before GA.
