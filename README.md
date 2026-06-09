# RALE Architect: Reliability-Audited Listening Exam Architect (Track 2)

## 1. Problem

RALE Architect addresses a specific failure mode in generative AI systems: multimodal outputs often look plausible but fail when text, image regions, coordinates, audio, captions, and assessment questions must all agree.

Our proving ground is map-listening assessment generation for educational publishing workflows. These tasks are unforgiving: a generated site map, labelled landmarks, walking-tour script, synchronized audio, captions, and multiple-choice questions must stay consistent.

Under baseline testing, standard LLM vision-extraction suffers from spatial and content drift:
* **Spatial Collisions:** Bounding boxes representing landmarks on generated site maps overlap or cluster too tightly.
* **Edge-Clipping:** Landmarks are pushed too close to the canvas boundaries, clipping during visual rendering.
* **Script Density:** The generated text fails to meet internal word-count targets required for a complete listening artefact.

The bottleneck is not raw generation. The bottleneck is the lack of deterministic validation, observable failure handling, and repair coordination around multimodal generation.

---

## 2. Our Solution

RALE Architect is a Track 2 Optimize project built around Google ADK orchestration. It takes an existing experimental generation pipeline and adds a cyclic Detect → Reject → Repair workflow for reliability.

The system uses six agent roles:
 1. **Artist Agent:** Generates the base map image using Imagen 4.0.
 2. **MQA Review Agent:** Performs an early visual quality gate on the generated map before downstream extraction and assessment generation.
 3. **Miner Agent:** Extracts spatial telemetry and landmark candidates from the generated map using a fast, cost-effective model (`gemini-2.5-flash`).
 4. **Auditor Agent:** Applies deterministic Geometry, Rubric, and Consistency (GRC) checks using Python logic (not LLM guessing). This includes coordinate boundaries, spacing rules, and script-density gates.
 5. **Playwright Agent:** Repairs rejected outputs. Powered by a higher-reasoning model (`gemini-2.5-pro`), it mathematically recalculates coordinates, expands scripts, and corrects inconsistencies based on explicit Auditor feedback.
 6. **Specialist Agent:** Generates the final assessment content, including the structured listening script and multiple-choice questions.

Rejected outputs are not silently accepted. They are routed back through repair, revalidated, and only then released as a complete, verified assessment package.

---

## 3. Track 2 Optimization & Empirical Reliability Curve

RALE is designed specifically for the Optimize track: an existing agentic prototype hardened through stress testing, observability, and repair loops. 

To empirically prove our architecture, we engineered a 300-run benchmark load-test (N=300):
* **Standard Baseline (100 Runs):** 140px spacing / 20px edge margin.
* **Robustness Regime (100 Runs):** 200px spacing / 40px edge margin.
* **Failure Boundary (100 Runs):** 260px spacing / 60px edge margin.

Every rejection, repair, and pass/fail decision is captured in a fully inspectable ADK trace and permanently logged to our Cloud SQL ledger.

---

## 4. Cost & Performance Discipline

RALE uses dynamic model routing to avoid utilizing the most expensive reasoning model on every step. 

* **Financials:** Cost-effective models (`gemini-2.5-flash`) handle first-pass generation and routine validation, while higher-reasoning repair (`gemini-2.5-pro`) is reserved strictly for complex rejected cases. This dynamic routing reduced estimated avoidable regeneration costs compared with full pipeline regeneration.
* **Performance:** By delegating the baseline to the faster Flash model, average completion time for successful first-pass runs is drastically reduced, protecting the user's time and only incurring higher latency when an edge-case repair is strictly necessary.

---

## 5. Technologies Used

Google Agent Development Kit (ADK): agent roles, workflow routing, context propagation, event traces, and rejection-to-repair flow.

Vertex AI / Gemini via google-genai SDK: Gemini model calls in the Cloud Run judging deployment using Application Default Credentials.

Imagen: generated visual artefacts for map-style assessment scenarios.

Google Cloud Text-to-Speech: audio narration for the listening artefact.

Cloud SQL / PostgreSQL: centralized benchmark and audit ledger for Cloud Run evaluation traces, validation attempts, and run outcomes.

Google Cloud Run: public judging deployment.

Docker, Gunicorn, Flask: containerized web application and demo interface.

SQLite: local-development fallback only.

---

## 6. Data Sources

RALE uses predefined thematic assessment scenarios, such as theme parks, wildlife parks, botanical gardens, campuses, and museum districts. These are synthetic demo scenarios designed to stress spatial reasoning, not private student data.

The Cloud Run judging demo records ADK events, validation attempts, repair outcomes, and benchmark results in Cloud SQL/PostgreSQL so concurrent Cloud Run instances write to one centralized audit ledger. SQLite is retained only as a local development fallback.

---

## 7. Replay and Test Disclosures

* **Live Cloud SQL Ledger:** The "Enterprise Audit" tab queries live production data from our Cloud SQL database to present auditable reliability, financial, and performance metrics across batch runs.
* **Fast Demo Replay:** The UI includes a toggle to use cached artefacts from a previously completed run so judges can instantly inspect a detect → repair → release flow. Live Generation is the default.
* **Spatial Stress Mode:** A UI toggle that injects stricter spatial constraints to deliberately trigger validation failures and demonstrate the Track 2 repair loop live.

---

## 8. Findings and Learnings

Our main finding was that prompt engineering alone is not enough for reliable multimodal assessment generation. First-pass outputs can look convincing while still failing geometry, rubric, schema, or content-consistency checks.

The most important improvement was fail-loud, deterministic validation: the Auditor utilizes hard Python math to reject incomplete or inconsistent outputs and passes explicit failure reasons back to the repair agent. This changed the workflow from “generate and hope” into a traceable, self-healing reliability loop.