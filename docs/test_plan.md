# Test Plan – Aleena's Cuisine Backend

## Overview
This plan enumerates functional, integration, end-to-end, security, and load scenarios required to exit Phase B. Each scenario records execution status (`PASS`/`FAIL`/`N/A`) plus notes.

| ID | Category | Scenario | Steps | Expected Result | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| UT-01 | Unit | Price calculation rules | Run `pytest backend/tests/test_cart_routes.py::test_cart_totals` | Totals computed per settings |  |  |
| UT-02 | Unit | Order idempotency logic | Run `pytest backend/tests/test_orders_routes.py::test_idempotent_order_creation` | Duplicate idempotency key returns existing order |  |  |
| UT-03 | Unit | Notification dispatch | Run `pytest backend/tests/test_payment_pipeline.py::test_notification_service_dispatches_multiple_channels` | SQS/SNS/WhatsApp stubs invoked once |  |  |
| IT-01 | Integration | Happy-path payment flow | a) Deploy to dev<br>b) Create cake, cart, order (`is_test=true`)<br>c) Trigger Razorpay capture webhook | Order status = `paid`, payment status = `captured`, invoice in S3 |  |  |
| IT-02 | Integration | Duplicate webhook delivery | Replay capture webhook payload twice | Second delivery returns `accepted=true`, no duplicate SQS jobs |  |  |
| IT-03 | Integration | Inventory guard | Attempt order with quantity exceeding stock | API returns `409 cart_price_mismatch` or `inventory_unavailable` |  |  |
| IT-04 | Integration | Razorpay failure path | Trigger `payment.failed` webhook | Order status `payment_failed`, notification emitted |  |  |
| IT-05 | Integration | Refund processing | Trigger `refund.processed` webhook | Order status `refunded`, notification emitted |  |  |
| E2E-01 | E2E | Customer checkout | Using frontend, add item -> checkout -> complete test payment | Customer sees order history entry with `paid` status |  |  |
| E2E-02 | E2E | Admin stock update | Admin creates cake with image, adjusts stock | Cake visible to customers with updated stock |  |  |
| E2E-03 | E2E | Invoice download link | Customer receives invoice link after payment | Link downloads generated PDF/JSON |  |  |
| SEC-01 | Security | Unauthenticated admin call | `curl /api/v1/admin/cakes` without `Authorization` | Response `401 unauthorized` |  |  |
| SEC-02 | Security | Invalid webhook signature | Send webhook with incorrect `X-Razorpay-Signature` | Response `400 invalid_signature`, metric `webhook_failures` increments |  |  |
| SEC-03 | Security | SQL injection attempt | Pass `' OR 1=1 --` in request fields | Input validation rejects / request fails with 400 |  |  |
| SEC-04 | Security | Secrets audit | Search logs for secret values post-deploy | No secrets leaked in CloudWatch |  |  |
| LOAD-01 | Load | 50 concurrent orders | Run `artillery run scripts/load/orders.yml` for 3 minutes | P95 < 1.5s, no Lambda throttles, Aurora ACU < threshold |  |  |
| OBS-01 | Observability | Request traceability | Execute representative API call | CloudWatch log entry with `request_id`, `duration_ms`, path |  |  |
| OBS-02 | Observability | X-Ray span coverage | View X-Ray service map post-flow | DB/external subsegments present |  |  |

### Tooling & Scripts
- **Unit tests**: `pytest backend/tests`
- **Integration harness**: `scripts/dev/integration.sh` (to be authored as needed)
- **Load test**: Example `scripts/load/orders.yml` (placeholder for Locust/Artillery configuration)

### Exit Criteria
- All unit and integration scenarios `PASS`
- At least three E2E scenarios validated
- Security and load tests executed with acceptable results
- Observability checks confirmed post-deploy
