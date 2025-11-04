import { Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { CartPreview } from "./components/CartPreview";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { HomePage } from "./pages/Home";
import { MenuPage } from "./pages/Menu";
import { ProductPage } from "./pages/Product";
import { CartPage } from "./pages/Cart";
import { CheckoutPage } from "./pages/Checkout";
import { SignInPage } from "./pages/SignIn";
import { SignUpPage } from "./pages/SignUp";
import { ProfilePage } from "./pages/Profile";
import { OrderSuccessPage } from "./pages/OrderSuccess";
import { NotFoundPage } from "./pages/NotFound";
import { AuthCallbackPage } from "./pages/AuthCallback";

const App = () => (
  <div className="app-shell">
    <Navbar />
    <CartPreview />
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/menu" element={<MenuPage />} />
      <Route path="/menu/:id" element={<ProductPage />} />
      <Route path="/cart" element={<CartPage />} />
      <Route path="/signin" element={<SignInPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/order-success" element={<OrderSuccessPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </div>
);

export default App;
