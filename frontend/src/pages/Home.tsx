import { Link } from "react-router-dom";

export const HomePage = () => (
  <main className="hero">
    <section className="hero__content">
      <h1>Celebrate every occasion with Aleena&apos;s cakes</h1>
      <p>
        Order handcrafted cakes, desserts, and baked treats with easy scheduling and secure payments via Razorpay.
      </p>
      <div className="hero__actions">
        <Link to="/menu" className="button button--primary">
          Explore menu
        </Link>
        <Link to="/cart" className="button button--ghost">
          View cart
        </Link>
      </div>
    </section>
  </main>
);
