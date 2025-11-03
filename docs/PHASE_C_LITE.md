# Phase C Lite Frontend Checklist

> Goal: stand up a temporary frontend fast, using AWS Amplify manual deploy. Complete these steps when time allows.

1. **Initial Setup**
   - Open AWS Amplify Console → choose **Host your web app**.
   - Pick **Deploy without Git provider** (manual upload) and create the app named `aleenascuisine-frontend`.

2. **Build Local Frontend**
   - Scaffold a lightweight React app (Vite or any static site generator).
   - Run the local build command to produce the static bundle (typically `dist/` or `build/`).
   - Confirm the output folder has the compiled HTML, JS, and CSS assets.

3. **Deploy to Amplify**
   - In Amplify, select **Deploy manually** and upload the build output folder.
   - Wait for the deployment; Amplify will issue a default domain such as `https://main.<hash>.amplifyapp.com`.
   - Verify the site loads on that default domain before proceeding.

4. **Connect Domain (`aleenascuisine.me`)**
   - Amplify Console → **Domain management** → **Add domain** → enter `aleenascuisine.me`.
   - Map the root domain and optionally `www` (or other subdomains).
   - If the domain is already in Route 53, Amplify will manage DNS automatically; otherwise, update the registrar to use the AWS Route 53 name servers.
   - Allow 15–30 minutes (sometimes longer) for DNS propagation, then re-check the custom domain.

5. **Configure Environment Variables**
   - Amplify Console → **App settings** → **Environment variables**.
   - Add / update:
     - `VITE_API_BASE_URL` → current API Gateway endpoint.
     - `VITE_RAZORPAY_KEY_ID` → Razorpay test key.
   - Save, then trigger a rebuild/deploy so the new variables embed in the static bundle.

6. **Verify End-to-End Flow**
   - From the deployed site, confirm API interactions (menu fetch, order submission) succeed against the backend.
   - Run a Razorpay **test payment** and ensure the UI shows the success path.
   - Access the site via `https://aleenascuisine.me` to confirm the custom domain resolves and serves the latest build.

> When expanding into full Phase C, plan to link the repo to Amplify (Git-backed deployments), add CI gates, and replace the placeholder frontend with the production-ready experience.
