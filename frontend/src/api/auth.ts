import { post } from "./client";

export interface ConfirmAccountPayload {
  username: string;
  code: string;
}

export interface ConfirmAccountResponse {
  message: string;
}

export const confirmAccount = (payload: ConfirmAccountPayload) =>
  post<ConfirmAccountResponse>("/api/v1/auth/confirm", payload);
