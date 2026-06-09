import logging
from google.adk import Agent
from tools.adk_tools import validate_multimodal_geometry
from .schemas import VisionResponse

logger = logging.getLogger(__name__)

class PlaywrightAgent:
    """
    Playwright Agent: An ADK-compliant Self-Healing Agent.
    Now utilizes Structured Outputs to eliminate Schema Drift during repair.
    """

    def __init__(self, key_manager):
        self.key_manager = key_manager
        # Stable 2.5 Pro for high-reasoning repair
        self.adk_agent = Agent(
            name="PLAYWRIGHT",
            model="gemini-2.5-pro",
            instruction=(
                "You are a validator-guided recovery agent. Your task is to repair multimodal "
                "proposals that failed validation. Use the provided error context to "
                "programmatically refine the landmarks. "
                "CRITICAL: You are performing a coordinate-only repair. You MUST preserve the original script by passing an empty string \"\" for the script field. "
                "Always check your repairs with validate_multimodal_geometry tool. "
                "Return valid JSON matching the schema."
            ),
            tools=[validate_multimodal_geometry],
            output_schema=VisionResponse,
            output_key="vision_result"
        )
