# Configuration directory

This folder holds declarative YAML configuration used by the SenseAble demo. Files are intentionally simple and safe to keep in source control — do not populate them with secrets.

Files

- `personalization.yaml` — default Sensory Accessibility Fingerprint (SAF) dimensions and rewrite preferences.
- `azure.yaml` — placeholders for Azure-related configuration (subscription, endpoints, authentication). **Do not** put real secrets here; use environment variables instead.
- `models.yaml` — model selection and LLM settings. Deployment names and keys should be configured via environment variables or a secure secret store.
- `paths.yaml` — data and cache paths used by the app.
- `stg.yaml` — Sensory Translation Graph tuning parameters and cross-modal weights.
- `rag.yaml` — retrieval, reranking and fallback settings for RAG components.
- `demo.yaml` — demo personas and demo-mode flags.
- `agents.yaml` — agent roles, expected schemas and model assignments.

Guidance

- Never commit secrets into these files. Use a `.env` file, your OS environment, or a secrets manager.
- Override values at runtime by setting environment variables matching the logical name. For Azure credentials, prefer `AZURE_*` environment variables (for example, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`).
- For production deployments, load configuration from a secure secret store and avoid mounting the repository into the running container.

Loader

This repository includes a lightweight `loader.py` helper to read YAML files and perform minimal redaction and environment interpolation. It requires `pyyaml` to be installed in the environment.
