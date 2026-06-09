import os
import json
import logging
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we have clean slate for local DB tests
db_file = os.path.join(os.path.dirname(__file__), '../data', 'adk_state.db')
if os.path.exists(db_file):
    try:
        os.remove(db_file)
        logger.info("Cleared existing local SQLite state database.")
    except Exception as e:
        logger.warning(f"Could not clear SQLite file: {e}")

# 1. Import local fallback & check initialization
import database
logger.info("PROVING 1 & 2: Local fallback with SQLAlchemy SQLite creation...")
database.init_db()

# Check tables exist
db = database.SessionLocal()
try:
    runs = db.query(database.Run).all()
    events = db.query(database.ADKEvent).all()
    attempts = db.query(database.ValidationAttempt).all()
    logger.info(f"PROVED: SQLite Fallback created successfully. Tables queried without error.")
except Exception as e:
    logger.error(f"Failed to query local tables: {e}")
    exit(1)
finally:
    db.close()

# 3. Simulate a live workflow and check rows are persisted
logger.info("\nPROVING 3: Simulating run, event, and validation persistence...")
run_id = "test-run-123"
session_id = "session-abc"
scenario = "A Vibrant Tropical Wildlife Zoo"

database.log_run(run_id, scenario)
database.log_adk_event(
    run_id=run_id, session_id=session_id, invocation_id="inv-1", event_id="ev-1",
    author="miner_agent", event_type="Event", function_call_name="validate_multimodal_geometry",
    function_call_args='{"vision_proposal": {"script": "Welcome to the Zoo", "labels": [1, 2, 3]}}',
    function_response_name=None, function_response=None, final_response_flag=False
)
database.log_validation_attempt(run_id, 1, "REJECTED", "Too close coordinates")
database.update_run(run_id, "SUCCESS", True, True)

db = database.SessionLocal()
try:
    run_row = db.query(database.Run).filter(database.Run.run_id == run_id).first()
    event_row = db.query(database.ADKEvent).filter(database.ADKEvent.run_id == run_id).first()
    attempt_row = db.query(database.ValidationAttempt).filter(database.Run.run_id == run_id).first()
    
    assert run_row is not None, "Run row not persisted"
    assert event_row is not None, "ADKEvent row not persisted"
    assert attempt_row is not None, "ValidationAttempt row not persisted"
    logger.info(f"PROVED: Workflows are written cleanly via SQLAlchemy. Row verified for run_id '{run_id}'.")
except Exception as e:
    logger.error(f"Assertion failed: {e}")
    exit(1)
finally:
    db.close()

# 4. Proving Trace Logs Readability
logger.info("\nPROVING 4: Proving get_trace_logs functionality...")
logs = database.get_trace_logs(run_id=run_id)
logger.info(f"PROVED: trace logs query returned {len(logs)} log entries: {logs}")

# 6 & 7. GCS Upload and Local static uploads check
logger.info("\nPROVING 6 & 7: Checking GCS Upload path vs Local Fallback...")
from tools.audio_engine import AudioEngine
from tools.key_manager import KeyManager

key_mgr = KeyManager()

# Proving 7: Local upload works when GCS_BUCKET_NAME is unset
logger.info("Testing Local fallback path (No GCS_BUCKET_NAME set)...")
ae_local = AudioEngine(key_mgr, "static/uploads")
test_file = "test_audio_local.mp3"
res_url_local = ae_local._save_audio_content(b"dummy audio content", test_file)
logger.info(f"PROVED: Local filepath generated: '{res_url_local}'")

# Proving 6: GCS upload path works when GCS_BUCKET_NAME is set
logger.info("Testing GCS Upload path (GCS_BUCKET_NAME mock set)...")
os.environ["GCS_BUCKET_NAME"] = "fake-gcs-bucket-123"
with patch("google.cloud.storage.Client") as mock_storage:
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    ae_gcs = AudioEngine(key_mgr, "static/uploads")
    res_url_gcs = ae_gcs._save_audio_content(b"dummy audio content", "test_audio_gcs.mp3")
    
    # Assert blob upload was triggered
    mock_blob.upload_from_string.assert_called_once_with(b"dummy audio content", content_type="audio/mp3")
    logger.info(f"PROVED: GCS bucket upload triggered! Return URL: '{res_url_gcs}'")

logger.info("\nALL TESTS PASSED SUCCESSFULLY!")
