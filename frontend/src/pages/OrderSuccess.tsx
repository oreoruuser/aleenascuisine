import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { OrderDetail } from "../api/orders";
import { formatCurrency } from "../utils/currency";

interface LocationState {
  order?: OrderDetail;
  paymentId?: string;
}

export const OrderSuccessPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | undefined;
  const order = state?.order;

  useEffect(() => {
    if (!order) {
      navigate("/menu", { replace: true });
    }
  }, [navigate, order]);

  if (!order) {
    return null;
  }

  return (
    <main className="page">
      <h1>Payment successful</h1>
      <p>Your order is confirmed. We&apos;ll share delivery updates shortly.</p>
      <dl className="order-summary">
        <div>
          <dt>Order ID</dt>
          <dd>{order.orderId}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{order.status}</dd>
        </div>
        <div>
          <dt>Payment status</dt>
          <dd>{order.paymentStatus}</dd>
        </div>
        <div>
          <dt>Total paid</dt>
          <dd>{formatCurrency(order.totals.total)}</dd>
        </div>
        {state?.paymentId ? (
          <div>
            <dt>Payment reference</dt>
            <dd>{state.paymentId}</dd>
          </div>
        ) : null}
      </dl>
      <section className="order-items">
        <h2>Items</h2>
        <ul>
          {order.items.map((item) => (
            <li key={`${item.cartItemId}-${item.cakeId}`}>
              <span>
                {item.name ?? "Cake"} × {item.quantity}
              </span>
              <strong>{formatCurrency(item.lineTotal)}</strong>
            </li>
          ))}
        </ul>
      </section>
      <button
        type="button"
        className="button button--primary"
        onClick={() => navigate("/menu", { replace: true })}
      >
        Continue browsing
      </button>
    </main>
  );
};
