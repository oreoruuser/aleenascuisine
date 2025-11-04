export interface AuthConfig {
  razorpayKeyId: string;
  razorpayMode: "test" | "live";
  appBaseUrl: string;
  cognitoUserPoolId: string;
  cognitoClientId: string;
  cognitoRegion: string;
  cognitoDomain: string;
  cognitoRedirectUri: string;
  cognitoLogoutUri: string;
  cognitoScopes: string;
}

const getRequiredEnv = (key: string) => {
  const value = import.meta.env[key as keyof ImportMetaEnv];
  if (!value) {
    console.warn(`Environment variable ${key} is not set.`);
    return "";
  }
  return value;
};

export const authConfig: AuthConfig = {
  razorpayKeyId: getRequiredEnv("VITE_RAZORPAY_KEY_ID"),
  razorpayMode: (getRequiredEnv("VITE_RAZORPAY_MODE") as "test" | "live") || "test",
  appBaseUrl: typeof window !== "undefined" ? window.location.origin : "",
  cognitoUserPoolId: getRequiredEnv("VITE_COGNITO_USER_POOL_ID"),
  cognitoClientId: getRequiredEnv("VITE_COGNITO_CLIENT_ID"),
  cognitoRegion: getRequiredEnv("VITE_COGNITO_REGION"),
  cognitoDomain: getRequiredEnv("VITE_COGNITO_DOMAIN"),
  cognitoRedirectUri: getRequiredEnv("VITE_COGNITO_REDIRECT_URI"),
  cognitoLogoutUri: getRequiredEnv("VITE_COGNITO_LOGOUT_URI"),
  cognitoScopes: getRequiredEnv("VITE_COGNITO_SCOPES") || "openid email profile",
};
