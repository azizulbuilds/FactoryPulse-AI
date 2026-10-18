# FactoryPulse AI

**AI-assisted industrial monitoring and predictive-maintenance demo
built with FastAPI, React, SQLite, and AMD Token Factory.**

FactoryPulse AI brings machine-health indicators, sensor readings,
alerts, and maintenance knowledge into one operations dashboard. Its
Maintenance Copilot retrieves relevant passages from the maintenance
knowledge base and, when configured, uses AMD Token Factory to generate
a grounded response.

> **Demo and safety notice:** This project currently uses
> illustrative/demo machine data. It is not connected to live industrial
> equipment. Health scores, alert rules, and recommendations are not
> certified safety limits. Do not use this demo to control machinery or
> make safety-critical decisions.

## Features

-   Fleet overview, machine-health scores, machine status, and
    sensor-reading summaries.
-   Prioritized alerts and alert acknowledgement.
-   Maintenance Copilot using `knowledge_base/maintenance_basics.md`.
-   Optional LLM-generated answers through AMD Token Factory.
-   FastAPI REST backend with interactive API documentation.
-   Responsive React + Vite frontend.
-   SQLite persistence for local demo data.
-   Automated backend API and machine-rule tests.
-   Prepared sensor dataset for future ML experiments.

## Tech Stack

  Layer       Technologies
  ----------- ---------------------------------------------------------
  Frontend    React, Vite, JavaScript, CSS
  Backend     Python 3.11, FastAPI, Pydantic
  Data        SQLite, CSV
  Retrieval   TF-IDF-based knowledge retrieval
  LLM         AMD Token Factory, configured model `DeepSeek-V4-Flash`
  Testing     pytest

## Architecture

``` text
React + Vite dashboard
        | HTTP / REST
        v
FastAPI backend
  ├── Fleet overview and machine health
  ├── Monitoring readings and summary
  ├── Alerts and acknowledgement
  └── Maintenance assistant
         ├── Local maintenance knowledge base
         └── Optional AMD Token Factory LLM
        |
        v
SQLite demo database

ML experiments
  └── ml/data/processed/sensor_data.csv
```

## Repository Layout

``` text
FactoryPulse-AI/
├── apps/
│   ├── backend/          # FastAPI application and database
│   └── frontend/         # React + Vite dashboard
├── knowledge_base/       # Maintenance reference material
├── ml/
│   ├── data/processed/   # Processed sensor dataset
│   ├── configs/          # ML experiment configuration
│   ├── artifacts/        # Generated model artifacts, if any
│   └── src/              # ML and RAG scripts
├── scripts/              # Utility scripts
├── tests/                # Backend tests
├── .gitignore
└── README.md
```

## Requirements

-   Python 3.11 recommended
-   Node.js and npm compatible with the Vite project
-   Git
-   Optional: AMD Token Factory API key for LLM-generated maintenance
    answers

## Run Locally (Windows PowerShell)

Run commands from the repository root unless noted otherwise.

### 1. Create and activate the Python environment

``` powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies using the requirements file present in
`apps/backend`:

``` powershell
pip install -r apps\backend\requirements.txt
```

### 2. Configure the optional LLM integration

Set these variables in the same PowerShell terminal that will launch the
backend:

``` powershell
$env:FACTORYPULSE_LLM_BASE_URL = "https://developer.amd.com.cn/radeon/api/v1"
$env:FACTORYPULSE_LLM_MODEL = "DeepSeek-V4-Flash"
$env:FACTORYPULSE_LLM_API_KEY = "YOUR_AMD_TOKEN_FACTORY_KEY"
```

Replace the placeholder locally. **Never commit a real API key, paste it
into issues, or put it in README/source code.** These environment
variables apply to that terminal session and processes launched from it.
Set them again in a new terminal session when needed.

The backend reads `FACTORYPULSE_LLM_API_KEY`. Keep local `.env` files
out of Git. If a key was ever committed or pushed, revoke/rotate it even
if the file was later removed.

### 3. Start the backend

With `.venv` activated, from the repository root:

``` powershell
python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 --reload
```

Open FastAPI's interactive documentation at
`http://127.0.0.1:8000/docs`.

### 4. Start the frontend

Open a second terminal:

``` powershell
cd apps\frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.
Keep the backend running while testing the dashboard.

## API Endpoints

  -----------------------------------------------------------------------------------------
  Method                  Endpoint                                  Purpose
  ----------------------- ----------------------------------------- -----------------------
  `GET`                   `/api/v1/fleet/overview`                  Fleet and machine
                                                                    overview

  `GET`                   `/api/v1/monitoring/summary`              Monitoring summary

  `GET`                   `/api/v1/monitoring/readings?limit=100`   Recent sensor readings

  `GET`                   `/api/v1/alerts?limit=12`                 Recent alerts

  `PATCH`                 `/api/v1/alerts/{alert_id}/acknowledge`   Acknowledge an alert

  `POST`                  `/api/v1/maintenance/assistant`           Ask the Maintenance
                                                                    Copilot
  -----------------------------------------------------------------------------------------

Example Maintenance Copilot request:

``` json
{
  "question": "What should I check when machine process temperature is too high?"
}
```

Local maintenance-reference retrieval can run without the LLM.
LLM-generated answers require valid AMD Token Factory configuration.
Treat all recommendations as informational guidance, not approved
maintenance procedures.

## Testing

From the repository root with the Python environment activated:

``` powershell
python -m pytest -q --ignore=ml/src/test_autoencoder.py
```

During development, this command completed with **14 passed**. The
experimental autoencoder test was excluded because PyTorch was not
installed in that environment. Re-run tests after changes and report the
current result rather than assuming this earlier result still applies.

Build the frontend:

``` powershell
cd apps\frontend
npm run build
```

The production build completed successfully during development.

## Demo Data and ML Status

-   The dashboard uses illustrative/demo machine data, not live
    industrial telemetry.
-   Machine-health values and rule thresholds are demonstration logic,
    not certified safety limits.
-   A processed sensor dataset exists at
    `ml/data/processed/sensor_data.csv`.
-   The autoencoder/model-training workflow is experimental and is not
    required for the current dashboard demo.
-   Do not claim a predictive model is deployed or achieves a specific
    accuracy unless current evaluation results and a deployed inference
    path support that claim.

## Security

-   Do not commit `.env` files, API keys, access tokens, or credentials.
-   Keep local secrets in environment variables or an ignored local
    environment file.
-   If a secret reaches GitHub, rotate/revoke it. Removing it from the
    latest version does not necessarily remove it from Git history.
-   The demo is not hardened for production industrial use. Before
    deployment, review CORS, authentication/authorization, rate limits,
    logging, persistence, and secret management.

## Deployment Notes

The project is currently designed for local demonstration. Before
deploying publicly:

1.  Configure the backend and frontend as separate services or use a
    platform that supports both.
2.  Set the frontend API base/proxy configuration to the deployed
    backend URL.
3.  Configure `FACTORYPULSE_LLM_BASE_URL`, `FACTORYPULSE_LLM_MODEL`, and
    `FACTORYPULSE_LLM_API_KEY` as **server-side environment variables**
    in the hosting provider.
4.  Never expose the LLM key in frontend variables or browser code.
5.  Verify persistent storage if SQLite data must survive restarts;
    ephemeral hosting filesystems may reset.
6.  Test `/docs`, dashboard API calls, and the Maintenance Copilot after
    deployment.

## Team

**Team:** ForgePulse-AI

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
