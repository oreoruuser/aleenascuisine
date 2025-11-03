import { useCallback, useEffect, useMemo, useState } from "react";

type ApiResult = {
  timestamp: string;
  ok: boolean;
  status: number;
  body?: unknown;
  error?: string;
};

const buildHeaders = (apiKey: string, idToken: string) => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (apiKey) {
    headers["x-api-key"] = apiKey;
  }
  if (idToken) {
    headers["Authorization"] = `Bearer ${idToken}`;
  }
  return headers;
};

const formatJson = (value: unknown) =>
  JSON.stringify(value, null, 2).replace(/\\n/g, "\n");

const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL || "https://example.com";
const defaultRazorpayKey = import.meta.env.VITE_RAZORPAY_KEY_ID || "rzp_test_xxx";

function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultBaseUrl);
  const [apiKey, setApiKey] = useState("");
  const [idToken, setIdToken] = useState("");
  const [cakeId, setCakeId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [cartId, setCartId] = useState("");
  const [lastResult, setLastResult] = useState<ApiResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [razorpayKey] = useState(defaultRazorpayKey);

  const headers = useMemo(() => buildHeaders(apiKey, idToken), [apiKey, idToken]);

  useEffect(() => {
    if (!idToken) {
      setIdToken(localStorage.getItem("aleena:idToken") || "");
    }
    if (!apiKey) {
      setApiKey(localStorage.getItem("aleena:apiKey") || "");
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("aleena:apiKey", apiKey);
  }, [apiKey]);

  useEffect(() => {
    localStorage.setItem("aleena:idToken", idToken);
  }, [idToken]);

  const callApi = useCallback(
    async (path: string, init?: RequestInit) => {
      setIsLoading(true);
      setLastResult(null);
      const url = `${apiBaseUrl.replace(/\/$/, "")}${path}`;
      try {
        const response = await fetch(url, {
          ...init,
          headers: {
            ...headers,
            ...(init?.headers as Record<string, string> | undefined),
          },
        });
        const text = await response.text();
        const body = text ? JSON.parse(text) : undefined;
        const result: ApiResult = {
          ok: response.ok,
          status: response.status,
          body,
          timestamp: new Date().toISOString(),
        };
        setLastResult(result);
        return body;
      } catch (error) {
        setLastResult({
          ok: false,
          status: -1,
          error: error instanceof Error ? error.message : String(error),
          timestamp: new Date().toISOString(),
        });
        return undefined;
      } finally {
        setIsLoading(false);
      }
    },
    [apiBaseUrl, headers]
  );

  const hitHealth = () => callApi("/health");

  const listCakes = async () => {
    const payload = await callApi("/cakes", { method: "GET" });
    if (payload?.cakes?.length) {
      setCakeId((payload.cakes[0]?.cake_id as string) || "");
    }
  };

  const createCart = async () => {
    if (!cakeId) {
      setLastResult({
        ok: false,
        status: -1,
        error: "Provide a cake_id first (fetch cakes).",
        timestamp: new Date().toISOString(),
      });
      return;
    }
    const body = {
      customer_id: null,
      cart_token: null,
      items: [
        {
          cake_id: cakeId,
          quantity,
          price_each: 0,
        },
      ],
    };
    const payload = await callApi("/cart", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (payload?.cart_id) {
      setCartId(payload.cart_id as string);
    }
  };

  const createOrder = async () => {
    if (!cartId) {
      setLastResult({
        ok: false,
        status: -1,
        error: "Create a cart first.",
        timestamp: new Date().toISOString(),
      });
      return;
    }
    const idempotencyKey = crypto.randomUUID();
    await callApi("/orders", {
      method: "POST",
      headers: {
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({
        cart_id: cartId,
        customer_id: null,
        idempotency_key: idempotencyKey,
        is_test: true,
      }),
    });
  };

  return (
    <div className="app-shell">
      <header>
        <h1>Aleena's Cuisine – Phase C Lite Frontend</h1>
        <p>Temporary control panel to exercise the dev API and Razorpay test mode.</p>
      </header>

      <section className="card">
        <h2>Configuration</h2>
        <label>
          API Base URL
          <input
            value={apiBaseUrl}
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://xxxx.execute-api.ap-south-1.amazonaws.com/dev/api/v1"
          />
        </label>
        <label>
          API Key
          <input
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="x-api-key"
          />
        </label>
        <label>
          ID Token (Cognito)
          <input
            value={idToken}
            onChange={(event) => setIdToken(event.target.value)}
            placeholder="Cognito JWT"
          />
        </label>
        <p className="hint">
          Razorpay key in use: <code>{razorpayKey}</code>
        </p>
        <button onClick={hitHealth} disabled={isLoading}>
          Ping /health
        </button>
        <button onClick={listCakes} disabled={isLoading}>
          Fetch Cakes
        </button>
      </section>

      <section className="card">
        <h2>Cart Builder</h2>
        <label>
          Cake ID
          <input
            value={cakeId}
            onChange={(event) => setCakeId(event.target.value)}
            placeholder="UUID from cakes list"
          />
        </label>
        <label>
          Quantity
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(event) => setQuantity(Number(event.target.value))}
          />
        </label>
        <button onClick={createCart} disabled={isLoading}>
          Create Cart
        </button>
        {cartId && (
          <p className="hint">
            Latest cart: <code>{cartId}</code>
          </p>
        )}
      </section>

      <section className="card">
        <h2>Order Creation</h2>
        <label>
          Cart ID
          <input
            value={cartId}
            onChange={(event) => setCartId(event.target.value)}
            placeholder="Cart ID from previous step"
          />
        </label>
        <button onClick={createOrder} disabled={isLoading}>
          Submit Order (test mode)
        </button>
      </section>

      <section className="card">
        <h2>Last Result</h2>
        {lastResult ? (
          <div className={`result ${lastResult.ok ? "ok" : "error"}`}>
            <p>
              <strong>Status:</strong> {lastResult.status} · {lastResult.timestamp}
            </p>
            {lastResult.error && <pre>{lastResult.error}</pre>}
            {lastResult.body && <pre>{formatJson(lastResult.body)}</pre>}
          </div>
        ) : (
          <p>No calls yet.</p>
        )}
      </section>

      <footer>
        <p>
          Build info: <code>{JSON.stringify(__APP_BUILD__)}</code>
        </p>
      </footer>
    </div>
  );
}

export default App;

declare const __APP_BUILD__: {
  mode: string;
  timestamp: string;
};
