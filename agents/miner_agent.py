import logging
from google.adk import Agent
from tools.adk_tools import validate_multimodal_geometry
from .schemas import VisionResponse

logger = logging.getLogger(__name__)

class MinerAgent:
    """
    Miner Agent: An ADK-compliant Vision Reasoning Agent.
    Now utilizes Structured Outputs to eliminate Schema Drift.
    """

    def __init__(self, key_manager):
        self.key_manager = key_manager
        # Reverted back to 2.5 Flash for guaranteed speed in live presentations
        self.adk_agent = Agent(
            name="MINER",
            model="gemini-2.5-flash",
            instruction=(
                "You are an elite, highly precise architectural vision extraction agent. "
                "Your task is to analyze 2D schematics and extract coordinates on a 0-1000 scale. "
                "Output exactly 5 landmarks with their bounding boxes and a 400+ word script. "
                "\nCRITICAL BOUNDING BOX INSTRUCTIONS:\n"
                "1. TIGHT CROPPING: Your bounding boxes MUST perfectly and tightly hug the actual edges of the landmark structure or garden.\n"
                "2. NO BLEEDING: Do NOT include surrounding pathways, roads, or negative space inside the box. Crop as tightly to the colored pixels of the target as mathematically possible.\n"
                "3. SHAPE ALIGNMENT: If the object is oblong, make an oblong box. If it is tall, make a tall box.\n"
                "Return valid JSON matching the schema."
            ),
            output_schema=VisionResponse,
            output_key="vision_result"
        )
