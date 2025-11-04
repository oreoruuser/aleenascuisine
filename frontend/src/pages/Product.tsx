import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchMenuItem, type CakeDetail } from "../api/orders";
import { Loader } from "../components/Loader";
import { formatCurrency } from "../utils/currency";
import { QuantitySelector } from "../components/QuantitySelector";
import { useCart } from "../hooks/useCart";

export const ProductPage = () => {
  const { id } = useParams<{ id: string }>();
  const [item, setItem] = useState<CakeDetail | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addItem } = useCart();

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const menuItem = await fetchMenuItem(id);
        setItem(menuItem);
      } catch (err) {
        const message = (err as { message?: string } | undefined)?.message || "Failed to load item";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [id]);

  if (loading) {
    return <Loader message="Loading item" />;
  }

  if (error || !item) {
    return (
      <main className="page">
        <h1>Item unavailable</h1>
        <p className="form-error">{error || "We could not find this item."}</p>
      </main>
    );
  }

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
    <main className="page">
      <article className="product-detail">
        {item.imageUrl ? <img src={item.imageUrl} alt={item.name} loading="lazy" /> : null}
        <div className="product-detail__content">
          <h1>{item.name}</h1>
          <p>{item.description}</p>
          <strong>{formatCurrency(item.price)}</strong>
          <div className="product-detail__cta">
            <QuantitySelector value={quantity} onChange={setQuantity} min={1} max={99} />
            <button type="button" className="button button--primary" onClick={handleAdd}>
              Add to cart
            </button>
          </div>
        </div>
      </article>
    </main>
  );
};
