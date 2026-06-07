import logging
from google.adk import Agent
from .schemas import SpecialistResponse

logger = logging.getLogger(__name__)

class SpecialistAgent:
    """
    Specialist Agent: Generates assessment questions based on the validated script.
    Now utilizes Structured Outputs for deterministic question formatting.
    """
    def __init__(self, key_manager):
        self.key_manager = key_manager
        # Stable 1.5 Flash for speed
        self.adk_agent = Agent(
            name="specialist_agent",
            model="gemini-flash-latest",
            instruction="Create exactly 5 IELTS MCQs based on the provided script.",
            output_schema=SpecialistResponse,
            output_key="specialist_result"
        )
