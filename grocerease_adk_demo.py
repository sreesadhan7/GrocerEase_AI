"""
GrocerEase AI - Direct ADK Communication Demo
Shows how to use ADK's shared state for agent communication
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

async def get_budget_analysis_tool(budget_input: str) -> str:
    """Tool function for budget analysis using Agent 1"""
    try:
        budget_agent = SnapWicScraperAgent()
        result = await budget_agent(budget_input)
        
        if isinstance(result, dict):
            return result.get('response', '')
        else:
            return result
    except Exception as e:
        return f"Budget analysis error: {str(e)}"

async def get_nutrition_analysis_tool(nutrition_input: str) -> str:
    """Tool function for nutrition analysis using Agent 2"""
    try:
        nutrition_agent = NutritionAgent()
        # Create a simple nutrition analysis based on common foods
        return f"""**Nutrition Analysis for {nutrition_input}:**

**General Nutrition Guidelines:**
• **Protein Sources**: Chicken, eggs, beans, peanut butter - excellent for muscle building
• **Fiber Sources**: Beans, whole grains, vegetables - help with digestion and heart health
• **Healthy Fats**: Peanut butter, nuts - good for brain and heart health
• **Vitamins**: Fresh fruits and vegetables - boost immune system

**Health Recommendations:**
• Focus on lean proteins for muscle building
• Include fiber-rich foods for digestive health
• Choose whole grains over refined grains
• Limit processed foods and added sugars
• Stay hydrated with water

**Budget-Friendly Tips:**
• Beans and lentils are excellent protein sources at low cost
• Frozen vegetables often have same nutrition as fresh
• Buy seasonal fruits and vegetables for best prices
• Consider store brands for better value

This analysis provides general nutrition guidance for your shopping list."""
    except Exception as e:
        return f"Nutrition analysis error: {str(e)}"

# Create coordinator agent
coordinator = LlmAgent(
    model=MODEL,
    name="grocerease_coordinator",
    description="Coordinates budget and nutrition agents for comprehensive grocery advice",
    instruction="""You are a GrocerEase AI coordinator that helps users with SNAP/WIC grocery shopping.

**YOUR WORKFLOW:**
1. **FIRST**: Use get_budget_analysis_tool to get the shopping list
2. **SECOND**: Use get_nutrition_analysis_tool to get nutrition advice
3. **THIRD**: Combine everything into ONE comprehensive response

**CRITICAL REQUIREMENTS:**
- ALWAYS call get_budget_analysis_tool FIRST
- ALWAYS call get_nutrition_analysis_tool SECOND
- ALWAYS provide store recommendations (Walmart vs Target pricing)
- ALWAYS combine everything into ONE final response

**RESPONSE FORMAT - PROVIDE ONLY ONE COMBINED RESPONSE:**

**GrocerEase AI Shopping & Nutrition Analysis:**

**Your Shopping List:**
[Show the complete shopping list with prices from get_budget_analysis_tool]

**Store Recommendations:**
- **Walmart**: Best for [specific items] - saves you $X.XX
- **Target**: Better for [specific items] - premium quality
- **Shopping Strategy**: [Recommend which store to visit first]

**Nutrition & Health Analysis:**
[Include key nutrition insights from get_nutrition_analysis_tool]

**Combined Actionable Advice:**
[Provide practical tips combining budget, nutrition, and store recommendations]

**EXAMPLE RESPONSE:**
**GrocerEase AI Shopping & Nutrition Analysis:**

**Your Shopping List:**
Based on your $15 budget (SNAP: $8, WIC: $7), here's your optimized shopping list:

• Great Value Large White Eggs, 12 Count - $1.98
• Great Value Canned Black Beans, 15 oz - $0.88
• Great Value Peanut Butter, Creamy, 40 oz - $3.48
• Fresh Bananas, per lb - $0.58

**Total Cost: $6.92 | Remaining Budget: $8.08**

**Store Recommendations:**
- **Walmart**: Best for eggs ($1.98 vs $2.79 at Target) and beans ($0.88 vs $1.29) - saves you $1.22
- **Target**: Better for organic options if budget allows
- **Shopping Strategy**: Start at Walmart for essentials, then Target for premium items

**Nutrition & Health Analysis:**
Eggs provide complete protein, beans offer fiber for blood sugar control, peanut butter gives healthy fats, and bananas provide potassium.

**Combined Actionable Advice:**
For your diabetic needs, this list is excellent - eggs and beans help with blood sugar control. With remaining $8.08, add leafy greens from Walmart ($2.50) and consider Target's organic options ($3.00). Shop Walmart first for savings, then Target for quality upgrades.

Provide ONLY this combined response format.""",
    tools=[get_budget_analysis_tool, get_nutrition_analysis_tool]
)

async def interactive_custom_prompts():
    """Interactive mode with custom prompts from command line"""
    
    session_service = InMemorySessionService()
    runner = Runner(agent=coordinator, app_name="grocerease_app", session_service=session_service)
    
    # Create session
    await session_service.create_session(
        app_name="grocerease_app",
        user_id="user1",
        session_id="session1"
    )
    
    while True:
        try:
            user_input = input("\nEnter your grocery request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter a grocery request.")
                continue
            
            print(f"\nProcessing: {user_input}")
            print("-" * 50)
            
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
                    print(f"\nGrocerEase AI Response:\n{event.content.parts[0].text}")
                    break
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    print("=== GrocerEase AI - CLI Mode ===")
    print("Enter your grocery requests directly. Type 'quit' to exit.")
    print()
    asyncio.run(interactive_custom_prompts())
