import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Add /app to sys.path
sys.path.insert(0, os.getcwd())

from agents.orchestrator_agent import OrchestratorAgent

def main():
    print("="*60)
    print("🤖 TESTING LIVE CUSTOM GENERATION PIPELINE")
    print("="*60)
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    orchestrator = OrchestratorAgent(api_key)
    
    scenario = "A Vertical Urban Garden and Park"
    config = {
        "vision_prompt": "Identify exactly 5 zones and write a 450 word script for a {SCENARIO}.",
        "image_prompt": "A professional, high-contrast, strictly 2D top-down architectural site map of: {SCENARIO}.",
        "stress_test": False
    }
    
    print(f"Target Scenario: '{scenario}'")
    print("Executing ADK Workflow (Detect-Reject-Repair Active)...")
    
    result = orchestrator.execute_workflow(scenario, config)
    
    print("\n" + "="*50)
    print("📊 CUSTOM RUN RESULTS")
    print("="*50)
    print(f"Status:                 {result.get('status')}")
    print(f"Audit Passed:           {result.get('audit_passed')}")
    print(f"Self-Healing Triggered: {result.get('recovery_triggered')}")
    
    if result.get("status") == "success":
        print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"  - Vision Output Status: Pydantic Schema Validated")
        print(f"  - Landmarks Extracted:  {len(result.get('vision_result', {}).get('labels', []))}/5")
        print(f"  - Script Word Count:    {len(result.get('vision_result', {}).get('script', '').split())} words")
        print(f"  - Specialist MCQs:      {len(result.get('vision_result', {}).get('questions', []))} MCQs generated successfully")
        
        # Print actual generated questions to prove deterministic formatting
        print("\n❓ Sample Specialist MCQ Generated:")
        questions = result.get('vision_result', {}).get('questions', [])
        if questions:
            q = questions[0]
            print(f"  - Question: {q.get('question')}")
            print(f"  - Options:  {', '.join(q.get('options', []))}")
            print(f"  - Answer:   {q.get('answer')}")
    else:
        print("\n❌ WORKFLOW FAILED!")
        print(f"  - Error Message: {result.get('message')}")
    print("="*50)

if __name__ == "__main__":
    main()
