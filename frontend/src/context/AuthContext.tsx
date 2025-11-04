import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAuth as useOidcAuth } from "react-oidc-context";
import type { User } from "oidc-client-ts";
import { setAuthToken } from "../api/client";

interface AuthState {
  initializing: boolean;
  loading: boolean;
  isAuthenticated: boolean;
  user?: AuthUser;
  tokens?: AuthTokens;
}

interface AuthContextValue extends AuthState {
  signIn: () => Promise<void>;
  signUp: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<AuthTokens | undefined>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export interface AuthTokens {
  accessToken: string;
  idToken?: string;
  refreshToken?: string;
  expiresAt?: number;
}

export interface AuthUser {
  id: string;
  email?: string;
  name?: string;
  phoneNumber?: string;
  emailVerified?: boolean;
}

interface AuthSession {
  tokens: AuthTokens;
  user: AuthUser;
}

const buildSession = (user?: User | null): AuthSession | undefined => {
  if (!user || !user.profile) {
    return undefined;
  }

  const tokens: AuthTokens = {
    accessToken: user.access_token ?? "",
    idToken: user.id_token ?? undefined,
    refreshToken: user.refresh_token ?? undefined,
    expiresAt: user.expires_at ? user.expires_at * 1000 : undefined,
  };

  if (!tokens.accessToken) {
    return undefined;
  }

  const profile = user.profile as Record<string, unknown>;
  const authUser: AuthUser = {
    id: typeof profile.sub === "string" ? profile.sub : tokens.accessToken,
    email: typeof profile.email === "string" ? profile.email : undefined,
    name: typeof profile.name === "string" ? profile.name : undefined,
    phoneNumber: typeof profile.phone_number === "string" ? profile.phone_number : undefined,
    emailVerified:
      typeof profile.email_verified === "boolean" ? profile.email_verified : undefined,
  };

  return { tokens, user: authUser };
};

const getReturnPath = () =>
  typeof window !== "undefined"
    ? `${window.location.pathname}${window.location.search}${window.location.hash}`
    : "/";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const oidc = useOidcAuth();
  const [state, setState] = useState<AuthState>({
    initializing: true,
    loading: false,
    isAuthenticated: false,
    user: undefined,
    tokens: undefined,
  });

  useEffect(() => {
    if (oidc.isLoading) {
      return;
    }

    const session = buildSession(oidc.user);

    if (session) {
      setAuthToken(session.tokens.accessToken);
      setState({
        initializing: false,
        loading: false,
        isAuthenticated: true,
        user: session.user,
        tokens: session.tokens,
      });
      return;
    }

    if (oidc.error) {
      console.warn("OIDC authentication error", oidc.error);
    }

    setAuthToken(null);
    setState({
      initializing: false,
      loading: false,
      isAuthenticated: false,
      user: undefined,
      tokens: undefined,
    });
  }, [oidc.isLoading, oidc.user, oidc.error]);

  const withLoading = useCallback(
    async (action: () => Promise<void>) => {
      setState((prev) => ({ ...prev, loading: true }));
      try {
        await action();
      } finally {
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    []
  );

  const signIn = useCallback(
    () =>
      withLoading(() =>
        oidc.signinRedirect({
          state: {
            returnPath: getReturnPath(),
          },
        })
      ),
    [withLoading, oidc]
  );

  const signUp = useCallback(
    () =>
      withLoading(() =>
        oidc.signinRedirect({
          extraQueryParams: {
            screen_hint: "signup",
          },
          state: {
            returnPath: getReturnPath(),
          },
        })
      ),
    [withLoading, oidc]
  );

  const signOut = useCallback(() => withLoading(() => oidc.signoutRedirect()), [withLoading, oidc]);

  const refresh = useCallback(async () => {
    try {
      const user = await oidc.signinSilent();
      const session = buildSession(user);
      if (session) {
        setAuthToken(session.tokens.accessToken);
        setState((prev) => ({
          ...prev,
          isAuthenticated: true,
          user: session.user,
          tokens: session.tokens,
        }));
        return session.tokens;
      }
    } catch (error) {
      console.warn("Failed silent sign-in", error);
    }

    await oidc.removeUser();
    setAuthToken(null);
    setState((prev) => ({
      ...prev,
      isAuthenticated: false,
      user: undefined,
      tokens: undefined,
    }));
    return undefined;
  }, [oidc]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      signIn,
      signOut,
      signUp,
      refreshSession: refresh,
    }),
    [state, signIn, signOut, signUp, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
};
