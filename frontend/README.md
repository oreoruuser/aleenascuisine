# Aleena's Cuisine – Phase C Lite Frontend

A minimal React + Vite panel for exercising the Aleena's Cuisine backend during Phase C Lite. The console lets you:

- Configure the API base URL, API key, and Cognito ID token.
- Ping the `/health` endpoint.
- Fetch the cakes catalog.
- Build a cart and submit a test order (with automatic idempotency key).

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Vite will expose the site at `http://localhost:5173` by default. Open the URL in your browser and supply the necessary credentials.

Set these environment variables when deploying:

- `VITE_API_BASE_URL` – full API Gateway endpoint that includes the `/api/v1` prefix.
- `VITE_RAZORPAY_KEY_ID` – Razorpay key to display in the UI for quick verification.

To generate a production bundle (upload the `dist/` folder to Amplify manual deployment):

```bash
npm run build
```

The build metadata is embedded in `window.__APP_BUILD__` so you can confirm the tagged release in the footer.
