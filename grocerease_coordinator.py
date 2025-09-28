"""
GrocerEase AI - ADK Coordinator System
Direct ADK communication between agents using shared state
"""

import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.generativeai as genai

# Import your actual agents
from Budgets_Agent.agent import SnapWicScraperAgent
from Nutrition_Agent.nutrition_agent import NutritionAgent

# Load environment variables
load_dotenv()

# Configure API key
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Model configuration
MODEL = "gemini-2.0-flash-exp"

# Initialize your actual agents
budget_agent = SnapWicScraperAgent()
nutrition_agent = NutritionAgent()

async def get_budget_analysis(budget_input: str) -> dict:
    """Analyze SNAP/WIC budget using Agent 1 and return structured data"""
    try:
        # Run the budget agent
        result = await budget_agent(budget_input)
        
        # Extract the response and structured data
        if isinstance(result, dict):
            response = result.get('response', '')
            structured_data = result.get('structured_data', {})
            
            # Return both formatted response and structured data
            formatted_response = f"""Budget Analysis Complete:

{response}

Budget Details:
• SNAP Budget: ${structured_data.get('budget_info', {}).get('snap_budget', 0):.2f}
• WIC Budget: ${structured_data.get('budget_info', {}).get('wic_budget', 0):.2f}
• Total Budget: ${structured_data.get('budget_info', {}).get('total_budget', 0):.2f}

Agent Source: {structured_data.get('agent_source', 'Unknown')}"""
            
            return {
                'response': formatted_response,
                'structured_data': structured_data
            }
        else:
            return {
                'response': result,
                'structured_data': {}
            }
            
    except Exception as e:
        return {
            'response': f"Budget analysis error: {str(e)}",
            'structured_data': {}
        }

async def get_nutrition_analysis(food_items: str, agent1_output: dict = None) -> str:
    """Analyze nutrition using Agent 2 with Agent 1's output"""
    try:
        # Run the nutrition agent with Agent 1's output
        response = await nutrition_agent(food_items, agent1_output)
        return response
            
    except Exception as e:
        return f"Nutrition analysis error: {str(e)}"

# Create coordinator agent that uses both agents as tools
coordinator = LlmAgent(
    model=MODEL,
    name="grocerease_coordinator", 
    description="Coordinates grocery shopping using budget and nutrition agents with direct ADK communication",
    instruction="""You are a GrocerEase AI coordinator. You help users with SNAP/WIC grocery shopping by coordinating two specialized tools:

**AGENT COORDINATION WORKFLOW:**
1. **Budget Analysis First**: Use get_budget_analysis to get shopping list and budget details
2. **Nutrition Analysis Second**: Use get_nutrition_analysis with the budget data for health analysis
3. **Comprehensive Response**: Combine both analyses into actionable shopping advice

**TOOL CAPABILITIES:**
- **get_budget_analysis**: Creates SNAP/WIC-optimized shopping lists with prices
- **get_nutrition_analysis**: Analyzes nutrition using USDA data and provides health recommendations

**COMMUNICATION PATTERN:**
- Budget analysis returns structured data with shopping list and budget info
- Nutrition analysis receives this data and provides nutrition analysis
- You coordinate the workflow and provide comprehensive advice

**RESPONSE STRUCTURE:**
1. **Budget Analysis**: Shopping list with prices and budget breakdown
2. **Nutrition Analysis**: Health recommendations and nutrition facts
3. **Combined Advice**: Actionable shopping and health guidance

**EXAMPLE WORKFLOW:**
User: "I have $20 SNAP budget, I'm diabetic"
1. Call get_budget_analysis("I have $20 SNAP budget, I'm diabetic")
2. Call get_nutrition_analysis("diabetic-friendly analysis")
3. Provide comprehensive diabetic-friendly shopping advice

Always ensure both tools are used to provide complete grocery shopping assistance.""",
    tools=[get_budget_analysis, get_nutrition_analysis]
)

async def test_coordinator():
    """Test the coordinator with direct ADK communication"""
    print("=== GrocerEase AI - Coordinator Test ===")
    print("Using direct ADK communication between agents")
    print()
    
    # Test scenario
    test_input = "I have $20 SNAP budget, I'm diabetic"
    print(f"Testing: {test_input}")
    print("-" * 50)
    
    session_service = InMemorySessionService()
    runner = Runner(agent=coordinator, app_name="grocerease_app", session_service=session_service)
    
    # Create session
    await session_service.create_session(
        app_name="grocerease_app",
        user_id="user1",
        session_id="session1"
    )
    
    message = types.Content(
        role='user', 
        parts=[types.Part(text=test_input)]
    )
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1", 
        new_message=message
    ):
        if event.is_final_response():
            print(f"Coordinator Response:\n{event.content.parts[0].text}")
            break

async def interactive_coordinator():
    """Interactive test with coordinator"""
    print("=== Interactive Coordinator Test ===")
    print("Using direct ADK communication between agents")
    print()
    
    user_input = input("Enter your grocery request: ").strip()
    
    if not user_input:
        print("No input provided.")
        return
    
    print(f"\nProcessing: {user_input}")
    print("-" * 50)
    
    session_service = InMemorySessionService()
    runner = Runner(agent=coordinator, app_name="grocerease_app", session_service=session_service)
    
    # Create session
    await session_service.create_session(
        app_name="grocerease_app",
        user_id="user1",
        session_id="session1"
    )
    
    message = types.Content(
        role='user', 
        parts=[types.Part(text=user_input)]
    )
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1", 
        new_message=message
    ):
        if event.is_final_response():
            print(f"Coordinator Response:\n{event.content.parts[0].text}")
            break

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Test coordinator")
    print("2. Interactive coordinator")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_coordinator())
    elif choice == "2":
        asyncio.run(interactive_coordinator())
    else:
        print("Invalid choice. Testing coordinator...")
        asyncio.run(test_coordinator())
