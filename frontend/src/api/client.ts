const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  parseJson?: boolean;
}

const buildUrl = (path: string) => {
  if (!API_BASE_URL) {
    return path;
  }
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
};

const parseResponse = async (response: Response, parseJson: boolean) => {
  if (!parseJson) {
    return response;
  }
  const text = await response.text();
  if (!text) {
    return undefined;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    console.warn("Failed to parse JSON response", error);
    return text;
  }
};

export const request = async <T = unknown>(
  path: string,
  method: HttpMethod,
  body?: unknown,
  options?: RequestOptions
): Promise<T> => {
  const headers = new Headers(options?.headers);
  if (!(body instanceof FormData)) {
    headers.set("Content-Type", headers.get("Content-Type") || "application/json");
  }
  if (!options?.skipAuth && authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const payload: RequestInit = {
    ...options,
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  };

  const response = await fetch(buildUrl(path), payload);
  const data = await parseResponse(response, options?.parseJson ?? true);

  if (!response.ok) {
    const message =
      (data as { message?: string } | undefined)?.message ||
      response.statusText ||
      "Request failed";
    const error = new Error(message) as Error & {
      status?: number;
      data?: unknown;
    };
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data as T;
};

export const get = <T = unknown>(path: string, options?: RequestOptions) =>
  request<T>(path, "GET", undefined, options);
export const post = <T = unknown>(path: string, body?: unknown, options?: RequestOptions) =>
  request<T>(path, "POST", body, options);
export const patch = <T = unknown>(path: string, body?: unknown, options?: RequestOptions) =>
  request<T>(path, "PATCH", body, options);
export const del = <T = unknown>(path: string, options?: RequestOptions) =>
  request<T>(path, "DELETE", undefined, options);
