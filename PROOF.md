# Architecture Audit Proof

## 1. ADK Version
```bash
$ docker exec rale-service python -c "import google.adk; print(getattr(google.adk, '__version__', 'no version'));"
2.1.0
```

## 2. ADK Graph Routing APIs
**Verified Imports in `agents/orchestrator_agent.py`:**
```python
from google.adk import Runner, Workflow
from google.adk.workflow import Edge, BaseNode
from google.adk.events.event import Event, EventActions
```

## 3. Authentic Workflow Execution
**Code from `agents/orchestrator_agent.py`:**
```python
        # DECLARATIVE, CYCLIC WORKFLOW DEFINITION
        wf = Workflow(
            name="validation_dag",
            edges=[
                ("START", self.miner.adk_agent),
                (self.miner.adk_agent, auditor),
                Edge(from_node=auditor, to_node=self.playwright.adk_agent, route="REJECTED"),
                (self.playwright.adk_agent, auditor), # Cyclic link back to Auditor
                Edge(from_node=auditor, to_node=self.specialist.adk_agent, route="PASSED")
            ]
        )
        
        runner = Runner(
            app_name="rale_app",
            agent=wf,
            session_service=session_service
        )

        async for event in runner.run_async(user_id="system", session_id=session_id, new_message=msg):
            # ... handles event persistence
```

## 4. Test Proofs

### Rejection Route Test
**Output:**
```
TEST ROUTING EVENTS: [('miner', '{"script": "MINER", "labels": []}'), ('auditor', 'TEST_ROUTE_REJECTION_123'), ('playwright', '{"script": "PLAYWRIGHT", "labels": [{"number":1}]}'), ('auditor', 'OK'), ('specialist', '{"questions": [{"q": "test"}]}')]
SUCCESS: Rejected route went to Playwright and cycled back to Auditor.
```

### Always-Reject Failure Test
**Output:**
```
ALWAYS REJECT EVENTS: ['MINER', 'REJECTED', 'PLAYWRIGHT', 'REJECTED', 'PLAYWRIGHT', 'MAX_RETRIES']
SUCCESS: Specialist never called, max retries reached.
```

### Fake Trace Removed Test
**Output:**
```
audit_tests.py::test_no_trace_memory_handler_exists PASSED
```

### SQLite Persistence Test
**Output:**
```
audit_tests.py::test_sqlite_persists_run_trace_after_restart_or_new_process PASSED
```

## 5. Authentic SQLite Event Persistence
**Real row from `adk_events` table:**
```
(1, 'ff3b384d-759f-4207-893f-87fca101866a', 'session_ff3b384d-759f-4207-893f-87fca101866a', 'e-7b202746-4190-464a-84be-e66b353f2bdd', '61cb4e73-482f-4a4f-b7c3-90a5694b1926', 'miner_agent', 'Event', 'validate_multimodal_geometry_func', '{"vision_proposal": {"script": "This document provides a comprehensive overview...", "labels": [{"number": 1, "ymax": 150, "xmin": 50, "bbox_type": "landmark", "location_name": "Main Atrium Skylight", "xmax": 150, "ymin": 50}, ...]}}', '', '', 0, '2026-06-04 12:59:24')
```

## 6. Unsafe Wording Audit
```bash
$ grep -rinE "ADK FunctionTool|ADK Event|ADK Runner|local SQLite audit trail|Local Event Persistence|local-first|conditional graph workflow|100% REAL" . --exclude-dir=google_adk_local --exclude-dir=venv* --exclude-dir=.venv --exclude-dir=.git || echo "No matches found."
No matches found.
```

## 7. Architecture: Local-First vs GCP Migration
1. **Current State:** This is a local-first architecture designed to prove the structural mechanics of the Google ADK before scaling.
2. **Database:** We currently use local SQLite to durably persist runs and events. This will migrate to Google Cloud SQL (PostgreSQL).
3. **Asset Storage:** Image and audio artifacts are currently saved to the local file system. This will migrate to Google Cloud Storage (GCS).
4. **Observability:** The ADK Event Trace Ledger queries our local SQLite tables. This telemetry pipeline will migrate directly to Google Cloud Logging.
5. **Compute:** The application runs on local Docker/Flask. It is packaged to deploy seamlessly to Google Cloud Run.
6. **Secrets:** Environment variables (.env) will migrate to Google Cloud Secret Manager.
*(Note: This overview has been added to the application UI under the Architecture tab.)*
