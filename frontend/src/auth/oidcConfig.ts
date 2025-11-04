import type { UserManagerSettings } from "oidc-client-ts";
import { authConfig } from "./config";

const {
  cognitoRegion,
  cognitoUserPoolId,
  cognitoClientId,
  cognitoRedirectUri,
  cognitoLogoutUri,
  cognitoScopes,
  appBaseUrl,
} = authConfig;

const authority = `https://cognito-idp.${cognitoRegion}.amazonaws.com/${cognitoUserPoolId}`;
const runtimeRedirectUri = cognitoRedirectUri || (appBaseUrl ? `${appBaseUrl}/auth/callback` : "");
const runtimeLogoutUri = cognitoLogoutUri || appBaseUrl || runtimeRedirectUri;

export const oidcConfig: UserManagerSettings = {
  authority,
  client_id: cognitoClientId,
  redirect_uri: runtimeRedirectUri,
  post_logout_redirect_uri: runtimeLogoutUri,
  response_type: "code",
  scope: cognitoScopes || "openid email profile",
  automaticSilentRenew: true,
  loadUserInfo: true,
  revokeTokensOnSignout: true,
  monitorSession: false,
  metadataSeed: {
    issuer: authority,
    authorization_endpoint: `${authConfig.cognitoDomain}/oauth2/authorize`,
    token_endpoint: `${authConfig.cognitoDomain}/oauth2/token`,
    revocation_endpoint: `${authConfig.cognitoDomain}/oauth2/revoke`,
    userinfo_endpoint: `${authConfig.cognitoDomain}/oauth2/userInfo`,
    end_session_endpoint: `${authConfig.cognitoDomain}/logout`,
  },
};
