# SenseAble

SenseAble is a system for culturally aware, multisensory, and personalized text accessibility. The system adapts sensory-rich text into accessible alternatives while preserving meaning, cultural grounding, and user preferences.

This repository contains the implementation corresponding to the SenseAble system described in our system demonstration paper (link will be provided soon).

The backend implements:
- Sensory expression detection
- Zero-shot sensory difficulty scoring
- Cultural metaphor retrieval via retrieval-augmented generation
- Sensory Translation Graph (STG) traversal
- Multisensory reasoning and substitution
- Meaning-preserving constrained rewriting
- Persistent agentic memory with user-specific accessibility profiles

## Repository Structure

The backend code in this repository is organized into modular components aligned with the system architecture:
- api: FastAPI application and REST endpoints
- core: Core pipeline logic, agents, and reasoning modules
- evaluation: Automatic metrics and evaluation utilities
- config: YAML and JSON configuration files
- utils: Shared utilities for embeddings, logging, and text processing

## Running the Backend

1. Create a Python virtual environment
2. Install dependencies from requirements.txt
3. Configure model and agent settings in the config directory
4. Launch the FastAPI application

## Demo Mode

The public demo uses representative personas and cached interactions instead of live model calls (Due to organizational security, compliance, and data-governance constraints, the backend models (enterprise Azure deployments of GPT-5 and Agentic-Copilot services) cannot be exposed via a public interactive interface at this moment). This ensures that the demo faithfully reflects system behavior while respecting security and data-governance constraints.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.