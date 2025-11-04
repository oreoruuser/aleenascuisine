import { useState } from "react";
import { useCart } from "../hooks/useCart";
import type { CakeSummary } from "../api/orders";
import { QuantitySelector } from "./QuantitySelector";
import { formatCurrency } from "../utils/currency";

type ProductCardProps = {
  item: CakeSummary & {
    description?: string;
    imageUrl?: string;
  };
};

export const ProductCard = ({ item }: ProductCardProps) => {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useCart();
  const isAvailable = item.isAvailable !== false;

  const handleAdd = () => {
    if (!isAvailable) {
      return;
    }
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
      <div className="product-card__media">
        {item.imageUrl ? (
          <img src={item.imageUrl} alt={item.name} loading="lazy" />
        ) : (
          <div className="product-card__placeholder" aria-hidden="true">
            {item.name.slice(0, 1)}
          </div>
        )}
        {item.category ? <span className="product-card__badge">{item.category}</span> : null}
      </div>
      <div className="product-card__content">
        <header className="product-card__header">
          <h3>{item.name}</h3>
          {item.description ? <p>{item.description}</p> : null}
        </header>
        <div className="product-card__footer">
          <div className="product-card__price-row">
            <strong className="product-card__price">{formatCurrency(item.price)}</strong>
            <span
              className={
                isAvailable ? "product-card__availability" : "product-card__availability product-card__availability--soldout"
              }
            >
              {isAvailable ? "Available" : "Sold out"}
            </span>
          </div>
          <div className="product-card__actions">
            {isAvailable ? (
              <QuantitySelector value={quantity} onChange={setQuantity} min={1} max={99} />
            ) : (
              <span className="product-card__soldout-note">Back soon</span>
            )}
            <button
              type="button"
              className="button button--primary"
              onClick={handleAdd}
              disabled={!isAvailable}
            >
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </article>
  );
};
