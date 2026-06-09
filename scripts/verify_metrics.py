import os
import csv
import json
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("PROVING 5: Verifying that log-metrics no longer logs word_count=0 or anchor_count=0 on successful runs...")

# Ensure clean metrics file
csv_path = 'data/competition_metrics.csv'
if os.path.exists(csv_path):
    os.remove(csv_path)

app = create_app()
client = app.test_client()

# Case: successful run on first pass (recoveryTriggered=False), but frontend sends 0 for first-pass metrics
payload = {
    "mode": "NORMAL",
    "scenario": "A Prestigious University Campus",
    "firstPassWords": 0,
    "firstPassAnchors": 0,
    "recoveryTriggered": False,
    "finalWords": 320,
    "finalAnchors": 5,
    "duration": 18.5
}

response = client.post('/api/log-metrics', json=payload)
assert response.status_code == 200, "log-metrics request failed"

# Read generated CSV to verify first-pass metrics were correctly matched to final metrics (not 0!)
with open(csv_path, 'r', newline='') as f:
    reader = list(csv.reader(f))
    headers = reader[0]
    data_row = reader[1]
    
    # Headers are: Mode, Scenario, FirstPass_Words, FirstPass_Anchors, FirstPass_Status, Rejection_Reason, Recovery_Triggered, Final_Words, Final_Anchors, Final_Status, Failure_Type, Duration_Seconds
    first_pass_words_val = int(data_row[2])
    first_pass_anchors_val = int(data_row[3])
    final_words_val = int(data_row[7])
    final_anchors_val = int(data_row[8])
    
    logger.info(f"Logged Row: {data_row}")
    assert first_pass_words_val == 320, f"Expected 320, got {first_pass_words_val}"
    assert first_pass_anchors_val == 5, f"Expected 5, got {first_pass_anchors_val}"
    assert final_words_val == 320, f"Expected 320, got {final_words_val}"
    assert final_anchors_val == 5, f"Expected 5, got {final_anchors_val}"

logger.info("PROVED: Metric zeroes on successful first-pass runs are programmatically matched to final metrics, preventing zero logs in competition_metrics.csv!")
