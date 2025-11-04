import { useEffect } from "react";
import { Loader } from "../components/Loader";
import { useAuth } from "../hooks/useAuth";

export const SignUpPage = () => {
  const { signUp } = useAuth();

  useEffect(() => {
    void signUp();
  }, [signUp]);

  return <Loader message="Redirecting to sign up" />;
};
