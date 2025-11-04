import { useEffect, useMemo, useState } from "react";
import { fetchMenu, type CakeSummary } from "../api/orders";
import { Loader } from "../components/Loader";
import { ProductCard } from "../components/ProductCard";
import { curatedCakes } from "../data/cakes";

type DisplayCake = CakeSummary & { description?: string; imageUrl?: string };

export const MenuPage = () => {
  const [items, setItems] = useState<DisplayCake[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const menu = await fetchMenu();
        const curatedBySlug = new Map(curatedCakes.map((cake) => [cake.slug, cake]));
        const enriched = menu.map<DisplayCake>((cake) => {
          const curated = curatedBySlug.get(cake.slug);
          if (curated) {
            curatedBySlug.delete(cake.slug);
          }
          return {
            ...cake,
            description: curated?.description,
            imageUrl: curated?.imageUrl,
            category: cake.category ?? curated?.category ?? undefined,
          };
        });
        const remainingCurated = Array.from(curatedBySlug.values());
        const combined = enriched.length
          ? enriched.concat(remainingCurated)
          : curatedCakes;
        setItems(combined);
        setError(enriched.length ? null : "Showing our signature collection while we refresh the live menu.");
      } catch (err) {
        const message = (err as { message?: string } | undefined)?.message || "Failed to load menu";
        setItems(curatedCakes);
        setError(`${message}. Showing our signature collection for now.`);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  if (loading) {
    return <Loader message="Loading menu" />;
  }

  const categoryDescriptions: Record<string, string> = {
    Signature: "Our chef's award-winning centrepieces designed for milestone celebrations.",
    "Best Sellers": "Crowd favourites that our regulars reorder every single month.",
    Chocolate: "Cacao-forward indulgence crafted with single-origin couvertures.",
    Entremets: "Multi-textured French entremets finished with a mirror-gloss glaze.",
  "Summer Specials": "Limited-run tropical creations featuring seasonal produce.",
  Patisserie: "Inspired by Parisian patisseries, ideal for intimate gatherings.",
    Cheesecakes: "Ultra-creamy, slow-baked cheesecakes with a silky finish.",
    "Tea Cakes": "Light, fragrant loaves that pair beautifully with afternoon tea.",
  };

  const groups = useMemo(() => {
    const categories = new Map<string, DisplayCake[]>();
    for (const item of items) {
      const key = item.category || "Artisan Cakes";
      const bucket = categories.get(key) ?? [];
      bucket.push(item);
      categories.set(key, bucket);
    }
    return Array.from(categories.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [items]);

  return (
    <main className="page page--menu">
      <header className="page__header page__header--stacked">
        <div>
          <p className="eyebrow">Artisanal Cakes &amp; Petite Gateaux</p>
          <h1>Explore Aleena&apos;s patisserie showcase</h1>
          <p className="page__subhead">
            Small-batch cakes crafted with Valrhona chocolate, seasonal fruits, and house-made fillings. Eggless and
            custom inscription options available on request.
          </p>
        </div>
        <div className="menu__badges">
          <span>48-hour preorder</span>
          <span>Same-day pickup for select cakes</span>
          <span>Complimentary tasting consultation</span>
        </div>
      </header>

      {error ? <div className="alert alert--muted">{error}</div> : null}

      {groups.map(([category, catalog]) => (
        <section key={category} className="menu-section">
          <header className="menu-section__header">
            <div>
              <h2>{category}</h2>
              {categoryDescriptions[category] ? <p>{categoryDescriptions[category]}</p> : null}
            </div>
            <span className="menu-section__count">{catalog.length} selections</span>
          </header>
          <div className="grid">
            {catalog.map((item) => (
              <ProductCard key={item.id} item={item} />
            ))}
          </div>
        </section>
      ))}
    </main>
  );
};
