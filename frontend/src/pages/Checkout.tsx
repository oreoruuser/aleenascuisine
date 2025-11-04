import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useCart } from "../hooks/useCart";
import { createOrder, fetchOrder } from "../api/orders";
import { authConfig } from "../auth/config";
import { openRazorpayCheckout } from "../utils/razorpay";
import { formatCurrency } from "../utils/currency";

export const CheckoutPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cartId, items, totals, subtotal, grandTotal, itemCount, syncCart, clearCart } = useCart();
  const [address, setAddress] = useState("");
  const [contactPhone, setContactPhone] = useState(user?.phoneNumber || "");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!itemCount) {
      navigate("/cart", { replace: true });
    }
  }, [itemCount, navigate]);

  useEffect(() => {
    void syncCart({ customerId: user?.id });
  }, [syncCart, user?.id]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!address) {
      setError("Delivery address is required");
      return;
    }
    if (!contactPhone) {
      setError("Contact phone number is required");
      return;
    }

    try {
      setLoading(true);
      const snapshot = await syncCart({ customerId: user?.id });
      const effectiveCartId = snapshot?.cartId ?? cartId;

      if (!effectiveCartId) {
        throw new Error("Cart not ready. Please try again.");
      }

      const { order, providerOrderId } = await createOrder({
        cartId: effectiveCartId,
        customerId: user?.id,
        idempotencyKey: crypto.randomUUID(),
        isTest: authConfig.razorpayMode !== "live",
      });

      const amountPaise = Math.round((order.totals.total || 0) * 100);
      const instance = await openRazorpayCheckout({
        key: authConfig.razorpayKeyId,
        amount: amountPaise,
        currency: order.currency,
        name: "Aleena's Cuisine",
        description: `Order ${order.orderId}`,
        order_id: providerOrderId,
        notes: notes ? { notes } : undefined,
        prefill: {
          name: user?.name ?? undefined,
          email: user?.email ?? undefined,
          contact: contactPhone || undefined,
        },
        handler: async (response: {
          razorpay_payment_id: string;
          razorpay_order_id: string;
          razorpay_signature: string;
        }) => {
          try {
            const latestOrder = await fetchOrder(order.orderId);
            clearCart();
            navigate("/order-success", {
              replace: true,
              state: {
                order: latestOrder,
                paymentId: response.razorpay_payment_id,
              },
            });
          } catch (latestError) {
            const message =
              (latestError as { message?: string } | undefined)?.message ||
              "Payment captured, but we could not confirm the order. Please contact support.";
            setError(message);
          } finally {
            setLoading(false);
          }
        },
      });

      instance.on("payment.failed", (response) => {
        const failure = response as { error?: { description?: string } };
        const message =
          failure?.error?.description ||
          "Payment failed or was cancelled. Please try again.";
        setError(message);
        setLoading(false);
      });
    } catch (err) {
      const message = (err as { message?: string } | undefined)?.message || "Checkout failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (!itemCount) {
    return null;
  }

  return (
    <main className="page">
      <h1>Checkout</h1>

      <form className="checkout-form" onSubmit={handleSubmit}>
        <section>
          <h2>Delivery details</h2>
          <label>
            Address
            <textarea value={address} onChange={(event) => setAddress(event.target.value)} required />
          </label>
          <label>
            Contact phone
            <input value={contactPhone} onChange={(event) => setContactPhone(event.target.value)} required />
          </label>
          <label>
            Delivery notes (optional)
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
        </section>

        <aside className="checkout-summary">
          <h2>Order summary</h2>
          <ul>
            {items.map((item) => (
              <li key={item.id}>
                <span>
                  {item.name} × {item.quantity}
                </span>
                <span>{formatCurrency(item.price * item.quantity)}</span>
              </li>
            ))}
          </ul>
          {totals ? (
            <div className="checkout-breakdown">
              <div>
                <span>Subtotal</span>
                <strong>{formatCurrency(totals.subtotal)}</strong>
              </div>
              <div>
                <span>Taxes</span>
                <strong>{formatCurrency(totals.taxes)}</strong>
              </div>
              <div>
                <span>Shipping</span>
                <strong>{formatCurrency(totals.shipping)}</strong>
              </div>
            </div>
          ) : null}
          <div className="checkout-total">
            <span>Total</span>
            <strong>{formatCurrency(totals?.total ?? grandTotal)}</strong>
          </div>
          {error ? <p className="form-error">{error}</p> : null}
          <button type="submit" className="button button--primary" disabled={loading}>
            {loading ? "Processing..." : "Pay with Razorpay"}
          </button>
        </aside>
      </form>
    </main>
  );
};
