import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Loader } from "./Loader";

export const ProtectedRoute = () => {
  const { isAuthenticated, initializing, signIn } = useAuth();

  useEffect(() => {
    if (!initializing && !isAuthenticated) {
      void signIn();
    }
  }, [initializing, isAuthenticated, signIn]);

  if (initializing) {
    return <Loader message="Loading your session" />;
  }

  if (!isAuthenticated) {
    return <Loader message="Redirecting to sign in" />;
  }

  return <Outlet />;
};
