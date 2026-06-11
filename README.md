# RALE Architect: Reliability-Audited Listening Exam Architect (Track 2)

RALE’s contribution is not another prompt template for generating listening tests. Its contribution is a reliability layer around multimodal generation: deterministic validation, explicit rejection reasons, targeted repair, model escalation only when needed, and a Cloud SQL audit ledger showing every pass, rejection, repair, and final outcome.

## 1. Problem

RALE Architect addresses a specific failure mode in generative AI systems: multimodal outputs often look plausible but fail when text, image regions, coordinates, audio, captions, and assessment questions must all agree.

Our proving ground is map-listening assessment generation for educational publishing workflows. These tasks are unforgiving: a generated site map, labeled landmarks, walking-tour script, synchronized audio, captions, and multiple-choice questions must stay consistent.

Under baseline testing, standard LLM vision-extraction suffers from spatial and content drift:
* **Spatial Collisions:** Bounding boxes representing landmarks on generated site maps overlap or cluster too tightly.
* **Edge-Clipping:** Landmarks are pushed too close to the canvas boundaries, clipping during visual rendering.
* **Script Density:** The generated text fails to meet internal word-count targets required for a complete listening artifact.

The bottleneck is not raw generation. The bottleneck is the lack of deterministic validation, observable failure handling, and repair coordination around multimodal generation.

---

## 2. Our Solution

RALE Architect is a Track 2 Optimize project built around Google ADK orchestration. It takes an existing experimental generation pipeline and adds a cyclic Detect → Reject → Repair workflow for reliability.

The system executes a six-role workflow:

1. **Artist Agent:** Generates the base map image using Imagen 4.0.
2. **MQA Review Agent:** Performs an early visual quality gate on the generated map.
3. **Miner Agent:** Extracts spatial telemetry and landmark candidates using gemini-2.5-flash.
4. **Auditor Agent:** Applies deterministic Geometry, Rubric, and Consistency checks using Python logic.
5. **Playwright Agent:** Repairs coordinate proposals using gemini-2.5-pro and explicit Auditor feedback.
6. **Specialist Agent:** Generates the final listening script and multiple-choice questions.

Rejected outputs are not silently accepted. They are routed back through repair, revalidated, and only then released as a complete, verified assessment package.

RALE does not compete by generating prettier artifacts; it competes by making multimodal generation measurable, rejectable, repairable, and auditable.

---

## 3. Track 2 Optimization & Empirical Reliability Curve

RALE is designed specifically for the Optimize track: an existing agentic prototype hardened through stress testing, observability, and repair loops. 

Using Agent Simulation, we proved prompt engineering alone fails at multimodal logic. Across 474 evaluation runs, RALE’s self-healing loop drove measured reliability gains:

* **Baseline Conditions (262 runs):** 56.1% → 95.8%
* **Robustness Testing (100 runs):** 49.0% → 95.0%
* **Failure Boundary (112 runs):** 17.0% → 83.0%

Every rejection, repair, and pass/fail decision is captured in a fully inspectable ADK trace and persisted to Cloud SQL.

---

## 4. Empirical Results

Across the final Cloud SQL evaluation batch of 474 runs, RALE Architect proved that its Detect → Reject → Repair workflow works under extreme constraint. 

At the failure boundary, only 17.0% of generations passed on the first attempt. After validator-guided repair, final validated success increased to 83.0%. These results are recorded in the Cloud SQL audit ledger and can be inspected through the Enterprise Audit view in the UI.

---

## 5. Cost & Performance Discipline

RALE uses dynamic model routing to avoid utilizing the most expensive reasoning model on every step. 

* **Financials:** Cost-effective models (`gemini-2.5-flash`) handle first-pass generation and routine validation, while higher-reasoning repair (`gemini-2.5-pro`) is reserved strictly for complex rejected cases. This dynamic routing reduced estimated avoidable regeneration costs compared with full pipeline regeneration.
* **Honesty on Costs:** Cost figures are path-based estimates. RALE compares targeted repair against full pipeline regeneration, not token-metered billing. This keeps the cost claim auditable and avoids overstating precision.
* **Performance:** By delegating the baseline to the faster Flash model, average completion time for successful first-pass runs is reduced, protecting the user's time and only incurring higher latency when an edge-case repair is strictly necessary.

---

## 6. Technologies Used

* **Google Agent Development Kit (ADK):** agent roles, workflow routing, context propagation, event traces, and rejection-to-repair flow.
* **Vertex AI / Gemini via google-genai SDK:** Gemini model calls (`gemini-2.5-flash` and `gemini-2.5-pro`) in the Cloud Run judging deployment using Application Default Credentials (ADC).
* **Imagen:** generated visual artifacts for map-style assessment scenarios.
* **Google Cloud Text-to-Speech:** audio narration for the listening artifact.
* **Cloud SQL / PostgreSQL:** centralized benchmark and audit ledger for Cloud Run evaluation traces, validation attempts, and run outcomes.
* **Google Cloud Run:** public judging deployment.
* **Docker, Gunicorn, Flask:** containerized web application and demo interface.
* **SQLite:** local-development fallback only.

---

## 7. Data Sources

RALE uses predefined thematic assessment scenarios, such as theme parks, wildlife parks, botanical gardens, campuses, and museum districts. These are synthetic demo scenarios designed to stress spatial reasoning, not private student data.

The Cloud Run judging demo records ADK events, validation attempts, repair outcomes, and benchmark results in Cloud SQL/PostgreSQL so concurrent Cloud Run instances write to one centralized audit ledger. SQLite is retained only as a local development fallback.

---

## 8. Replay and Test Disclosures

* **Live Cloud SQL Ledger:** The "Enterprise Audit" tab queries live production data from our Cloud SQL database to present auditable reliability, financial, and performance metrics across batch runs.
* **Fast Demo Replay:** The UI includes a toggle to use cached artifacts from a previously completed run so judges can instantly inspect a detect → repair → release flow. Live Generation is the default.
* **Spatial Stress Mode:** A UI toggle that injects stricter spatial constraints (260px safety buffers) to deliberately trigger validation failures and demonstrate the Track 2 repair loop live.

---

## 9. What to Try in the Demo

- **Run Live Generation** to see the full ADK pipeline execute end-to-end.
- **Toggle Spatial Stress Mode** to increase geometric difficulty and trigger the repair path.
- **Open the Enterprise Audit tab** to inspect Cloud SQL-backed reliability, repair, and cost metrics.
- **Use Fast Demo Replay** to inspect a cached repaired run without waiting for live model generation.
- **Compare Student View and Agent/Audit View** to see how the same artifact is presented before and after validation.

---

## 10. Findings and Learnings

Our main finding was that prompt engineering alone is not enough for reliable multimodal assessment generation. First-pass outputs can look convincing while still failing geometry, rubric, schema, or content-consistency checks.

The most important improvement was fail-loud, deterministic validation: the Auditor utilizes hard Python math to reject incomplete or inconsistent outputs and passes explicit failure reasons back to the repair agent. This changed the workflow from “generate and hope” into a traceable, self-healing reliability loop.

---

## 11. Future Applications

The RALE architecture is directly applicable to any high-stakes multimodal workflow where visual and textual elements must align, such as:
* Automated floor plan and safety script generation.
* Scientific diagrams with corresponding textbook descriptions.
* Technical manual illustrations with synchronized instructional audio.
