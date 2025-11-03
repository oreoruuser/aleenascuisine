# Phase B Delivery Guide

## Environment & Configuration

| Variable | Description | Source |
| --- | --- | --- |
| `API_PREFIX` | Base path for all REST routes | SAM parameter `ApiVersion` (defaults to `/api/v1`) |
| `REGION` | AWS region | `samconfig.toml` (`ap-south-1`) |
| `ALEENA_ENV` | Deployment environment (`dev`/`prod`) | SAM parameter `Env` |
| `DATABASE_URL` | Aurora Data API connection string (derived automatically) | Secrets Manager `/${AppPrefix}/db` |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Razorpay credentials | Secrets Manager `/${AppPrefix}/razorpay` |
| `JWT_SECRET_ARN` | Cognito client secret / JWT signing material | Secrets Manager `/${AppPrefix}/jwt` |
| `WHATSAPP_SECRET_ARN` | WhatsApp Business token payload | Secrets Manager `/${AppPrefix}/whatsapp` |
| `POST_PAYMENT_QUEUE_URL` | SQS queue for invoice worker | Created by SAM (`${AppPrefix}-order-paid`) |
| `ADMIN_NOTIFICATIONS_TOPIC_ARN` | SNS topic for admin updates | Created by SAM (`${AppPrefix}-order-events`) |
| `LOG_LEVEL` | Application log verbosity | SAM parameter `LogLevel` (defaults to `INFO`) |

### Secrets & Keys

All secrets are stored in AWS Secrets Manager encrypted with the CMK provisioned in `template.yaml` (`KmsKey`). Do **not** copy secrets to `.env` files. To rotate credentials:

1. Update the value in Secrets Manager (`${AppPrefix}/razorpay`, `${AppPrefix}/db`, `${AppPrefix}/jwt`, `${AppPrefix}/whatsapp`).
2. Redeploy with `sam deploy --config-env <env>` or trigger Lambda environment refresh (console "Deploy new version").

## Deployment Playbooks

### Deploy to Production

1. **Snapshot DB**: `aws rds create-db-cluster-snapshot --db-cluster-identifier ${AppPrefix}-aurora --db-cluster-snapshot-identifier ${AppPrefix}-predeploy-$(date +%Y%m%d%H%M)`
2. **Run migrations**: `sam build && sam deploy --config-env prod`; apply Alembic migrations: `python backend/scripts/run_data_api_migration.py --env prod`.
3. **Functional smoke**:
   - `curl https://api.aleenascuisine.com/api/v1/health`
   - Create test order + payment using Razorpay test mode (`is_test=true`).
4. **Update routing**: flip DNS / API Gateway stage alias to new version once verification passes.

### Rollback Strategy

- Revert Lambda version via Lambda console > Versions > "Publish new version" selecting previous build.
- If schema changes break prod, restore DB snapshot: `aws rds restore-db-cluster-from-snapshot ...` and repoint secret / env variables.
- Redeploy SAM stack referencing previous artifact if necessary.

### Failed Webhook Investigation

1. Query `razorpay_events` table (persisted via `order_repo.record_webhook`).
2. Inspect CloudWatch logs (`/aws/lambda/${AppPrefix}-app`) filtered by `request_id` from Razorpay retry page.
3. Validate signature secret alignment; replay webhook via Razorpay test dashboard after confirming fix.

### Credential Rotation

1. Generate new Razorpay API key pair.
2. Update Secrets Manager entry `/${AppPrefix}/razorpay` with new values.
3. Redeploy Lambda (no code change required) so environment vars refresh.
4. Trigger webhook replay to confirm continuity.

## Observability Validation Checklist

- [ ] `curl /api/v1/health` -> `status=ok`, includes `request.request_id`.
- [ ] Execute test payment flow and ensure CloudWatch logs show JSON entries with request metadata.
- [ ] Confirm X-Ray service map contains `external.razorpay.*` and `db.*` subsegments.
- [ ] In CloudWatch Metrics namespace `AleenasCuisine/Application`, verify data points for:
  - `orders_created`
  - `order_processing_time`
  - `payments_success`
  - `webhook_failures`
- [ ] Ensure `WebhookFailureAlarm`, `FastApiLambdaErrorAlarm`, `AuroraCapacityAlarm` status is `OK`.
- [ ] Validate invoice object exists in `S3://${AppPrefix}-invoices/` for the test order.

## Operational Contacts & Escalation

- Primary On-call: `matkevin00@gmail.com`
- Slack channel: `#aleena-ops`
- Pager escalation: configure SNS subscription `OpsAlertsTopic` for future on-call rotation.

## Appendix: References

- SAM config: `infrastructure/samconfig.toml`
- Template: `infrastructure/template.yaml`
- OpenAPI definition: `backend/openapi.yaml`
- CloudWatch dashboard: `infrastructure/cloudwatch-dashboard.json`
- Test plan: `docs/test_plan.md`
- Postman collection: `docs/postman_collection.json`
- Audit verification: `docs/audit_logging_verification.md`
