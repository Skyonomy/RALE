import os
import sys
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s")
logger = logging.getLogger(__name__)

# Set PYTHONPATH to /app inside the container
sys.path.insert(0, os.getcwd())

import database

def simulate_concurrent_worker(idx):
    thread_name = threading.current_thread().name
    logger.info(f"Worker {idx} starting database transaction stress sequence...")
    
    run_id = f"stress-run-{idx}-{uuid.uuid4().hex[:6]}"
    scenario = f"Stress Test Scenario {idx}"
    session_id = f"stress-session-{idx}"
    
    try:
        # Step 1: Write Run Initialized Row
        database.log_run(run_id, scenario)
        logger.info(f"Worker {idx} successfully logged Run row: {run_id}")
        
        # Step 2: Write Multiple ADK Events
        for ev_idx in range(5):
            database.log_adk_event(
                run_id=run_id, session_id=session_id, invocation_id=f"inv-{ev_idx}",
                event_id=f"ev-{idx}-{ev_idx}", author=f"agent-{idx}", event_type="Event",
                function_call_name="validate_multimodal_geometry",
                function_call_args=f'{{"test": "args-{ev_idx}"}}',
                function_response_name=None, function_response=None, final_response_flag=False
            )
        logger.info(f"Worker {idx} successfully logged 5 ADK events for run: {run_id}")
        
        # Step 3: Write Validation Attempt
        database.log_validation_attempt(run_id, 1, "PASSED", "All geometry checks cleared")
        logger.info(f"Worker {idx} successfully logged validation attempt for run: {run_id}")
        
        # Step 4: Update Run
        database.update_run(run_id, "SUCCESS", True, False)
        logger.info(f"Worker {idx} successfully updated Run row to SUCCESS: {run_id}")
        
        return True
    except Exception as e:
        logger.error(f"Worker {idx} crashed with OperationalError / Transaction Failure: {e}", exc_info=True)
        return False

def main():
    logger.info("Initializing SQLite Stress Database...")
    database.init_db()
    
    num_threads = 8
    logger.info(f"PROVING STABILITY: Spawning {num_threads} concurrent threads to write to SQLite simultaneously...")
    
    success_results = []
    with ThreadPoolExecutor(max_workers=num_threads, thread_name_prefix="StressWorker") as executor:
        futures = [executor.submit(simulate_concurrent_worker, i) for i in range(num_threads)]
        for f in futures:
            success_results.append(f.result())
            
    num_failures = success_results.count(False)
    logger.info("=================================")
    logger.info(f"STRESS TEST COMPLETE!")
    logger.info(f"Threads Spawned: {num_threads}")
    logger.info(f"Successful Tasks: {success_results.count(True)}/{num_threads}")
    logger.info(f"Failed Tasks: {num_failures}/{num_threads}")
    logger.info("=================================")
    
    if num_failures > 0:
        logger.error(f"FAIL: {num_failures} threads suffered a transaction write collision or OperationalError!")
        sys.exit(1)
    else:
        logger.info("SUCCESS: SQLite successfully handled all 8 simultaneous multi-threaded write workflows under WAL-mode!")
        sys.exit(0)

if __name__ == "__main__":
    main()
