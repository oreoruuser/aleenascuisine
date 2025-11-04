import { Link } from "react-router-dom";
import { useCart } from "../hooks/useCart";
import { formatCurrency } from "../utils/currency";
import { QuantitySelector } from "../components/QuantitySelector";

export const CartPage = () => {
  const { items, subtotal, totals, grandTotal, itemCount, updateQuantity, removeItem, clearCart, syncing } = useCart();

  if (!itemCount) {
    return (
      <main className="page">
        <h1>Your cart</h1>
        <p>Your cart is empty. Explore the menu to add items.</p>
        <Link to="/menu" className="button button--primary">
          Browse menu
        </Link>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="page__header">
        <div>
          <h1>Your cart</h1>
          <p>{itemCount} item{itemCount === 1 ? "" : "s"}</p>
        </div>
        <button type="button" className="button button--ghost" onClick={clearCart}>
          Clear cart
        </button>
      </header>

      <section className="cart-list">
        {items.map((item) => (
          <article key={item.id} className="cart-item">
            <div className="cart-item__info">
              <h3>{item.name}</h3>
              <p>{formatCurrency(item.price)}</p>
            </div>
            <div className="cart-item__actions">
              <QuantitySelector
                value={item.quantity}
                onChange={(quantity) => updateQuantity(item.id, quantity)}
                min={0}
                max={99}
              />
              <button type="button" className="button button--ghost" onClick={() => removeItem(item.id)}>
                Remove
              </button>
            </div>
          </article>
        ))}
      </section>

      <footer className="cart-summary">
        <div className="cart-summary__row">
          <span>Subtotal</span>
          <strong>{formatCurrency(totals?.subtotal ?? subtotal)}</strong>
        </div>
        {totals ? (
          <>
            <div className="cart-summary__row">
              <span>Taxes</span>
              <strong>{formatCurrency(totals.taxes)}</strong>
            </div>
            <div className="cart-summary__row">
              <span>Shipping</span>
              <strong>{formatCurrency(totals.shipping)}</strong>
            </div>
          </>
        ) : null}
        <div className="cart-summary__row cart-summary__total">
          <span>Total</span>
          <strong>{formatCurrency(totals?.total ?? grandTotal)}</strong>
        </div>
        <Link to="/checkout" className="button button--primary" aria-busy={syncing}>
          Proceed to checkout
        </Link>
      </footer>
    </main>
  );
};
