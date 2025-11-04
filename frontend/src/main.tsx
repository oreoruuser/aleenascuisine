import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { AuthProvider as OidcProvider } from "react-oidc-context";
import { oidcConfig } from "./auth/oidcConfig";

type UserWithState = {
  state?: {
    returnPath?: string;
  };
};

const handleSigninCallback = (user?: UserWithState | null) => {
  const target = user?.state?.returnPath || "/menu";
  window.history.replaceState({}, document.title, target || "/");
};
import { CartProvider } from "./context/CartContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
  <OidcProvider {...oidcConfig} onSigninCallback={handleSigninCallback}>
        <AuthProvider>
          <CartProvider>
            <App />
          </CartProvider>
        </AuthProvider>
      </OidcProvider>
    </BrowserRouter>
  </React.StrictMode>
);
