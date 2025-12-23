# Docker setup for SenseAble demo

This folder contains containerization helpers for running the SenseAble backend.

Key files
- `Dockerfile` - image build instructions (uses repository root as build context).
- `docker-compose.yml` - development compose file that mounts the repository into the container.
- `Makefile` - convenience targets for building and running locally.

Environment
- The compose file reads environment variables from a `.env` file at the repository root. Do NOT commit secrets to the repository. Typical variables:
  - `AZURE_COPILOT_ENDPOINT` (optional)
  - `AZURE_COPILOT_API_KEY` (optional)
  - `AZURE_COPILOT_DEPLOYMENT` (optional)

Development usage

1. Create a `.env` file at the project root with any runtime variables you need (example below).
2. Build and run with docker-compose from the `docker/` directory:

```powershell
cd docker
docker-compose up --build
```

Or use the Makefile from the repository root:

```powershell
make docker-build
make docker-up
```

Example `.env` (DO NOT CHECK INTO SOURCE):

```
# Example .env
AZURE_COPILOT_ENDPOINT=
AZURE_COPILOT_API_KEY=
AZURE_COPILOT_DEPLOYMENT=
```

Notes
- The compose file mounts the repository into the container for live code edits during development. For production images, prefer building a static image without mounting the source.
- The Dockerfile sets `PYTHONPATH=/app` so the package can be imported directly. Keep secrets out of Dockerfiles and source control.
