import type { CSSProperties } from "react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useCart } from "../hooks/useCart";

const linkStyle: CSSProperties = {
  color: "inherit",
  textDecoration: "none",
  padding: "0.5rem 0.75rem",
  borderRadius: "0.5rem",
};

const getActiveClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "nav-link nav-link--active" : "nav-link";

export const Navbar = () => {
  const { isAuthenticated, user, signOut, signIn, signUp, loading } = useAuth();
  const { itemCount } = useCart();

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <header className="navbar">
      <div className="navbar__inner">
        <Link to="/" className="navbar__brand">
          Aleena&apos;s Cuisine
        </Link>
        <nav className="navbar__nav">
          <NavLink to="/menu" className={getActiveClass} style={linkStyle}>
            Menu
          </NavLink>
          <NavLink to="/cart" className={getActiveClass} style={linkStyle}>
            Cart ({itemCount})
          </NavLink>
          {isAuthenticated ? (
            <>
              <NavLink to="/profile" className={getActiveClass} style={linkStyle}>
                {user?.name || user?.email}
              </NavLink>
              <button
                type="button"
                className="button button--secondary"
                onClick={handleSignOut}
                disabled={loading}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="button button--secondary"
                onClick={() => {
                  void signIn();
                }}
                disabled={loading}
              >
                Sign in
              </button>
              <button
                type="button"
                className="button button--primary"
                onClick={() => {
                  void signUp();
                }}
                disabled={loading}
              >
                Create account
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};
