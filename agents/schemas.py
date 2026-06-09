from pydantic import BaseModel, Field
from typing import List, Optional

class Landmark(BaseModel):
    number: int = Field(..., description="The sequence number of the landmark (1-5).")
    location_name: str = Field(..., description="The semantic name of the location (e.g., 'Main Concourse').")
    ymin: float = Field(..., description="The top coordinate (0-1000).")
    xmin: float = Field(..., description="The left coordinate (0-1000).")
    ymax: float = Field(..., description="The bottom coordinate (0-1000).")
    xmax: float = Field(..., description="The right coordinate (0-1000).")
    x: Optional[float] = Field(default=None, description="The horizontal center coordinate (calculated).")
    y: Optional[float] = Field(default=None, description="The vertical center coordinate (calculated).")
    bbox_type: str = Field(default="landmark", description="The type of bounding box.")
    semantic_reason: str = Field(..., description="The visual evidence for selecting this point.")
    anchor_policy: str = Field(default="center", description="How to calculate the anchor point.")

class VisionResponse(BaseModel):
    script: str = Field(..., description="A 400+ word professional tour guide script.")
    labels: List[Landmark] = Field(..., description="A list of exactly 5 validated landmarks.")

class Question(BaseModel):
    question: str = Field(..., description="The text of the multiple choice question.")
    options: List[str] = Field(..., description="A list of 4 plausible options.")
    answer: str = Field(..., description="The correct option text.")

class SpecialistResponse(BaseModel):
    questions: List[Question] = Field(..., description="Exactly 5 IELTS-style MCQs.")

class DynamicTheming(BaseModel):
    style_description: str = Field(..., description="The overall description of the map style, incorporating the scenario's theme (e.g., 'A grimy, neon-lit 2D top-down cyberpunk illustrated map of...').")
    style_instructions: str = Field(..., description="Specific style instruction keywords (e.g., 'Style: Dark retro-futuristic cyberpunk, vibrant neon yellow, cyan and pink highlights. Rich playful cartoon textures, zero clutter.').")
    structure_zone_name: str = Field(..., description="A creative, theme-appropriate name for the Structure Zone (Grey Roof), e.g., 'Grand Drawbridge Reception' or 'Terminal Main Hall'.")
    structure_zone: str = Field(..., description="A detailed description of the Structure Zone (Grey Roof), fitting its name and scenario.")
    primary_zone_name: str = Field(..., description="A creative, theme-appropriate name for the Primary Zone (Golden Hexagon), e.g., 'Golden Rocket Coaster' or 'Chronos Data Mainframe'.")
    primary_zone: str = Field(..., description="A detailed description of the Primary Zone (Golden Hexagon), fitting its name and scenario.")
    aquatic_zone_name: str = Field(..., description="A creative, theme-appropriate name for the Aquatic Zone (Blue Pool), e.g., 'Shipwreck Bay Splash Slides' or 'Plutonium Coolant Well'.")
    aquatic_zone: str = Field(..., description="A detailed description of the Aquatic Zone (Blue Pool), fitting its name and scenario.")
    green_zone_name: str = Field(..., description="A creative, theme-appropriate name for the Green Zone (Dark-Green Shape), e.g., 'Lost Jungle Raptor Trek' or 'Neon Bio-dome'.")
    green_zone: str = Field(..., description="A detailed description of the Green Zone (Dark-Green Shape), fitting its name and scenario.")
    plaza_zone_name: str = Field(..., description="A creative, theme-appropriate name for the Plaza Zone (Stone Concourse), e.g., 'Main Street Celebration Plaza' or 'Sector 4 Assembly Alley'.")
    plaza_zone: str = Field(..., description="A detailed description of the Plaza Zone (Stone Concourse), fitting its name and scenario.")
