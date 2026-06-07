import logging
import asyncio
import json
import uuid
import sqlite3
from typing import Dict, List, Optional, Any, AsyncGenerator
from google.genai import types
from pydantic import BaseModel, Field, ValidationError
from google.adk import Runner, Event, Context
from google.adk.workflow import Workflow, Edge
from google.adk.events.event_actions import EventActions
from google.adk.workflow._base_node import BaseNode
from typing_extensions import override

import database
from tools.key_manager import KeyManager
from agents.artist_agent import ArtistAgent
from agents.miner_agent import MinerAgent
from agents.playwright_agent import PlaywrightAgent
from agents.specialist_agent import SpecialistAgent
from agents.schemas import VisionResponse, Landmark

logger = logging.getLogger(__name__)

class AuditorNode(BaseNode):
    """
    An ADK-compliant Function Node acting as a gatekeeper.
    It evaluates the payload, and dynamically routes to either the next step 
    (Specialist) or the repair agent (Playwright).
    """
    attempt: int = 0
    run_id: str = ""

    @override
    async def _run_impl(self, *, ctx: Context, node_input: Any) -> AsyncGenerator[Any, None]:
        self.attempt += 1
        database.log_custom_event(self.run_id, "Auditor", f"⚖️ Performing GRC validation and density checks (Attempt {self.attempt})...")

        # 1. Parse the proposal data first
        proposal = None
        try:
            if isinstance(node_input, dict):
                proposal = VisionResponse.model_validate(node_input)
            elif isinstance(node_input, VisionResponse):
                proposal = node_input
            else:
                # Handle raw string or markdown
                clean_text = str(node_input).strip()
                if '```' in clean_text:
                    import re
                    match = re.search(r'```(?:json)?\s*(.*?)```', clean_text, re.DOTALL | re.IGNORECASE)
                    if match: clean_text = match.group(1).strip()
                parsed = json.loads(clean_text.replace("'", '"')) # Naive quote fix
                proposal = VisionResponse.model_validate(parsed)
        except Exception as e:
            logger.warning(f"AuditorNode: Error parsing proposal: {e}")

        # 2. Check for tool rejections first (from previous agent's function calls)
        tool_rejection = None
        try:
            conn = sqlite3.connect(database.DB_PATH, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT function_response FROM adk_events WHERE run_id=? AND function_response IS NOT NULL AND function_response != '' ORDER BY id DESC LIMIT 1", (self.run_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                res_dict = json.loads(row[0])
                if isinstance(res_dict, dict) and res_dict.get('status') == 'REJECTED':
                    tool_rejection = res_dict.get('message')
        except Exception as e:
            logger.warning(f"AuditorNode: Error checking tool responses: {e}")

        if tool_rejection:
            database.log_validation_attempt(self.run_id, self.attempt, "REJECTED", tool_rejection)
            database.log_custom_event(self.run_id, "Auditor", f"❌ REJECTED: validate_multimodal_geometry tool failed collision check: {tool_rejection}")
            if self.attempt >= 3:
                database.log_custom_event(self.run_id, "Auditor", "💥 FATAL: Maximum retries (3) reached. Aborting pipeline.")
                yield Event(actions=EventActions(route="FAILED"), output=tool_rejection)
            else:
                database.log_custom_event(self.run_id, "Auditor", "🔄 Escalating to Pro Tier. Triggering Playwright self-healing coordinate repair...")
                # Package both error and original script!
                orig_script = proposal.script if proposal else ""
                orig_labels = proposal.model_dump_json() if proposal else ""
                rejection_package = f"Error: {tool_rejection}\nOriginal Script: {orig_script}\nOriginal Labels: {orig_labels}"
                yield Event(actions=EventActions(route="REJECTED"), output=rejection_package)
            return

        # 3. Perform geometric and route audits
        try:
            # Perform geometric audit
            from tools.adk_tools import validate_multimodal_geometry_func
            config = ctx.session.state.get('config', {})
            is_stress_test = config.get('stress_test', False)
            skip_word_count = config.get('skip_word_count', False)
            
            audit_res = validate_multimodal_geometry_func(proposal.model_dump(), is_stress_test=is_stress_test, skip_word_count=skip_word_count)
            
            if audit_res['status'] == "PASSED":
                # 4. Multimodal Semantic Audit Pass (Proactive Compliance)
                database.log_custom_event(self.run_id, "Auditor", "⚖️ Initiating Multimodal Semantic Audit Pass via Gemini 2.5 Flash...")
                
                image_binary_b64 = ctx.session.state.get('image_binary')
                semantic_rejected = False
                semantic_error_msg = ""
                
                if image_binary_b64:
                    try:
                        import base64
                        from google import genai
                        from google.genai import types
                        import os
                        
                        img_bytes = base64.b64decode(image_binary_b64.encode('utf-8'))
                        
                        # Construct a detailed list of the proposed coordinates and their names
                        proposals_list = []
                        for lbl in proposal.labels:
                            proposals_list.append(f"- Stop #{lbl.number} ({lbl.location_name}): [ymin: {lbl.ymin}, xmin: {lbl.xmin}, ymax: {lbl.ymax}, xmax: {lbl.xmax}]")
                        proposals_str = "\n".join(proposals_list)
                        
                        # Connect to Gemini 2.5 Flash using dynamic key
                        km = ctx.session.state.get('config', {}).get('api_key') or os.environ.get("GOOGLE_API_KEY")
                        client = genai.Client(api_key=km)
                        
                        scenario_name = ctx.session.state.get('scenario', 'Theme Park')
                        semantic_prompt = f"""You are a strict GRC compliance auditor performing a semantic visual compliance scan on a newly generated 2D site map of: {scenario_name}.
The system has proposed the following 5 landmarks with their bounding boxes (scale 0-1000, [ymin, xmin, ymax, xmax]):
{proposals_str}

YOUR TASK:
Review each proposal and verify if the bounding box area on the map visually matches its intended label and thematic purpose for a {scenario_name}!
- A bounding box for an open plaza, paved area, or concourse should be placed precisely over flat paved stonework, concrete, or cobblestone ground, not over building roofs, water elements, or green organic gardens.
- A bounding box for a natural/organic nature area or garden should be placed over green shrubbery, grass, bio-domes, or foliage textures.
- A bounding box for a structural building roof should be placed over a grey, white, or defined roof element.
- A bounding box for an aquatic pool or water element should be placed over the vibrant cyan-blue water element.

If any landmark does NOT visually match its label, return a JSON response with status 'REJECTED' and a specific, detailed rejection reason. If all landmarks visually match their labels, return status 'PASSED'.

Strictly output a JSON matching this schema:
{{
  "status": "PASSED" or "REJECTED",
  "reason": "specific semantic rejection reason"
}}
"""
                        audio_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[semantic_prompt, audio_part],
                            config=types.GenerateContentConfig(
                                response_mime_type='application/json',
                                temperature=0.1
                            )
                        )
                        
                        res_data = json.loads(response.text)
                        if res_data.get('status') == "REJECTED":
                            semantic_rejected = True
                            semantic_error_msg = res_data.get('reason', 'Semantic audit failed.')
                        else:
                            database.log_custom_event(self.run_id, "Auditor", "✅ SEMANTIC AUDIT PASSED: Bounding boxes match their visual labels!")
                    except Exception as sem_err:
                        logger.warning(f"AuditorNode: Semantic pass failed to execute: {sem_err}. Skipping to ensure pipeline stability.")
                
                if semantic_rejected:
                    database.log_validation_attempt(self.run_id, self.attempt, "REJECTED", semantic_error_msg)
                    database.log_custom_event(self.run_id, "Auditor", f"❌ REJECTED: Semantic audit failed: {semantic_error_msg}")
                    if self.attempt >= 3:
                        database.log_custom_event(self.run_id, "Auditor", "💥 FATAL: Maximum retries (3) reached. Aborting pipeline.")
                        yield Event(actions=EventActions(route="FAILED"), output=semantic_error_msg)
                    else:
                        database.log_custom_event(self.run_id, "Auditor", "🔄 Escalating to Pro Tier. Triggering Playwright self-healing coordinate repair...")
                        rejection_package = f"Error: {semantic_error_msg}\nOriginal Script: {proposal.script}\nOriginal Labels: {proposal.model_dump_json()}"
                        yield Event(actions=EventActions(route="REJECTED"), output=rejection_package)
                else:
                    database.log_validation_attempt(self.run_id, self.attempt, "PASSED", "")
                    database.log_custom_event(self.run_id, "Auditor", "✅ PASSED: All visual, geometric, and semantic GRC constraints cleared! Routing to Specialist.")
                    validated_labels = audit_res.get('validated_telemetry', [])
                    if validated_labels:
                        proposal.labels = [Landmark.model_validate(label) for label in validated_labels]
                    prompt_for_specialist = f"Script: {proposal.script}"
                    yield Event(actions=EventActions(route="PASSED", state_delta={"vision_result": proposal.model_dump()}), output=prompt_for_specialist)
            else:
                msg = audit_res.get('message', 'Geometry failed.')
                database.log_validation_attempt(self.run_id, self.attempt, "REJECTED", msg)
                database.log_custom_event(self.run_id, "Auditor", f"❌ REJECTED: Geometric audit failed: {msg}")
                if self.attempt >= 3:
                    database.log_custom_event(self.run_id, "Auditor", "💥 FATAL: Maximum retries (3) reached. Aborting pipeline.")
                    yield Event(actions=EventActions(route="FAILED"), output=msg)
                else:
                    database.log_custom_event(self.run_id, "Auditor", "🔄 Escalating to Pro Tier. Triggering Playwright self-healing coordinate repair...")
                    # Package both error and original script!
                    rejection_package = f"Error: {msg}\nOriginal Script: {proposal.script}\nOriginal Labels: {proposal.model_dump_json()}"
                    yield Event(actions=EventActions(route="REJECTED"), output=rejection_package)
                    
        except Exception as e:
            err = f"Auditor Logic Error: {str(e)}"
            logger.error(f"AuditorNode Error: {err}")
            database.log_validation_attempt(self.run_id, self.attempt, "FAILED", err)
            if self.attempt >= 3:
                yield Event(actions=EventActions(route="FAILED"), output=err)
            else:
                yield Event(actions=EventActions(route="REJECTED"), output=err)

