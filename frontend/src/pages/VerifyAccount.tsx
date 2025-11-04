import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { confirmAccount } from "../api/auth";

type Status = "idle" | "submitting" | "success" | "error";

export const VerifyAccountPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [usernameInput, setUsernameInput] = useState<string>("");
  const isSubmittingRef = useRef(false);
  const autoTriggeredRef = useRef(false);

  const { usernameFromParams, codeFromParams } = useMemo(() => {
    const state = (location.state as { username?: string; code?: string } | null) ?? {};
    const usernameParam =
      searchParams.get("username") ||
      searchParams.get("userName") ||
      searchParams.get("email") ||
      searchParams.get("login") ||
      undefined;
    const codeParam =
      searchParams.get("code") ||
      searchParams.get("confirmation_code") ||
      searchParams.get("confirmationCode") ||
      undefined;

    return {
      usernameFromParams: state.username || usernameParam || "",
      codeFromParams: state.code || codeParam || "",
    };
  }, [location.state, searchParams]);

  useEffect(() => {
    const state = location.state as { error?: string } | null;
    if (state?.error) {
      setStatus("error");
      setError(state.error);
    }
  }, [location.state]);

  useEffect(() => {
    if (!usernameInput && usernameFromParams) {
      setUsernameInput(usernameFromParams);
    }
  }, [usernameFromParams, usernameInput]);

  const cleanCode = useMemo(() => codeFromParams.trim(), [codeFromParams]);

  const handleUsernameChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (status !== "idle") {
      setStatus("idle");
      setError(null);
    }
    setUsernameInput(event.currentTarget.value);
  };

  const attemptConfirm = useCallback(async (username: string, code: string) => {
    if (isSubmittingRef.current) {
      return;
    }
    isSubmittingRef.current = true;
    setStatus("submitting");
    setError(null);
    try {
      await confirmAccount({ username, code });
      setStatus("success");
    } catch (err) {
      const message =
        (err as { message?: string })?.message ||
        "Verification failed. Please double-check the details and try again.";
      setError(message);
      setStatus("error");
    } finally {
      isSubmittingRef.current = false;
    }
  }, []);

  const handleVerify = useCallback(async () => {
    const cleanUsername = usernameInput.trim();
    if (!cleanUsername) {
      setError("Enter the email or username you used during sign up.");
      setStatus("error");
      return;
    }
    if (!cleanCode) {
      setError(
  "We couldn't find a verification code in this link. Please open the email titled \"Verify your new account\" and follow the link again."
      );
      setStatus("error");
      return;
    }
    await attemptConfirm(cleanUsername, cleanCode);
  }, [attemptConfirm, cleanCode, usernameInput]);

  useEffect(() => {
    if (autoTriggeredRef.current) {
      return;
    }
    const cleanUsername = usernameInput.trim();
    if (!cleanUsername || !cleanCode) {
      return;
    }
    autoTriggeredRef.current = true;
    void attemptConfirm(cleanUsername, cleanCode);
  }, [attemptConfirm, cleanCode, usernameInput]);

  const canVerify = Boolean(usernameInput.trim()) && status !== "submitting";

  return (
    <main className="page page--centered">
      <h1>Verify your account</h1>
      <p>
        Enter the email or username you used to register, then click verify to complete your sign up. We&apos;ll finish
        the process with the code from your confirmation email.
      </p>
      <label className="form__label" htmlFor="verify-username">
        Email or username
        <input
          id="verify-username"
          type="text"
          name="username"
          value={usernameInput}
          onChange={handleUsernameChange}
          autoComplete="email"
          className="form__input"
          disabled={status === "submitting"}
          placeholder="you@example.com"
        />
      </label>
      {error ? <p className="form__error">{error}</p> : null}
      {status === "success" ? (
        <div className="form__success">
          <p>Your account is verified! You can now sign in.</p>
          <button
            type="button"
            className="button button--primary"
            onClick={() => navigate("/signin", { replace: true })}
          >
            Continue to sign in
          </button>
        </div>
      ) : (
        <button type="button" className="button button--primary" onClick={handleVerify} disabled={!canVerify}>
          {status === "submitting" ? "Verifying..." : "Verify account"}
        </button>
      )}
      {!cleanCode && status !== "success" ? (
        <p className="form__hint">
          We couldn&apos;t find a verification code in this link. Check the email titled &quot;Verify your new account&quot; and
          open the link on this device.
        </p>
      ) : null}
    </main>
  );
};
