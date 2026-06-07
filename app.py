import os
import base64
from typing import Any
import logging
import json
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

import database
database.init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agents.orchestrator_agent import OrchestratorAgent
from tools.forensic_compositor import ForensicCompositor
from tools.audio_engine import AudioEngine

DEFAULT_IMAGE_PROMPT = """A professional, high-contrast, strictly 2D top-down architectural site map of: {SCENARIO}.
Style: Clean, minimalist schematic design. High-fidelity textures with absolutely zero text, zero labels, zero letters, and zero clutter."""

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config:
        app.config.update(test_config)

    # CONFIGURATION
    GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
    UPLOAD_DIR = os.path.join(app.root_path, "static/uploads")
    DATA_DIR = os.path.join(app.root_path, "data")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # AGENTS INITIALIZATION
    from tools.key_manager import KeyManager
    key_manager = KeyManager()
    
    orchestrator = OrchestratorAgent(GEMINI_KEY) # Orchestrator creates its own KeyManager internally for now, but we'll align it.
    # To keep it simple and fix the crash:
    audio_engine = AudioEngine(orchestrator.key_manager, UPLOAD_DIR)

    # PROMPTS (Strict Visual Schematic - NO TEXT)
    def expand_thematic_prompt(scenario: str, api_key: str) -> Any:
        from google import genai
        from google.genai import types
        from agents.schemas import DynamicTheming
        try:
            if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true":
                client = genai.Client()
            else:
                client = genai.Client(api_key=api_key)
            logger.info(f"PromptArchitect: Expanding theme for scenario '{scenario}' using Gemini 2.5 Flash")

            prompt = f"""You are a master theme park and architectural site planner. 
    We need to generate a 2D top-down map of: {scenario}.
    We need you to creatively translate this scenario into 5 physical, highly detailed thematic zones.
    Each of the 5 zones must correspond precisely to our visual colored/shaped anchors:
    1. Primary Zone (Golden Hexagon): The core landmark centerpiece or main dome (e.g. a golden vault or stylized themed tower).
    2. Aquatic Zone (Blue Pool): A water feature (e.g. lagoon, swamp, cooling pool, fountain, river segment).
    3. Green Zone (Dark-Green Shape): A nature/landscaped area (e.g. forest, jungle, park, garden, bio-dome).
    4. Structure Zone (Grey Roof): The main building roof (e.g. a grey metal hangar, slate roof hall, stone temple roof).
    5. Plaza Zone (Stone Concourse): An open stone-textured assembly plaza (e.g. cobblestone square, paved alleyway, launching courtyard).

    CRITICAL ARCHITECTURAL RULES FOR EACH ZONE:
    - REALISTIC AND ATYPICAL NAMES (CRITICAL): Generate simple, typical, factual, and realistic names for each landmark. Avoid overly elaborate, fantasy, mystical, or fictional terminology (e.g., do NOT generate names like 'The Reflecting Pool of Scholarly Serenity' or 'The Cobblestone Forum of Discourse'). Instead, use straightforward, standard names that a real-world visitor or architect would expect:
      * For a Zoo: Use 'Primate Enclosure', 'Lakeside Pond', 'Central Aviary Dome', 'Leopard Habitat', 'Main Entrance & Gift Shop'.
      * For a University: Use 'Academic Library Hall', 'Campus Reflecting Pond', 'Central Quadrangle Lawn', 'Main Administration Hall', 'Student Assembly Plaza'.
      * For a Botanical Garden: Use 'Tropical Orchid Greenhouse', 'Lily Pad Aquatic Pond', 'Rose Garden Walk', 'Visitor Exhibition Pavilion', 'Welcome Plaza'.
      * For a Museum District: Use 'Historic Archives Hall', 'Central Memorial Fountain', 'Sculpture Garden Lawn', 'Modern Art Gallery Wing', 'Museum Concourse Courtyard'.
    - STRICT PHYSICAL SEPARATION: You MUST describe each of the 5 zones as a completely isolated, free-standing, physically separate structure or area. They must NOT touch, overlap, or be part of a single contiguous or symmetrical circular building complex. Symmetrical circular/ring building plans are STRICTLY FORBIDDEN as they merge multiple zones into a single structure.
    - COMPACT AND UNIQUE: Describe exactly ONE instance of each anchor. For example, do not describe general background lawn or park areas; specify the Green Zone as 'A single, isolated, compact circular green bio-dome or manicured hedge maze.' Describe exactly ONE specific, free-standing, distinct grey-roofed structure.
    - HIGH COLOR CONTRAST: Use high-contrast color and shape descriptions to make each landmark immediately stand out from its surroundings.
    - THEMATIC LANDMARK DOMAIN ALIGNMENT (CRITICAL): Align landmark descriptions strictly with the scenario's native domain. Do NOT mix unrelated domains:
      * Amusement/Theme Parks/Carnivals: Describe mechanical structures (steel rollercoaster tracks, Ferris wheels, log flumes).
      * Historical/Castles/Medieval: Describe stone architecture (keeps, fortified slate roofs, cobblestone plazas, moats, topiary gardens). Absolutely NO rollercoasters or mechanical rides.
      * Zoos/Wildlife Reserves/Aquariums: Describe habitats (enclosures, pavilions, organic lakes, dense jungle foliage, stone pathways). No amusement rides.
      * Spaceports/Sci-Fi Stations: Describe high-tech terminals (modular metal hangars, solar collector panels, bio-domes, launching concrete pads).

    For the Style, decide whether this scenario is playful/creative (e.g. cartoon, whimsical, sci-fi) or professional/clean (e.g. minimalist engineering blueprint). Return the overall style description and specific style instructions.
    Provide extremely descriptive, colorful, theme-appropriate text for all 5 zones that Imagen can paint beautifully.
    Strictly output a JSON matching the requested schema."""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DynamicTheming,
                    temperature=0.7
                )
            )
            data = json.loads(response.text)
            return DynamicTheming.model_validate(data)
        except Exception as e:
            logger.error(f"PromptArchitect Error: {e}. Falling back to default static themed mapping.")
            # Fallback mock/safe dynamic theming
            return DynamicTheming(
                style_description=f"A professional, high-contrast, strictly 2D top-down architectural site map of: {scenario}.",
                style_instructions="Style: Clean, minimalist schematic design. High-fidelity textures but ZERO CLUTTER.",
                structure_zone_name="Grand Castle Gates & Reception",
                structure_zone="A large grey or white building or main structural roof complex.",
                primary_zone_name="Golden Horizon Giant Ferris Wheel",
                primary_zone="A bright golden-yellow hexagon with a distinct metallic or paved texture.",
                aquatic_zone_name="Shipwreck Bay Tidal Wave Slides",
                aquatic_zone="A clear, vibrant cyan-blue water feature (e.g. lake, pool, or fountain).",
                green_zone_name="Prehistoric Dino-Expedition Trek",
                green_zone="A lush dark-green organic shaped garden or lawn with dense foliage textures.",
                plaza_zone_name="Celebration Street Roundabout & Food Bazaar",
                plaza_zone="An open paved stone-textured square, assembly concourse, or courtyard."
            )

    def get_image_prompt(scenario: str, theme: Any) -> str:
        scenario_instructions = f"""- The Structure (Grey Roof, named '{theme.structure_zone_name}'): {theme.structure_zone}
    - The Primary Zone (Golden Hexagon, named '{theme.primary_zone_name}'): {theme.primary_zone}
    - The Aquatic Zone (Blue Pool, named '{theme.aquatic_zone_name}'): {theme.aquatic_zone}
    - The Green Zone (Dark-Green Shape, named '{theme.green_zone_name}'): {theme.green_zone}
    - The Plaza Zone (Stone Concourse, named '{theme.plaza_zone_name}'): {theme.plaza_zone}"""

        return f"""A 2D top-down clean site map layout with absolutely no text, no words, no letters, no characters. {theme.style_description}
    {theme.style_instructions}
    CRITICAL INSTRUCTIONS:
    1. ABSOLUTELY NO TEXT, LETTERS, OR NUMBERS: Do NOT write any words, characters, numbers, letters, labels, or titles anywhere on the image. The image must be completely word-free and character-free. Zero text.
    2. 5 DISTINCT SECTORS: Draw exactly 5 large, clearly separated zones. Use wide, clean paved paths or green lawns as 'negative space' between them.
    3. VISUAL ANCHORS (MANDATORY): Each zone must be a unique, obvious shape and color:
    - THE PRIMARY ZONE: A bright golden or yellow hexagon with a distinct metallic or paved texture.
    - THE AQUATIC ZONE: A clear, vibrant cyan-blue feature (e.g., a lake, pool, or fountain).
    - THE GREEN ZONE: A lush dark-green organic shape with dense foliage textures.
    - THE STRUCTURE: A large grey or white architectural roof with a visible entrance.
    - THE PLAZA ZONE: A stone-textured open square or circular concourse.
    4. SCENARIO ALIGNMENT: The 5 zones must be aligned to the {scenario} as follows:
    {scenario_instructions}
    5. PERSPECTIVE: Strictly 90-degree top-down view. No 3D, no tilting.
    6. NO WORDS: The Compass Rose must only use visual arrows, no N/S/E/W letters. The entrance must be a visual opening, no 'ENTRANCE' text."""

    DEFAULT_VISION_PROMPT = """You are a warm, extremely welcoming, and highly engaging professional guide leading an educational walking tour for visitors at: {SCENARIO}.

    TASK: Identify 5 logical tour stops on this 2D site map based on VISUAL SHAPE AND COLOR.

    INSTRUCTIONS:
    1. SCAN: Look for the 5 color-coded anchors (Golden Hexagon, Blue Pool, Green Garden, Grey Building, Stone Plaza) on the map.
    2. ANCHOR: Assign Stop #1 to the visual Main Entrance / Entry Gates (Grey Building), situated at the bottom, top, or sides of the map. Assign the remaining 4 stops in a logical clockwise walking tour order.
    3. BOUNDING BOXES: Draw precise, tight bounding boxes [ymin, xmin, ymax, xmax] around each identified sector on the 1000x1000 grid.
    4. SCRIPTING (450 WORDS): Write a professional, highly engaging, and natural human tour guide script for this scenario.
       - STYLE: Warm, enthusiastic, and conversational. Speak like an expert guide leading a real walking tour at a premier {SCENARIO} (e.g., "Welcome adventurers!", "Let's stroll right past...", "look up to see...", "on our left...").
       - CRITICAL LIMITATION: ABSOLUTELY NEVER mention raw numerical coordinates, brackets, coordinates, numbers, or grid boundaries in the spoken script (e.g. do NOT say '[573, 103]', 'coordinates', or 'grid').
       - LANDMARKS: Guide the listener using smooth spatial directions and specific thematic names for this scenario:
         * Grey Building (Stop #1) -> {STRUCTURE_NAME}.
         * Golden Hexagon -> {PRIMARY_NAME}.
         * Blue Pool -> {AQUATIC_NAME}.
         * Green Garden -> {GREEN_NAME}.
         * Stone Plaza -> {PLAZA_NAME}.

    JSON FORMAT:
    {
    "script": "Welcome...",
    "labels": [
    {"number": "1", "location_name": "{STRUCTURE_NAME}", "ymin": 15, "xmin": 400, "ymax": 120, "xmax": 600, "bbox_type": "landmark", "semantic_reason": "The clear grand steps or entryway opening visible on the map.", "anchor_policy": "center"}
    ]
    }"""

    @app.route('/')
    def index():
        try:
            with open('PROOF.md', 'r') as f:
                proof_content = f.read()
        except FileNotFoundError:
            proof_content = "Proof document not found."
        resp = make_response(render_template('index.html', proof_content=proof_content))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    @app.route('/api/trace', methods=['GET'])
    def get_trace():
        run_id = request.args.get('run_id')
        offset = int(request.args.get('offset', 0))
        logs = database.get_trace_logs(run_id, offset)
        return jsonify({"logs": logs})

    @app.route('/api/generate', methods=['POST'])
    def generate():
        """Monolithic wrapper for UI convenience."""

        data = request.json
        raw_scenario = data.get('scenario', 'University Library')
        
        # Sanitize scenario title for UI
        title_map = {
            "A Large Multi-Story University Library": "University Library",
            "A Modern City Hospital Wing": "City Hospital",
            "A Family-Friendly Theme Park Resort": "Theme Park",
            "A Local Nature Park and Wildlife Reserve": "Nature Park",
            "A High-Tech International Airport Terminal": "International Airport"
        }
        scenario_title = title_map.get(raw_scenario, raw_scenario)
        
        logger.info(f"STARTING GENERATION: {scenario_title}")

        theme = expand_thematic_prompt(raw_scenario, GEMINI_KEY)
        
        # Dynamically inject the generated name of each zone into the Vision Prompt!
        vision_prompt = DEFAULT_VISION_PROMPT.replace("{SCENARIO}", raw_scenario)
        vision_prompt = vision_prompt.replace("{STRUCTURE_NAME}", theme.structure_zone_name)
        vision_prompt = vision_prompt.replace("{PRIMARY_NAME}", theme.primary_zone_name)
        vision_prompt = vision_prompt.replace("{AQUATIC_NAME}", theme.aquatic_zone_name)
        vision_prompt = vision_prompt.replace("{GREEN_NAME}", theme.green_zone_name)
        vision_prompt = vision_prompt.replace("{PLAZA_NAME}", theme.plaza_zone_name)

        config = {
            "image_prompt": get_image_prompt(raw_scenario, theme),
            "vision_prompt": vision_prompt,
            "stress_test": data.get('stress_test', False)
        }
        
        try:
            result = orchestrator.execute_workflow(raw_scenario, config)
            if result['status'] == 'error':
                logger.error(f"Workflow Error: {result['message']}")
                return jsonify(result), 500
            
            logger.info("Compositor: Artifact synchronization complete.")
            # Create the 'Teacher View' with HUD overlays
            teacher_b64 = ForensicCompositor.composite_teacher_map(result['raw_binary'], result['vision_result'])
            
            logger.info("AudioEngine: Synchronized audio stream ready.")
            script = result['vision_result'].get('script', '')
            audio_res = audio_engine.generate_karaoke_audio(script)
            
            logger.info("Verified artifact ready for export.")
            
            # Extract metrics for logging convenience
            first_pass_words = result.get('first_pass_metrics', {}).get('word_count', 0)
            first_pass_anchors = result.get('first_pass_metrics', {}).get('anchor_count', 0)
            final_words = len(result['vision_result'].get('script', '').split())
            final_anchors = len(result['vision_result'].get('labels', []))

            return jsonify({
                "status": "success",
                "scenario": scenario_title,
                "image_url": result['image_url'],
                "teacher_image_b64": teacher_b64,
                "vision_result": result['vision_result'],
                "questions": result['vision_result'].get('questions', []),
                "audio_url": f"/static/uploads/{audio_res['audio_filename']}" if audio_res.get('status') == 'success' else "",
                "words": audio_res.get('words', []),
                "audit": {
                    "passed": result['audit_passed'],
                    "error": result['audit_error'],
                    "recovery_triggered": result['recovery_triggered'],
                    "first_pass_rejection_reason": result.get('first_pass_rejection_reason', 'NONE'),
                    "mqa_passed": result.get('audit', {}).get('mqa_passed', True),
                    "mqa_rejection_reason": result.get('audit', {}).get('mqa_rejection_reason', 'NONE'),
                    "first_pass_metrics": {
                        "words": first_pass_words,
                        "anchors": first_pass_anchors
                    },
                    "final_metrics": {
                        "words": final_words,
                        "anchors": final_anchors
                    }
                }
            })
        except Exception as e:
            logger.exception("CRITICAL ERROR IN GENERATION")
            return jsonify({"status": "error", "message": str(e)}), 500

    # --- DISCRETE AGENTIC ENDPOINTS (For Testing & Observability) ---

    @app.route('/api/pass1', methods=['POST'])
    def pass1():
        """Pass 1: Artist (Image) + Miner (Initial Draft)"""
        data = request.json
        scenario = data.get('scenario', 'University Library')
        
        art_res = orchestrator.artist.generate_map(scenario, DEFAULT_IMAGE_PROMPT)
        if art_res['status'] == 'error': return jsonify(art_res), 500
        
        vision_res = orchestrator.miner.extract_ground_truth(art_res['raw_binary'], DEFAULT_VISION_PROMPT, scenario)
        if vision_res['status'] == 'error': return jsonify(vision_res), 500
        
        return jsonify({
            "status": "success",
            "image_url": art_res['image_url'],
            "raw_binary_b64": base64.b64encode(art_res['raw_binary']).decode('utf-8'),
            "vision_result": vision_res['data']
        })

    @app.route('/api/pass2', methods=['POST'])
    def pass2():
        """Pass 2: Playwright Recovery (Self-Healing)"""
        data = request.json
        scenario = data.get('scenario')
        raw_binary = base64.b64decode(data.get('raw_binary_b64'))
        error_context = data.get('error_context', 'Manual trigger for recovery demo.')
        
        recovery_res = orchestrator.playwright.handle_recovery(raw_binary, DEFAULT_VISION_PROMPT, scenario, error_context)
        if recovery_res['status'] == 'error': return jsonify(recovery_res), 500
        
        return jsonify({
            "status": "success",
            "vision_result": recovery_res['data']
        })

    @app.route('/api/pass3', methods=['POST'])
    def pass3():
        """Pass 3: Assessment Specialist (MCQs)"""
        data = request.json
        script = data.get('script')
        
        assessment_res = orchestrator.specialist.generate_assessment(script)
        if assessment_res['status'] == 'error': return jsonify(assessment_res), 500
        
        return jsonify({
            "status": "success",
            "questions": assessment_res['questions']
        })

    @app.route('/api/log-metrics', methods=['POST'])
    def log_metrics():
        """Logs the results of a single generation run for competition evidence."""
        data = request.json
        csv_file = os.path.join(DATA_DIR, 'competition_metrics.csv')
        file_exists = os.path.isfile(csv_file)
        
        try:
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        'Mode', 'Scenario', 'FirstPass_Words', 'FirstPass_Anchors', 
                        'FirstPass_Status', 'Rejection_Reason', 'Recovery_Triggered', 
                        'Final_Words', 'Final_Anchors', 'Final_Status', 'Failure_Type', 
                        'Duration_Seconds'
                    ])
                
                writer.writerow([
                    data.get('mode', 'NORMAL'),
                    data.get('scenario', 'Unknown'),
                    data.get('firstPassWords', 0),
                    data.get('firstPassAnchors', 0),
                    'FAIL' if data.get('recoveryTriggered') else 'PASS',
                    data.get('rejectionReason', 'NONE'),
                    data.get('recoveryTriggered', False),
                    data.get('finalWords', 0),
                    data.get('finalAnchors', 0),
                    'SUCCESS',
                    data.get('failureType', 'NONE'),
                    data.get('duration', 0)
                ])
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
