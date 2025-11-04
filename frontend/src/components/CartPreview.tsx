import { Link } from "react-router-dom";
import { useCart } from "../hooks/useCart";
import { formatCurrency } from "../utils/currency";

export const CartPreview = () => {
  const { itemCount, subtotal, totals, grandTotal } = useCart();

  if (!itemCount) {
    return null;
  }

  const amount = totals?.total ?? grandTotal ?? subtotal;

  return (
    <div className="cart-preview">
      <p>
        {itemCount} item{itemCount === 1 ? "" : "s"} • {formatCurrency(amount)}
      </p>
      <Link to="/cart" className="button button--primary">
        View cart
      </Link>
    </div>
  );
};
