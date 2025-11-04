import { Link } from "react-router-dom";

export const NotFoundPage = () => (
  <main className="page">
    <h1>Page not found</h1>
    <p>The page you are looking for does not exist. Head back to the menu to keep browsing.</p>
    <Link to="/menu" className="button button--primary">
      Go to menu
    </Link>
  </main>
);
