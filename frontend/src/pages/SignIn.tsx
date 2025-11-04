import { useEffect } from "react";
import { Loader } from "../components/Loader";
import { useAuth } from "../hooks/useAuth";

export const SignInPage = () => {
  const { signIn } = useAuth();

  useEffect(() => {
    void signIn();
  }, [signIn]);

  return <Loader message="Redirecting to sign in" />;
};
