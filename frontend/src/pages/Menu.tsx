import { useEffect, useState } from "react";
import { fetchMenu, type CakeSummary } from "../api/orders";
import { Loader } from "../components/Loader";
import { ProductCard } from "../components/ProductCard";

export const MenuPage = () => {
  const [items, setItems] = useState<CakeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const menu = await fetchMenu();
        setItems(menu);
      } catch (err) {
        const message = (err as { message?: string } | undefined)?.message || "Failed to load menu";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  if (loading) {
    return <Loader message="Loading menu" />;
  }

  if (error) {
    return (
      <main className="page">
        <h1>Menu</h1>
        <p className="form-error">{error}</p>
      </main>
    );
  }

  return (
    <main className="page">
      <h1>Menu</h1>
      <section className="grid">
        {items.map((item) => (
          <ProductCard key={item.id} item={item} />
        ))}
      </section>
    </main>
  );
};
