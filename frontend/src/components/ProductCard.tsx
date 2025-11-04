import { useState } from "react";
import { useCart } from "../hooks/useCart";
import type { CakeSummary } from "../api/orders";
import { QuantitySelector } from "./QuantitySelector";
import { formatCurrency } from "../utils/currency";

export const ProductCard = ({ item }: { item: CakeSummary & { description?: string; imageUrl?: string } }) => {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useCart();

  const handleAdd = () => {
    addItem({
      id: item.id,
      name: item.name,
      price: item.price,
      quantity,
      imageUrl: item.imageUrl,
    });
    setQuantity(1);
  };

  return (
    <article className="product-card">
      {item.imageUrl ? <img src={item.imageUrl} alt={item.name} loading="lazy" /> : null}
      <div className="product-card__content">
        <header>
          <h3>{item.name}</h3>
          {item.description ? <p>{item.description}</p> : null}
        </header>
        <footer>
          <strong>{formatCurrency(item.price)}</strong>
          <div className="product-card__actions">
            <QuantitySelector value={quantity} onChange={setQuantity} min={1} max={99} />
            <button type="button" className="button button--primary" onClick={handleAdd}>
              Add to cart
            </button>
          </div>
        </footer>
      </div>
    </article>
  );
};