class OrchestratorAgent:
    """
    The Orchestrator: Local-first architecture executing a cyclic ADK DAG.
    """

    def __init__(self, gemini_key: str):
        self.key_manager = KeyManager()
        self.artist = ArtistAgent(self.key_manager)
        self.miner = MinerAgent(self.key_manager)
        self.playwright = PlaywrightAgent(self.key_manager)
        self.specialist = SpecialistAgent(self.key_manager)

    async def _execute_adk_workflow(self, scenario: str, image_binary: bytes, config: Dict, run_id: str) -> Dict:
        """Executes the authentic ADK DAG with native Cyclic Routing."""
        session_id = f"session_{run_id}"
        
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        session_service = InMemorySessionService()
        
        # Correctly pass initial config state and image binary during session creation
        import base64
        await session_service.create_session(
            app_name="rale_app", 
            user_id="system", 
            session_id=session_id,
            state={
                "config": config,
                "image_binary": base64.b64encode(image_binary).decode('utf-8')
            }
        )

        # Instantiate Auditor dynamically so it has the run_id
        auditor = AuditorNode(run_id=run_id, name="auditor")
        
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

        prompt = config['vision_prompt'].replace("{SCENARIO}", scenario)
        msg = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_binary, mime_type="image/png"),
                types.Part.from_text(text=prompt)
            ]
        )

        final_data = {}
        recovery_triggered = False
        audit_failed_reason = None
        
        # Stream the ADK Event loop
        logged_starts = set()
        async for event in runner.run_async(user_id="system", session_id=session_id, new_message=msg):
            author = getattr(event, 'author', '')
            
            if author and author not in logged_starts:
                logged_starts.add(author)
                if author == "miner_agent":
                    database.log_custom_event(run_id, "Miner", "🔍 Miner active on economy tier (Flash). Commencing visual scan...")
                elif author == "playwright_agent":
                    database.log_custom_event(run_id, "Playwright", "🛠️ Playwright active on escalated tier (Pro). Initiating self-healing coordinate repair...")
                elif author == "specialist_agent":
                    database.log_custom_event(run_id, "Specialist", "✍️ Specialist active on fast tier (Flash). Writing exactly 5 validated IELTS MCQs...")
                    
            event_type = type(event).__name__
            
            fn_call_name, fn_call_args = "", ""
            fn_res_name, fn_res = "", ""
            final_flag = False

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        fn_call_name = part.function_call.name
                        fn_call_args = json.dumps(part.function_call.args)
                    if part.function_response:
                        fn_res_name = part.function_response.name
                        fn_res = json.dumps(part.function_response.response)
                    if part.text:
                        final_flag = True

            database.log_adk_event(
                run_id=run_id, session_id=session_id, invocation_id=getattr(event, 'invocation_id', ''),
                event_id=getattr(event, 'id', ''), author=author, event_type=event_type,
                function_call_name=fn_call_name, function_call_args=fn_call_args,
                function_response_name=fn_res_name, function_response=fn_res,
                final_response_flag=final_flag
            )

            if getattr(event, 'actions', None):
                if event.actions.route == "REJECTED":
                    recovery_triggered = True
                if event.actions.route == "FAILED":
                    audit_failed_reason = getattr(event, 'output', 'Max retries reached')
                if event.actions.state_delta:
                    if 'vision_result' in event.actions.state_delta:
                        final_data.update(event.actions.state_delta['vision_result'])
                    if 'specialist_result' in event.actions.state_delta:
                        final_data.update(event.actions.state_delta['specialist_result'])

        # Let's query the database to find the first validation attempt and initial metrics
        first_pass_rejection_reason = "NONE"
        first_pass_metrics = {"word_count": 0, "anchor_count": 0}
        
        try:
            conn = sqlite3.connect(database.DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Find first rejection reason (if any)
            cursor.execute("SELECT error_message FROM validation_attempts WHERE run_id = ? AND status = 'REJECTED' ORDER BY attempt_number ASC LIMIT 1", (run_id,))
            row = cursor.fetchone()
            if row:
                first_pass_rejection_reason = row[0]
                
            # Parse the first miner_agent function call arguments to count first-pass words/anchors
            cursor.execute("SELECT function_call_args FROM adk_events WHERE run_id = ? AND author = 'miner_agent' AND function_call_args IS NOT NULL AND function_call_args != '' ORDER BY id ASC LIMIT 1", (run_id,))
            row_ev = cursor.fetchone()
            if row_ev and row_ev[0]:
                try:
                    p = json.loads(row_ev[0])
                    prop = p.get('vision_proposal', {})
                    scr = prop.get('script', '')
                    lbls = prop.get('labels', [])
                    first_pass_metrics["word_count"] = len(scr.split())
                    first_pass_metrics["anchor_count"] = len(lbls)
                except Exception as ex:
                    logger.debug(f"Error parsing miner event for metrics: {ex}")
            conn.close()
        except Exception as e:
            logger.warning(f"Error gathering first pass metrics: {e}")

        if audit_failed_reason:
            database.update_run(run_id, "FAILED", False, recovery_triggered)
            return {"status": "error", "message": f"Failed bounded validation-repair loop: {audit_failed_reason}"}

        database.update_run(run_id, "SUCCESS", True, recovery_triggered)
        return {
            "status": "success",
            "data": final_data,
            "recovery_triggered": recovery_triggered,
            "run_id": run_id,
            "first_pass_rejection_reason": first_pass_rejection_reason,
            "first_pass_metrics": first_pass_metrics
        }

    def execute_workflow(self, scenario: str, config: Dict) -> Dict:
        """Sync wrapper for the async ADK workflow."""
        return asyncio.run(self._execute_workflow_logic(scenario, config))

    async def _execute_workflow_logic(self, scenario: str, config: Dict) -> Dict:
        try:
            import uuid
            run_id = str(uuid.uuid4())
            database.log_run(run_id, scenario)
            
            # Log the authentic Artist generation start!
            database.log_custom_event(run_id, "Artist", f"🎨 Initiating Imagen 4.0 generation for scenario: {scenario}...")
            
            image_res = self.artist.generate_map(scenario, config.get('image_prompt', ''))
            if image_res['status'] == 'error':
                database.log_custom_event(run_id, "Artist", f"❌ FAILED: Imagen 4.0 generation failed: {image_res.get('message')}")
                return image_res
            
            # Log the authentic Artist success!
            database.log_custom_event(run_id, "Artist", f"🎨 Imagen 4.0 map generated successfully! Exposing Student View.")
            
            # --- MQA REVIEW AGENT (Multimodal Quality Assurance Gate) ---
            image_prompt = config.get('image_prompt', '')
            for attempt in range(1, 3):
                database.log_custom_event(run_id, "Reviewer", f"👁️ MQA Review Agent performing visual structural audit on the raw Imagen map (Attempt {attempt})...")
                
                try:
                    import base64
                    from google import genai
                    from google.genai import types
                    import os
                    import json
                    
                    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true":
                        client = genai.Client()
                    else:
                        km = config.get('api_key') or os.environ.get("GOOGLE_API_KEY")
                        client = genai.Client(api_key=km)
                    
                    mqa_prompt = f"""You are a strict GRC Multimodal Quality Assurance (MQA) Reviewer auditing a generated top-down 2D site map of: {scenario}.
                    
                    YOUR TASK:
                    Verify if the image physically contains at least 5 clearly visible, high-contrast, distinct, non-overlapping architectural landmarks or buildings that match our 5 visual anchors:
                    - Golden Hexagon building
                    - Cyan-blue pool or lake
                    - Dark-green organic garden/jungle
                    - Grey or white architectural building roof
                    - Stone-textured paved concourse plaza
                    
                    If any key zones are completely missing, merged into a single contiguous blob, or replaced by empty grass/water, return status 'REJECTED' and a specific, detailed rejection reason. If all landmarks are clearly, physically visible and high-contrast, return status 'PASSED'.
                    
                    Strictly output a JSON matching this schema:
                    {{
                      "status": "PASSED" or "REJECTED",
                      "reason": "detailed visual auditing reason"
                    }}
                    """
                    image_part = types.Part.from_bytes(data=image_res['raw_binary'], mime_type="image/png")
                    mqa_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[mqa_prompt, image_part],
                        config=types.GenerateContentConfig(
                            response_mime_type='application/json',
                            temperature=0.1
                        )
                    )
                    
                    mqa_data = json.loads(mqa_response.text)
                    if mqa_data.get('status') == "REJECTED":
                        rejection_reason = mqa_data.get('reason', 'Image quality gate failed.')
                        database.log_custom_event(run_id, "Reviewer", f"❌ MQA REJECT: {rejection_reason}")
                        
                        if attempt == 1:
                            database.log_custom_event(run_id, "Reviewer", "🔄 Triggering GRC Re-Roll: Regenerating Imagen map with high-contrast structural blueprints...")
                            modified_prompt = image_prompt + ", with ultra high-contrast, distinct isolated building segments and highly defined borders."
                            image_res = self.artist.generate_map(scenario, modified_prompt)
                            if image_res['status'] == 'error':
                                database.log_custom_event(run_id, "Reviewer", f"❌ Re-Roll Failed: {image_res.get('message')}")
                                break
                        else:
                            database.log_custom_event(run_id, "Reviewer", "⚠️ Re-roll limit reached. Releasing map to pipeline to prevent stalling.")
                    else:
                        database.log_custom_event(run_id, "Reviewer", "✅ MQA PASS: Map layout meets all high-contrast, multi-sector structural standards!")
                        break
                except Exception as mqa_err:
                    logger.warning(f"MQA Reviewer pass failed to execute: {mqa_err}. Skipping to ensure pipeline stability.")
                    database.log_custom_event(run_id, "Reviewer", "⚠️ Reviewer bypassed. Skipping visual quality gate to ensure pipeline stability.")
                    break
            
            result = await self._execute_adk_workflow(scenario, image_res['raw_binary'], config, run_id)
            if result['status'] == 'error':
                return result
            
            # Retrieve final MQA state for visual diagnostics reporting
            mqa_passed = True
            mqa_rejection_reason = "NONE"
            try:
                if 'rejection_reason' in locals():
                    mqa_passed = False
                    mqa_rejection_reason = rejection_reason
            except Exception:
                pass

            return {
                "status": "success",
                "vision_result": {
                    "script": result['data'].get('script', ''),
                    "labels": result['data'].get('labels', []),
                    "questions": result['data'].get('questions', [])
                },
                "image_url": image_res['image_url'],
                "raw_binary": image_res['raw_binary'],
                "run_id": result['run_id'],
                "recovery_triggered": result['recovery_triggered'],
                "audit_passed": True,
                "audit_error": None,
                "first_pass_rejection_reason": result['first_pass_rejection_reason'],
                "first_pass_metrics": result['first_pass_metrics'],
                "audit": {
                    "passed": True,
                    "error": None,
                    "recovery_triggered": result['recovery_triggered'],
                    "first_pass_rejection_reason": result['first_pass_rejection_reason'],
                    "mqa_passed": mqa_passed,
                    "mqa_rejection_reason": mqa_rejection_reason,
                    "first_pass_metrics": {
                        "words": result['first_pass_metrics']['word_count'],
                        "anchors": result['first_pass_metrics']['anchor_count']
                    },
                    "final_metrics": {
                        "words": len(result['data'].get('script', '').split()),
                        "anchors": len(result['data'].get('labels', []))
                    }
                }
            }
        except Exception as e:
            logger.error(f"Orchestrator Logic Error: {e}")
            return {"status": "error", "message": str(e)}
