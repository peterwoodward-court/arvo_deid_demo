# De‑ID Demo – A0 Poster Companion
Minimal repo that powers an interactive demo for your poster.

## ️📐  Architecture
```
static site (GitHub Pages / GCS) ──► Cloud Function (Python) ──► Google Cloud DLP
                                         ▲
                                         │(optional) Vertex AI for hallucination check
```

* `frontend/` — vanilla HTML + JS (no framework)  
* `cloud/`    — Python 3.11 Cloud Function exposing **/deid**

## 🚀 Quick Start

1. **Create** a GCP project & enable **DLP API**.  
2. **Deploy** the function:
   ```bash
   cd cloud
   gcloud functions deploy deid \
     --runtime python311 \
     --trigger-http --allow-unauthenticated \
     --region europe-west2
   ```
   Note the HTTPS endpoint it prints (`https://REGION-PROJECT.cloudfunctions.net/deid`).

3. **Edit** `frontend/config.js` and paste that endpoint:
   ```js
   export const API_ENDPOINT = "https://…/deid";
   ```

4. **Publish** the site (GitHub Pages, Firebase Hosting, or GCS Static).  
   ```
   cd frontend
   firebase deploy       #  or  gsutil rsync -R . gs://YOUR_BUCKET
   ```

5. **Generate** a QR code pointing to the site URL and drop it into your poster.

## 🛠  Local dev preview
```
cd frontend
python3 -m http.server 8080
# open http://localhost:8080
```

## 🧩  Extending
* Add `hallucination` endpoint in `cloud/main.py` using Vertex AI Chat.
* Replace inline templates in `script.js` with Markdown files fetched on demand.
* Wrap everything in Cloud Run for regional routing.

--  
Generated 2025-05-02.
