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
        # Stable 2.5 Flash for guaranteed availability and speed
        self.adk_agent = Agent(
            name="miner_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are a precision vision extraction agent. Your task is to analyze "
                "architectural schematics and extract 1000x1000 coordinates. "
                "Output exactly 5 landmarks with their bounding boxes and a 450+ word script. "
                "Return valid JSON matching the schema."
                "\nCRITICAL: ALWAYS use the validate_multimodal_geometry tool to check your "
                "coordinates before returning your final answer. If it rejects your proposal, "
                "you MUST fix the coordinates based on its feedback and check again!"
            ),
            tools=[validate_multimodal_geometry],
            output_schema=VisionResponse,
            output_key="vision_result"
        )
