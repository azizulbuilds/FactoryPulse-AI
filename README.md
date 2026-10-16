# FactoryPulse AI — Frontend update

This is a drop-in React/Vite UI refresh for the existing `apps/frontend` directory. It uses only React and Vite (no chart or icon dependency is added). The visual system is the **Industrial Signal** theme: graphite-blue navigation, an icy neutral canvas, cobalt actions, cyan data accents, and restrained amber/red alert states. It intentionally avoids the previous forest-green/lime palette.

## Apply the update

1. Stop the frontend dev server with `Ctrl + C`.
2. Extract this ZIP into the **root of your existing `FactoryPulse-AI` project**. Allow the files under `apps/frontend` to merge/overwrite.
3. Keep your existing `package.json`, `package-lock.json`, and `src/main.jsx`. The Vite React starter's `main.jsx` should already import `./index.css` and `./App.jsx`.
4. Start the backend in one terminal, from the project root:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 --reload
   ```

5. Start the frontend in another terminal:

   ```powershell
   cd apps/frontend
   npm install
   npm run dev
   ```

6. Open the Vite URL printed in the terminal (usually `http://localhost:5173`).

## Backend connection

The UI expects these endpoints on the existing FastAPI backend:

- `GET /api/v1/fleet/overview`
- `GET /api/v1/monitoring/summary`
- `GET /api/v1/monitoring/readings?limit=100`
- `GET /api/v1/alerts?limit=12`
- `PATCH /api/v1/alerts/{alert_id}/acknowledge`
- `POST /api/v1/maintenance/assistant` with `{ "question": "..." }`

Vite proxies `/api/*` requests to `http://127.0.0.1:8000`. Set `FACTORYPULSE_API_URL` before starting Vite if your backend runs at another address.

The UI tolerates common response wrappers (`machines`, `items`, `alerts`, `readings`, and `summary`). If it cannot find machine rows, it displays clearly labelled **illustrative preview data** instead of presenting sample values as live telemetry. API status is shown in the header. Maintenance assistant output depends on the backend route and configuration being available.

## Included UX

- Responsive operations dashboard and navigation
- Fleet summary and machine health distribution
- Sensor trend visualization with live history when available
- Searchable machine table and detail drawer
- Prioritized alert list and acknowledgement action
- Maintenance copilot interface with prompt suggestions and source display
- Preview-mode warning, refresh button, and 30-second polling

The health indicator reflects the backend's current scoring/rule logic. It is not a certified safety assessment, and illustrative warning thresholds should be validated for the actual equipment before operational use.
