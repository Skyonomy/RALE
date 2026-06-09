import asyncio
import os
import time

# Set up environment for Vertex AI and Postgres FIRST
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0467467263"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["POSTGRES_URL"] = "postgresql+psycopg2://postgres:Athey123@127.0.0.1:5432/adk_state"

import json
import uuid
import logging
from typing import Any
from google import genai
from google.genai import types
from agents.orchestrator_agent import OrchestratorAgent
from agents.schemas import DynamicTheming
import database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database.init_db()

SCENARIOS = [
    "A Large Multi-Story University Library",
    "A Modern City Hospital Wing",
    "A Family-Friendly Theme Park Resort",
    "A Local Nature Park and Wildlife Reserve",
    "A High-Tech International Airport Terminal",
    "A Futuristic Mars Colony Habitat",
    "A Medieval Castle and Fortified Village",
    "A Sustainable Vertical Urban Farm",
    "A Deep Sea Research Station",
    "A Steampunk Industrial Factory District"
]

DEFAULT_VISION_PROMPT = """You are a warm, extremely welcoming, and highly engaging professional guide leading an educational walking tour for visitors at: {SCENARIO}.

TASK: Identify 5 logical tour stops on this 2D site map based on VISUAL SHAPE AND COLOR.

INSTRUCTIONS:
1. SCAN: Look for the 5 color-coded anchors (Golden Hexagon, Blue Pool, Green Garden, Grey Building, Stone Plaza) on the map.
2. ANCHOR: Assign Stop #1 to the visual Main Entrance / Entry Gates (Grey Building), situated at the bottom, top, or sides of the map. Assign the remaining 4 stops in a logical clockwise walking tour order.
3. BOUNDING BOXES: Draw precise, tight bounding boxes [ymin, xmin, ymax, xmax] around each identified sector on the 1000x1000 grid.
4. SCRIPTING (400 WORDS): Write a professional, highly engaging, and natural human tour guide script for this scenario.
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

def expand_thematic_prompt(scenario: str) -> Any:
    client = genai.Client()
    logger.info(f"Expanding theme for scenario '{scenario}'")

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
    - REALISTIC AND ATYPICAL NAMES (CRITICAL): Generate simple, typical, factual, and realistic names for each landmark. Avoid overly elaborate, fantasy, mystical, or fictional terminology.
    - STRICT PHYSICAL SEPARATION: You MUST describe each of the 5 zones as a completely isolated, free-standing, physically separate structure or area. They must NOT touch, overlap, or be part of a single contiguous or symmetrical circular building complex.
    - COMPACT AND UNIQUE: Describe exactly ONE instance of each anchor.
    - HIGH COLOR CONTRAST: Use high-contrast color and shape descriptions.
    - THEMATIC LANDMARK DOMAIN ALIGNMENT (CRITICAL): Align landmark descriptions strictly with the scenario's native domain.

    Return the overall style description and specific style instructions.
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

def get_image_prompt(scenario: str, theme: Any) -> str:
    scenario_instructions = f"""- The Structure (Grey Roof, named '{theme.structure_zone_name}'): {theme.structure_zone}
    - The Primary Zone (Golden Hexagon, named '{theme.primary_zone_name}'): {theme.primary_zone}
    - The Aquatic Zone (Blue Pool, named '{theme.aquatic_zone_name}'): {theme.aquatic_zone}
    - The Green Zone (Dark-Green Shape, named '{theme.green_zone_name}'): {theme.green_zone}
    - The Plaza Zone (Stone Concourse, named '{theme.plaza_zone_name}'): {theme.plaza_zone}"""

    return f"""A 2D top-down clean site map layout with absolutely no text, no words, no letters, no characters. {theme.style_description}
    {theme.style_instructions}
    CRITICAL INSTRUCTIONS:
    1. ABSOLUTELY NO TEXT, LETTERS, OR NUMBERS: Zero text.
    2. 5 DISTINCT SECTORS: Draw exactly 5 large, clearly separated zones.
    3. VISUAL ANCHORS (MANDATORY): Each zone must be a unique, obvious shape and color.
    4. SCENARIO ALIGNMENT: The 5 zones must be aligned to the {scenario} as follows:
    {scenario_instructions}
    5. PERSPECTIVE: Strictly 90-degree top-down view.
    6. NO WORDS: The Compass Rose must only use visual arrows, no N/S/E/W letters."""

async def run_one(orchestrator, scenario_base, is_spatial, semaphore, run_number):
    async with semaphore:
        run_id = str(uuid.uuid4())
        
        # Dashboard expects "[STRESS]" in the scenario name for spatial tests
        scenario = f"{scenario_base} [STRESS]" if is_spatial else scenario_base
        
        logger.info(f"Run #{run_number} [{run_id}] Starting for: {scenario} (Spatial: {is_spatial})")
        
        try:
            theme = expand_thematic_prompt(scenario_base)
            
            vision_prompt = DEFAULT_VISION_PROMPT.replace("{SCENARIO}", scenario_base)
            vision_prompt = vision_prompt.replace("{STRUCTURE_NAME}", theme.structure_zone_name)
            vision_prompt = vision_prompt.replace("{PRIMARY_NAME}", theme.primary_zone_name)
            vision_prompt = vision_prompt.replace("{AQUATIC_NAME}", theme.aquatic_zone_name)
            vision_prompt = vision_prompt.replace("{GREEN_NAME}", theme.green_zone_name)
            vision_prompt = vision_prompt.replace("{PLAZA_NAME}", theme.plaza_zone_name)

            config = {
                "run_id": run_id,
                "image_prompt": get_image_prompt(scenario_base, theme),
                "vision_prompt": vision_prompt,
                "stress_test": is_spatial,
                "skip_audio": True # Explicitly turning off audio
            }
            
            start_time = time.time()
            result = await orchestrator._execute_workflow_logic(scenario, config)
            duration = time.time() - start_time
            
            status = result.get('status')
            logger.info(f"Run #{run_number} [{run_id}] Finished. Status: {status}. Duration: {duration:.2f}s")
            return {
                "run_number": run_number,
                "run_id": run_id,
                "status": status,
                "duration": duration,
                "is_spatial": is_spatial,
                "scenario": scenario
            }
        except Exception as e:
            logger.error(f"Run #{run_number} [{run_id}] Failed: {e}")
            return {
                "run_number": run_number,
                "run_id": run_id,
                "status": "error",
                "error": str(e),
                "is_spatial": is_spatial,
                "scenario": scenario
            }

async def main():
    orchestrator = OrchestratorAgent("") # API key handled by env
    semaphore = asyncio.Semaphore(3)
    
    total_runs = 100
    batch_size = 10
    
    for batch_num in range(total_runs // batch_size):
        logger.info(f"--- Starting Batch {batch_num + 1} of {total_runs // batch_size} (NORMAL) ---")
        tasks = []
        start_idx = batch_num * batch_size + 1
        end_idx = start_idx + batch_size
        
        for i in range(start_idx, end_idx):
            scenario = SCENARIOS[(i-1) % len(SCENARIOS)]
            # Note: is_spatial is set to False here
            task = asyncio.create_task(run_one(orchestrator, scenario, False, semaphore, i))
            tasks.append(task)
            if i < end_idx - 1:
                await asyncio.sleep(5) # Staggered start within batch
            
        logger.info(f"Batch {batch_num + 1} tasks created. Waiting for completion...")
        batch_results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in batch_results if r.get('status') == 'success')
        logger.info(f"Batch {batch_num + 1} Summary: {success_count}/{batch_size} successful.")
        
        if batch_num < (total_runs // batch_size) - 1:
            logger.info("Sleeping for 5 minutes before next batch to prevent rate limits...")
            await asyncio.sleep(300)
            
    logger.info("All 100 Normal Runs Completed.")

if __name__ == "__main__":
    asyncio.run(main())
