import os
import json
import logging
import getpass
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, Text, event
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Determine Database URL (Default to ephemeral SQLite if not defined, otherwise Cloud SQL)
DB_URL = os.environ.get("POSTGRES_URL", "sqlite:///" + os.path.join(os.path.dirname(__file__), 'data', 'adk_state.db'))

# --- DIAGNOSTIC CHECKS ---
def run_db_diagnostics():
    try:
        resolved_path = DB_URL.replace("sqlite:///", "") if "sqlite" in DB_URL else "PostgreSQL Server"
        uid = os.getuid()
        user = getpass.getuser()
        
        logger.info("=== DB DIAGNOSTICS ===")
        logger.info(f"Resolved DB Connection String: {DB_URL}")
        logger.info(f"Resolved absolute DB path: {resolved_path}")
        logger.info(f"Current Process User: {user} (UID: {uid})")
        
        if "sqlite" in DB_URL:
            db_exists = os.path.exists(resolved_path)
            db_writable = os.access(resolved_path, os.W_OK) if db_exists else "N/A (File does not exist yet)"
            logger.info(f"DB File exists: {db_exists}")
            logger.info(f"DB File is writable: {db_writable}")
            
            parent_dir = os.path.dirname(resolved_path)
            parent_exists = os.path.exists(parent_dir)
            parent_writable = os.access(parent_dir, os.W_OK) if parent_exists else False
            logger.info(f"Parent data directory exists: {parent_exists}")
            logger.info(f"Parent data directory is writable: {parent_writable}")
        logger.info("======================")
    except Exception as e:
        logger.error(f"Error executing DB diagnostics: {e}")

# Run diagnostics at module import
run_db_diagnostics()

# Create Engine with hardened SQLite connection arguments if SQLite is used
if "sqlite" in DB_URL:
    engine = create_engine(
        DB_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
        pool_pre_ping=True,
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        
        # Log pragmas as requested
        cursor.execute("PRAGMA database_list;")
        db_list = cursor.fetchall()
        cursor.execute("PRAGMA journal_mode;")
        j_mode = cursor.fetchone()
        cursor.execute("PRAGMA synchronous;")
        sync = cursor.fetchone()
        
        logger.info(f"=== CONNECTED SQLite PRAGMAS ===")
        logger.info(f"PRAGMA database_list: {db_list}")
        logger.info(f"PRAGMA journal_mode: {j_mode}")
        logger.info(f"PRAGMA synchronous: {sync}")
        logger.info(f"=================================")
        
        cursor.close()
else:
    engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Run(Base):
    __tablename__ = "runs"
    run_id = Column(String, primary_key=True, index=True)
    scenario = Column(String)
    status = Column(String)
    audit_passed = Column(Boolean)
    recovery_triggered = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ADKEvent(Base):
    __tablename__ = "adk_events"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, index=True)
    session_id = Column(String)
    invocation_id = Column(String)
    event_id = Column(String)
    author = Column(String)
    event_type = Column(String)
    function_call_name = Column(String)
    function_call_args = Column(Text)
    function_response_name = Column(String)
    function_response = Column(Text)
    final_response_flag = Column(Boolean)
    capture_timestamp = Column(DateTime, default=datetime.utcnow)

class ValidationAttempt(Base):
    __tablename__ = "validation_attempts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, index=True)
    attempt_number = Column(Integer)
    status = Column(String)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    if "sqlite" in DB_URL:
        resolved_path = DB_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {DB_URL}")

def log_run(run_id, scenario):
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.run_id == run_id).first()
        if not run:
            new_run = Run(run_id=run_id, scenario=scenario, status='STARTED')
            db.add(new_run)
            db.commit()
    finally:
        db.close()

def update_run(run_id, status, audit_passed, recovery_triggered):
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.run_id == run_id).first()
        if run:
            run.status = status
            run.audit_passed = audit_passed
            run.recovery_triggered = recovery_triggered
            db.commit()
    finally:
        db.close()

def log_adk_event(run_id, session_id, invocation_id, event_id, author, event_type, function_call_name, function_call_args, function_response_name, function_response, final_response_flag):
    db = SessionLocal()
    try:
        event = ADKEvent(
            run_id=run_id, session_id=session_id, invocation_id=invocation_id,
            event_id=event_id, author=author, event_type=event_type,
            function_call_name=function_call_name, function_call_args=function_call_args,
            function_response_name=function_response_name, function_response=function_response,
            final_response_flag=final_response_flag
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

def log_validation_attempt(run_id, attempt_number, status, error_message):
    db = SessionLocal()
    try:
        attempt = ValidationAttempt(
            run_id=run_id, attempt_number=attempt_number,
            status=status, error_message=error_message
        )
        db.add(attempt)
        db.commit()
    finally:
        db.close()

def log_custom_event(run_id, author, message):
    db = SessionLocal()
    try:
        event = ADKEvent(
            run_id=run_id, author=author, event_type='Custom',
            function_call_args=message
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

def get_trace_logs(run_id=None, offset=0):
    db = SessionLocal()
    try:
        if not run_id:
            last_run = db.query(Run).order_by(Run.timestamp.desc()).first()
            if last_run:
                run_id = last_run.run_id
        
        query = db.query(ADKEvent)
        if run_id:
            query = query.filter(ADKEvent.run_id == run_id)
        
        events = query.order_by(ADKEvent.id.asc()).all()
        
        logs = []
        for event in events:
            message = ""
            if event.event_type == "Custom":
                message = event.function_call_args
            elif event.function_call_name:
                message = f"Called tool {event.function_call_name}"
            elif event.function_response:
                message = f"Tool returned: {event.function_response}"
            elif event.event_type:
                message = f"Event: {event.event_type}"
            
            if message:
                logs.append({
                    "time": event.capture_timestamp.isoformat() if event.capture_timestamp else None,
                    "agent": event.author,
                    "message": message
                })
        return logs[offset:]
    finally:
        db.close()

def get_first_pass_metrics(run_id):
    db = SessionLocal()
    try:
        first_pass_rejection_reason = "NONE"
        first_pass_metrics = {"word_count": 0, "anchor_count": 0}
        
        val_attempt = db.query(ValidationAttempt).filter(ValidationAttempt.run_id == run_id, ValidationAttempt.status == 'REJECTED').order_by(ValidationAttempt.attempt_number.asc()).first()
        if val_attempt:
            first_pass_rejection_reason = val_attempt.error_message
            
        miner_event = db.query(ADKEvent).filter(ADKEvent.run_id == run_id, ADKEvent.author == 'miner_agent', ADKEvent.function_call_args != None, ADKEvent.function_call_args != '').order_by(ADKEvent.id.asc()).first()
        if miner_event:
            try:
                p = json.loads(miner_event.function_call_args)
                prop = p.get('vision_proposal', {})
                scr = prop.get('script', '')
                lbls = prop.get('labels', [])
                first_pass_metrics["word_count"] = len(scr.split())
                first_pass_metrics["anchor_count"] = len(lbls)
            except Exception as ex:
                logger.debug(f"Error parsing miner event for metrics: {ex}")
                
        return first_pass_rejection_reason, first_pass_metrics
    finally:
        db.close()
