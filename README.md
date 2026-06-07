# RALE Architect

RALE Architect is an autonomous, multi-agent orchestrator built with the Google Agent Development Kit (ADK) and Gemini 2.5. It demonstrates production-grade multi-step reasoning, logical debugging, and self-healing.

## Track 2: Optimize (Existing Agents)
This repository is tailored for Track 2 of the Google for Startups AI Agents Challenge (2026). It showcases:
- **Agent Simulation & Evaluation**: The validation loops automatically detect logic faults (e.g. bounding box overlaps on generated site maps).
- **Self-Healing (Playwright Agent)**: When the auditor rejects output, the Playwright Agent recalculates and repairs the math error dynamically.
- **Multimodal MQA Review**: An independent visual QA agent verifies image generations against required criteria before proceeding.
- **Observability**: A live visual DAG and event trace ledger exposes the entire multi-agent deliberation process to the user.

## Architecture
- **Agents**: Orchestrated using Google ADK and Gemini 2.5 Flash / Pro.
- **Frontend**: Clean, glassmorphism UI with real-time word-by-word karaoke audio synchronization for generated walking tours.
- **Deployment**: Configured for Google Cloud Run (stateless, horizontally scalable).

## Quickstart (Local)
1. Copy `.env.example` to `.env` and insert your `GOOGLE_API_KEY`.
2. Run `docker build -t rale-architect .`
3. Run `docker run -p 5050:5050 --env-file .env rale-architect`
4. Visit `http://localhost:5050`
