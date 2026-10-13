# ForgePulse AI

### AMD-Powered Industrial Intelligence

ForgePulse AI is an industrial AI platform designed to help
factories identify unusual machine behaviour, investigate
potential problems, and retrieve relevant maintenance guidance.

## Problem

Factories generate sensor readings, equipment logs, and
technical documentation. Identifying unusual behaviour and
finding the right troubleshooting information can take time.

ForgePulse AI aims to bring these capabilities together in
one practical application.

## Planned Features

- Industrial sensor anomaly detection
- Machine health monitoring
- AI-assisted troubleshooting
- Retrieval-augmented generation (RAG)
- Maintenance alerts and recommendations
- AMD GPU-accelerated model inference

## Technology Stack

### Machine Learning
- Python
- PyTorch
- Scikit-learn

### AMD Integration
- AMD Instinct GPU
- AMD ROCm

### Backend
- FastAPI
- PostgreSQL

### Frontend
- React
- TypeScript
- Vite

### Generative AI
- Large Language Model API
- Embeddings
- Vector search
- Retrieval-augmented generation

## Development Approach

The model will be trained in a cloud environment rather than
on the developer's laptop.

AMD GPU inference will be integrated into the deployed
application and verified using the actual execution runtime.

## Current Status

Early development.

Model training, evaluation, AMD integration, and application
deployment are planned development milestones.

## Planned Dataset

AI4I 2020 Predictive Maintenance Dataset.

This dataset contains synthetic industrial sensor observations
and machine failure labels.

## Project Structure

- `apps/frontend/` — React application
- `apps/backend/` — FastAPI application
- `ml/` — Model training and inference
- `knowledge_base/` — Maintenance document retrieval
- `docs/` — Technical documentation
- `scripts/` — Development and verification scripts
- `tests/` — Automated tests

## License

MIT License (planned).