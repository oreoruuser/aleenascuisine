# Audit Logging Verification

## Objective
Confirm that payment lifecycle events are captured with immutable traceability across order creation, Razorpay callbacks, and invoice fulfillment.

## Data Stores
- **Aurora orders.audit_log table** stores lifecycle transitions (`order_received`, `payment_authorized`, `invoice_queued`), including actor, source IP, and request ID.
- **CloudWatch Logs** for `${AppPrefix}-app` retain structured JSON logs for 90 days with `audit=true` annotations.
- **S3 Invoices Bucket** `${AppPrefix}-invoices` contains generated invoices tagged with `order_id`, `checksum`, and `created_at` metadata.

## Validation Steps
1. **Place Test Order**
   - Trigger the payment pipeline in sandbox using Razorpay test keys (`is_test=true`).
   - Capture the emitted `request_id` from API response headers.
2. **Inspect Aurora Audit Rows**
   - Run the stored procedure `CALL audit.get_events(:order_id)` via Data API; confirm three events with the same `request_id` and incrementing `version` fields.
3. **Cross-check Logs**
   - In CloudWatch Logs Insights, query:
     ```sql
     fields @timestamp, detail.event_name, request.request_id
     | filter request.request_id = '<captured-request-id>' and audit = true
     | sort @timestamp asc
     ```
   - Ensure entries mirror Aurora audit rows with consistent metadata.
4. **Verify Invoice Object**
   - List S3 object: `aws s3api list-objects --bucket ${AppPrefix}-invoices --query "Contents[?contains(Key, '<order-id>')].{Key:Key,Checksum:ChecksumAlgorithm}"`.
   - Confirm object metadata `audit-request-id` equals the captured identifier.
5. **Retention Policy Check**
   - Confirm CloudWatch log group `/aws/lambda/${AppPrefix}-app` retention is `90` days (set in `template.yaml`).
   - Ensure `AuroraAuditTrailPolicy` IAM statement includes `rds-data:ExecuteStatement` for `audit.*` procedures.

## Expected Outcome
- Every test order produces matching records in Aurora, CloudWatch, and S3 with consistent `request_id` and `actor` metadata.
- Missing entries indicate ingestion issues; escalate via `PHASE_B.md` observability runbook.
