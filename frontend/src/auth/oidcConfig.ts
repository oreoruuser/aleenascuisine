import type { UserManagerSettings } from "oidc-client-ts";
import { authConfig } from "./config";

const { cognitoRegion, cognitoUserPoolId, cognitoClientId, cognitoRedirectUri, cognitoLogoutUri, cognitoScopes } = authConfig;

const authority = `https://cognito-idp.${cognitoRegion}.amazonaws.com/${cognitoUserPoolId}`;

export const oidcConfig: UserManagerSettings = {
  authority,
  client_id: cognitoClientId,
  redirect_uri: cognitoRedirectUri,
  post_logout_redirect_uri: cognitoLogoutUri,
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
