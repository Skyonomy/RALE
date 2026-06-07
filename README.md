# RALE Architect: Track 2 Optimization for Multimodal Assessment Reliability

## 1. Problem

RALE Architect addresses a specific failure mode in generative AI systems: multimodal outputs often look plausible but fail when text, image regions, coordinates, audio, captions, and assessment questions must all agree.

Our proving ground is IELTS-style map listening assessment generation for Gradence and B2B educational publishing workflows. These tasks are unforgiving: a generated site map, labelled landmarks, walking-tour script, synchronized audio, captions, and multiple-choice questions must stay consistent. If a landmark is clipped, a route contradicts the map, a script is too short, or a question refers to the wrong location, the artefact needs human repair.

The bottleneck is not raw generation. The bottleneck is the lack of deterministic validation, observable failure handling, and repair coordination around multimodal generation.

---

## 2. Our Solution

RALE Architect is a Track 2 Optimize project built around Google ADK orchestration. It takes an existing experimental generation pipeline and adds a cyclic **Detect → Reject → Repair** workflow for reliability.

The system uses five agent roles:
1.  **Miner Agent:** extracts spatial telemetry and landmark candidates from generated visual artefacts.
2.  **Specialist Agent:** generates the assessment content, including structured listening script and question material.
3.  **Auditor Agent:** applies **Geometry, Rubric, and Consistency (GRC)** checks, including coordinate boundaries, spacing rules, route sanity checks, schema validation, and script-density gates.
4.  **Playwright Agent:** repairs rejected outputs by recalculating coordinates, expanding scripts, or correcting route/landmark inconsistencies.
5.  **MQA Review Agent:** performs a final multimodal quality gate before release.

Rejected outputs are not silently accepted. They are routed back through repair, revalidated, and only then released as a complete, verified assessment package.

---

## 3. Track 2 Optimization

RALE is designed specifically for the Optimize track: an existing agentic prototype hardened through stress testing, observability, and repair loops.

*   **Spatial Stress Mode:** Deliberately applies stricter geometry and script-density constraints to trigger failures and demonstrate the recovery path.
*   **Observability HUD:** Shows the ADK event flow, rejection reasons, repair routes, and final validation results live on screen.

This lets judges see the complete before/after reliability story: the first-pass artefact fails validation, the system explains why, the repair agent fixes it, and the final map, script, audio, captions, and MCQs are released.

---

## 4. Cost Discipline

RALE uses model routing to avoid using the most expensive reasoning model on every step. Cost-effective models handle first-pass generation and routine validation, while higher-reasoning repair is reserved for complex rejected cases.

In evaluation runs, this reduced estimated per-run cost compared with an all-Pro baseline while preserving the Auditor’s validation pass criteria.

---

## 5. Technologies Used

-   **Google Agent Development Kit (ADK):** agent roles, workflow routing, context propagation, event traces, and rejection-to-repair flow.
-   **Vertex AI / Gemini via google-genai SDK:** Gemini model calls in the Cloud Run judging deployment using Application Default Credentials.
-   **Imagen:** generated visual artefacts for map-style assessment scenarios.
-   **Google Cloud Text-to-Speech:** audio narration for the listening artefact.
-   **Google Cloud Run:** public judging deployment.
-   **Docker, Gunicorn, Flask:** containerized web application and demo interface.
-   **SQLite:** session-local trace capture for the judging prototype.

---

## 6. Data Sources

RALE uses predefined thematic assessment scenarios, such as theme parks, wildlife parks, botanical gardens, campuses, and museum districts. These are synthetic demo scenarios designed to stress spatial reasoning, not private student data.

The Cloud Run judging demo uses ephemeral SQLite for session-local ADK trace capture and fast live observability. The core detect → validate → repair workflow runs end-to-end. Production persistence for Gradence would externalize traces and generated artefacts to managed Google Cloud services such as Cloud SQL and Cloud Storage.

---

## 7. Replay and Test Disclosures

*   **Fast Demo Replay:** Uses cached artefacts from a previously completed RALE run so judges can inspect the full detect → repair → release flow without waiting for live model generation. Live ADK Generation is also available and runs the full pipeline end-to-end.
*   **Spatial Stress Mode:** Injects stricter spatial and script-density constraints to deliberately trigger validation failures and demonstrate the Track 2 repair loop.

---

## 8. Findings and Learnings

Our main finding was that prompt engineering alone is not enough for reliable multimodal assessment generation. First-pass outputs can look convincing while still failing geometry, rubric, schema, or content-consistency checks.

The most important improvement was fail-loud validation: the Auditor rejects incomplete or inconsistent outputs and passes explicit failure reasons back to the repair agent. This changed the workflow from “generate and hope” into a traceable, self-healing reliability loop.

---

## 9. Future Applications

RALE is demonstrated in education because assessment generation has low tolerance for mismatch between visual artefacts and language content. The same architectural pattern can extend to other schematic-heavy workflows where generated visual layouts must remain consistent with text and metadata, such as training diagrams, facility maps, operational walkthroughs, and internal compliance documentation.
