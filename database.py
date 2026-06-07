import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'adk_state.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    
    # Table for high-level runs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            scenario TEXT,
            status TEXT,
            audit_passed BOOLEAN,
            recovery_triggered BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for ADK events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adk_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            session_id TEXT,
            invocation_id TEXT,
            event_id TEXT,
            author TEXT,
            event_type TEXT,
            function_call_name TEXT,
            function_call_args TEXT,
            function_response_name TEXT,
            function_response TEXT,
            final_response_flag BOOLEAN,
            capture_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for validation attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validation_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            attempt_number INTEGER,
            status TEXT,
            error_message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def log_run(run_id, scenario):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO runs (run_id, scenario, status) VALUES (?, ?, ?)', (run_id, scenario, 'STARTED'))
    conn.commit()
    conn.close()

def update_run(run_id, status, audit_passed, recovery_triggered):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE runs 
        SET status = ?, audit_passed = ?, recovery_triggered = ?
        WHERE run_id = ?
    ''', (status, audit_passed, recovery_triggered, run_id))
    conn.commit()
    conn.close()

def log_adk_event(run_id, session_id, invocation_id, event_id, author, event_type, function_call_name, function_call_args, function_response_name, function_response, final_response_flag):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO adk_events 
        (run_id, session_id, invocation_id, event_id, author, event_type, function_call_name, function_call_args, function_response_name, function_response, final_response_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (run_id, session_id, invocation_id, event_id, author, event_type, function_call_name, function_call_args, function_response_name, function_response, final_response_flag))
    conn.commit()
    conn.close()

def log_validation_attempt(run_id, attempt_number, status, error_message):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO validation_attempts (run_id, attempt_number, status, error_message)
        VALUES (?, ?, ?, ?)
    ''', (run_id, attempt_number, status, error_message))
    conn.commit()
    conn.close()

def log_custom_event(run_id, author, message):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO adk_events 
        (run_id, author, event_type, function_call_args)
        VALUES (?, ?, ?, ?)
    ''', (run_id, author, 'Custom', message))
    conn.commit()
    conn.close()

def get_trace_logs(run_id=None, offset=0):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    if not run_id:
        cursor.execute('SELECT run_id FROM runs ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            run_id = row[0]
            
    if run_id:
        cursor.execute('SELECT capture_timestamp, author, event_type, function_call_name, function_response, function_call_args FROM adk_events WHERE run_id = ? ORDER BY id ASC', (run_id,))
    else:
        cursor.execute('SELECT capture_timestamp, author, event_type, function_call_name, function_response, function_call_args FROM adk_events ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        timestamp, author, event_type, fn_call, fn_res, fn_args = row
        message = ""
        if event_type == "Custom":
            message = fn_args
        elif fn_call:
            message = f"Called tool {fn_call}"
        elif fn_res:
            message = f"Tool returned: {fn_res}"
        elif event_type:
            message = f"Event: {event_type}"
        
        # Only log meaningful events for UI
        if message:
            logs.append({
                "time": timestamp,
                "agent": author,
                "message": message
            })
    return logs[offset:]
