"""Agent 1: SNAP/WIC Price & Budget Tracker."""

import os
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import logging

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure Google AI API
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key or api_key == "your_api_key_here":
    logger.warning("GOOGLE_API_KEY not set. Please set it in your environment variables.")
else:
    import google.generativeai as genai
    genai.configure(api_key=api_key)

# Model configuration
MODEL = "gemini-2.0-flash-001"

# Import grocery data
from .static_grocery_data import get_all_static_groceries


class SnapWicScraperAgent(LlmAgent):
    """
    Agent 1: SNAP/WIC Price & Budget Tracker
    
    Uses LlmAgent's intelligence to handle budget optimization and shopping list creation.
    """

    def __init__(self):
        # Load grocery data dynamically
        grocery_data = get_all_static_groceries()
        grocery_data_text = self._format_grocery_data_for_prompt(grocery_data)
        
        super().__init__(
            name="SNAP_WIC_Price_Tracker",
            model=MODEL,
            description="Agent 1: Handles SNAP/WIC budgets, price tracking, and grocery selection within budget constraints.",
            instruction=f"""You are Agent 1 - the SNAP/WIC Price & Budget Tracker for GrocerEase AI.

**YOUR ROLE:** Create budget-optimized shopping lists using the grocery data provided below.

**GROCERY DATA AVAILABLE:**
{grocery_data_text}

**WHEN USERS PROVIDE BUDGETS:**
1. Parse SNAP/WIC amounts from their message (accepts SNAP only, WIC only, or both)
2. Select items that stay within budget limits
3. Prioritize eligible items based on available benefits:
   - SNAP only: Select SNAP-eligible items
   - WIC only: Select WIC-eligible items  
   - Both: Prioritize SNAP-eligible first, then WIC-eligible
4. Choose cheaper options to maximize quantity
5. Calculate total cost and remaining balance
6. Provide clear shopping list with prices

**EXAMPLE RESPONSES:**

For "$30 SNAP only":
"Based on your $30.00 SNAP budget, here's your optimized shopping list:

**Walmart (Best Prices):**
• [Select SNAP-eligible items from available data within budget]
• [Show prices and eligibility]

**Total Cost: $X.XX**
**Remaining SNAP Credit: $Y.YY**

All items are SNAP-eligible and selected for maximum value within your budget."

For "$15 WIC only":
"Based on your $15.00 WIC budget, here's your optimized shopping list:

**Walmart (Best Prices):**
• [Select WIC-eligible items from available data within budget]
• [Show prices and eligibility]

**Total Cost: $X.XX**
**Remaining WIC Credit: $Y.YY**

All items are WIC-eligible and selected for maximum value within your budget."

For "$30 SNAP and $15 WIC":
"Based on your $45.00 total budget (SNAP: $30.00, WIC: $15.00), here's your optimized shopping list:

**Walmart (Best Prices):**
• [Select SNAP-eligible items first, then WIC-eligible items]
• [Show prices and eligibility]

**Total Cost: $X.XX**
**Remaining Budget: $Y.YY**

All items are SNAP/WIC eligible and selected for maximum value within your budget."

**REDIRECT NUTRITION QUESTIONS:**
When users ask about nutrition, health, diabetes, heart health, or food substitutions, respond:
"For nutrition analysis, health filtering, and substitution recommendations, please ask Agent 2 - the Nutrition Analyst. I focus on budgets and prices."

Stay focused on SNAP/WIC budgets, prices, and shopping lists.""",
            output_key="agent1_output"
        )

    def _format_grocery_data_for_prompt(self, grocery_data: Dict[str, List[Dict]]) -> str:
        """Format grocery data for inclusion in the LLM prompt."""
        formatted_text = ""
        
        for store_name, items in grocery_data.items():
            formatted_text += f"\n{store_name} Items:\n"
            for item in items:
                name = item.get('name', 'Unknown')
                price = item.get('promo_price') or item.get('regular_price', 0)
                snap_eligible = "✅" if item.get('snap_eligible', False) else "❌"
                wic_eligible = "✅" if item.get('wic_eligible', False) else "❌"
                
                formatted_text += f"• {name} - ${price:.2f} (SNAP{snap_eligible} WIC{wic_eligible})\n"
        
        return formatted_text

    async def _parse_budget_from_input(self, user_input: str) -> tuple[float, float]:
        """
        Parse SNAP and WIC dollar amounts from user input using LlmAgent only.
        Handles typos, variations, and natural language with LLM intelligence.
            
        Returns:
            tuple: (snap_amount, wic_amount)
        """
        try:
            # Create a dedicated LlmAgent for budget parsing
            budget_parser = LlmAgent(
                model=MODEL,
                name="BudgetParser",
                description="Parses SNAP/WIC amounts from user input with typo tolerance",
                instruction="""You are a budget parser that extracts SNAP and WIC dollar amounts from user input.

Handle ALL typos and variations including:
- SNAPP instead of SNAP
- WICC instead of WIC  
- SNA instead of SNAP
- WI instead of WIC
- creddit instead of credit
- bucks instead of dollars
- Mixed case: snap, Snap, SNAP
- Missing spaces: $30SNAP
- Extra punctuation: SNAP! credit

Return ONLY the amounts in this exact format:
SNAP: $X.XX
WIC: $Y.YY

If no amount found, return:
SNAP: $0.00
WIC: $0.00

Examples:
"I have $30 SNAP credit" → SNAP: $30.00, WIC: $0.00
"My SNAP is $50, WIC $15" → SNAP: $50.00, WIC: $15.00
"I have $30 SNAPP creddit" → SNAP: $30.00, WIC: $0.00
"i have $30 snap bucks" → SNAP: $30.00, WIC: $0.00
"I have $30SNAP credit" → SNAP: $30.00, WIC: $0.00"""
            )
            
            # Use Runner with proper session service
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="budget_app",
                user_id="user_123",
                session_id="budget_session_123"
            )
            
            runner = Runner(
                agent=budget_parser,
                app_name="budget_app",
                session_service=session_service
            )
            
            # Prepare user message
            user_message = types.Content(
                role='user',
                parts=[types.Part(text=user_input)]
            )
            
            # Run the agent and collect response
            response_text = "No response received"
            
            async for event in runner.run_async(
                user_id="user_123",
                session_id="budget_session_123",
                new_message=user_message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break
            
            response = response_text
            
            # Let LlmAgent extract amounts from the response
            # Create a simple parser agent to extract the amounts
            parser_agent = LlmAgent(
                model=MODEL,
                name="AmountParser",
                description="Extracts SNAP and WIC amounts from text",
                instruction=f"""Extract SNAP and WIC amounts from this text:

{response}

Return ONLY the amounts in this exact format:
SNAP: $X.XX
WIC: $Y.YY

If no amount found, return:
SNAP: $0.00
WIC: $0.00"""
            )
            
            # Use Runner to get parsed amounts
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="parser_app",
                user_id="user_123",
                session_id="parser_session_123"
            )
            
            runner = Runner(
                agent=parser_agent,
                app_name="parser_app",
                session_service=session_service
            )
            
            parse_message = types.Content(
                role='user',
                parts=[types.Part(text="Extract the amounts")]
            )
            
            parse_response = "No response received"
            async for event in runner.run_async(
                user_id="user_123",
                session_id="parser_session_123",
                new_message=parse_message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        parse_response = event.content.parts[0].text
                        break
            
            # Extract amounts from parsed response
            snap_amount = 0.0
            wic_amount = 0.0
            
            lines = parse_response.split('\n')
            for line in lines:
                if 'SNAP:' in line and '$' in line:
                    try:
                        amount_str = line.split('$')[1].strip()
                        snap_amount = float(amount_str)
                    except (ValueError, IndexError):
                        pass
                elif 'WIC:' in line and '$' in line:
                    try:
                        amount_str = line.split('$')[1].strip()
                        wic_amount = float(amount_str)
                    except (ValueError, IndexError):
                        pass
            
            return snap_amount, wic_amount
            
        except Exception as e:
            logger.error(f"Error parsing budget with LlmAgent: {e}")
            return 0.0, 0.0

    def _create_structured_output(self, user_input: str, response: str, snap_amount: float, wic_amount: float) -> Dict[str, Any]:
        """Create structured data for Agent 2 to analyze."""
        return {
            'user_input': user_input,
            'agent_response': response,
            'budget_info': {
                'snap_budget': snap_amount,
                'wic_budget': wic_amount,
                'total_budget': snap_amount + wic_amount
            },
            'timestamp': datetime.now().isoformat(),
            'agent_source': 'Agent_1_Price_Tracker'
        }

    async def __call__(self, user_input: str) -> str:
        """
        Simplified LlmAgent-based approach for budget optimization.
        Process user input and generate budget-optimized shopping lists.
        """
        try:
            # Check if user is asking about nutrition - redirect to Agent 2
            user_input_lower = user_input.lower()
            if any(word in user_input_lower for word in ['nutrition', 'healthy', 'diabetes', 'heart', 'sodium', 'sugar', 'protein', 'vitamin']):
                return """I'm Agent 1 - Price & Benefits Tracker

I handle:
- SNAP/WIC budget tracking
- Price comparison across stores  
- Benefits eligibility verification
- Shopping list generation within budget

For nutrition questions, please ask Agent 2 (Nutrition Agent) who can:
• Analyze nutritional content of foods
• Filter for diabetes-friendly options
• Check heart-healthy choices
• Provide USDA nutrition data

Please provide your SNAP/WIC benefits like:
- "I have SNAP $30 and WIC $10"
- "My SNAP is $50, WIC $15"  """
            
            # Parse SNAP and WIC amounts from user input using LlmAgent only
            snap_amount, wic_amount = await self._parse_budget_from_input(user_input)
            
            if snap_amount == 0 and wic_amount == 0:
                return """Agent 1 - Price & Benefits Tracker

I track market prices and manage your SNAP/WIC benefits to find the best groceries within budget.

Please provide your benefits:
- "I have SNAP $30 and WIC $10"
- "My SNAP is $50"  
- "I have WIC $25"
- "SNAP: $40, WIC: $15"

What I do:
• Find SNAP/WIC eligible items from Walmart & Target
• Track real prices and calculate optimal shopping lists
• Ensure you stay within benefits limits
• Generate JSON output for nutrition analysis

Next step: After I generate your shopping list, Agent 2 can analyze nutrition content."""
            
            # Generate budget-optimized shopping list using LLM reasoning
            response = await self._generate_shopping_list(snap_amount, wic_amount, user_input)
            
            # Create structured output for Agent 2
            structured_output = self._create_structured_output(user_input, response, snap_amount, wic_amount)
            
            # Return both the response and structured data
            return {
                'response': response,
                'structured_data': structured_output
            }
            
        except Exception as e:
            logger.error(f"Error in Agent 1: {e}")
            return f"Sorry, I encountered an error processing your request. Please try again with your SNAP/WIC budget amounts."

    async def _generate_shopping_list(self, snap_budget: float, wic_budget: float, user_input: str) -> str:
        """Generate shopping list using LlmAgent reasoning based on budget constraints."""
        
        try:
            # Create a dedicated LlmAgent for shopping list generation
            shopping_list_generator = LlmAgent(
                model=MODEL,
                name="ShoppingListGenerator",
                description="Generates budget-optimized shopping lists using grocery data",
                instruction=f"""You are a shopping list generator that creates budget-optimized grocery lists.

**GROCERY DATA AVAILABLE:**
{self._format_grocery_data_for_prompt(get_all_static_groceries())}

**YOUR TASK:** Create a budget-optimized shopping list based on the user's budget and request.

**BUDGET CONSTRAINTS:**
- SNAP Budget: ${snap_budget:.2f}
- WIC Budget: ${wic_budget:.2f}
- Total Budget: ${snap_budget + wic_budget:.2f}

**USER REQUEST:** "{user_input}"

**REQUIREMENTS:**
1. Select items that stay within the budget limits
2. Prioritize SNAP-eligible items first, then WIC-eligible
3. Choose cheaper options to maximize quantity
4. Calculate total cost and remaining balance
5. Provide clear shopping list with prices
6. Format response professionally

**RESPONSE FORMAT:**
Based on your ${snap_budget + wic_budget:.2f} budget (SNAP: ${snap_budget:.2f}, WIC: ${wic_budget:.2f}), here's your optimized shopping list:

**Walmart (Best Prices):**
• [Item Name] - $[Price]
• [Item Name] - $[Price]

**Target (Premium Options):**
• [Item Name] - $[Price]

**BUDGET SUMMARY:**
• Total Budget: $${snap_budget + wic_budget:.2f}
• Total Cost: $[Calculated Total]
• Remaining Balance: $[Budget - Total Cost]

**IMPORTANT:** Always calculate and show the remaining balance. If remaining balance is negative, adjust the shopping list to stay within budget.

All items are SNAP/WIC eligible and selected for maximum value within your budget.

Next step: Ask Agent 2 to analyze the nutrition content of these items."""
            )
            
            # Use Runner with proper session service
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="shopping_app",
                user_id="user_123",
                session_id="shopping_session_123"
            )
            
            runner = Runner(
                agent=shopping_list_generator,
                app_name="shopping_app",
                session_service=session_service
            )
            
            # Prepare user message
            user_message = types.Content(
                role='user',
                parts=[types.Part(text=user_input)]
            )
            
            # Run the agent and collect response
            response_text = "No response received"
            
            async for event in runner.run_async(
                user_id="user_123",
                session_id="shopping_session_123",
                new_message=user_message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break
            
            response = response_text
            return response
            
        except Exception as e:
            logger.error(f"Error generating shopping list with LlmAgent: {e}")
            # Pure LlmAgent approach - no fallback
            return f"Sorry, I encountered an error generating your shopping list. Please try again with your SNAP/WIC budget amounts."
            
            # # Fallback to simple response if LlmAgent fails (commented out)
            # return self._create_simple_response(snap_budget, wic_budget)

    # # UNUSED FUNCTION - Commented out since we use pure LlmAgent approach
    # def _create_simple_response(self, snap_budget: float, wic_budget: float) -> str:
    #     """Create a simple budget-optimized response using actual grocery data."""
    #     
    #     # Load grocery data dynamically
    #     grocery_data = get_all_static_groceries()
    #     
    #     # Select items within budget
    #     selected_items = []
    #     total_cost = 0.0
    #     remaining_budget = snap_budget + wic_budget
    #     
    #     # Process all stores and items
    #     for store_name, items in grocery_data.items():
    #         for item in items:
    #             name = item.get('name', 'Unknown')
    #             price = item.get('promo_price') or item.get('regular_price', 0)
    #             snap_eligible = item.get('snap_eligible', False)
    #             wic_eligible = item.get('wic_eligible', False)
    #             
    #             # Check if item fits budget and is eligible
    #             if total_cost + price <= remaining_budget:
    #                 # For SNAP-only budget, prioritize SNAP-eligible items
    #                 if snap_budget > 0 and wic_budget == 0 and snap_eligible:
    #                     selected_items.append((name, price, store_name, snap_eligible, wic_eligible))
    #                     total_cost += price
    #                 # For WIC-only budget, prioritize WIC-eligible items
    #                 elif wic_budget > 0 and snap_budget == 0 and wic_eligible:
    #                     selected_items.append((name, price, store_name, snap_eligible, wic_eligible))
    #                     total_cost += price
    #                 # For combined budget, accept any eligible item
    #                 elif snap_budget > 0 and wic_budget > 0 and (snap_eligible or wic_eligible):
    #                     selected_items.append((name, price, store_name, snap_eligible, wic_eligible))
    #                     total_cost += price
    #     
    #     # Format response
    #     response = f"""Based on your ${snap_budget + wic_budget:.2f} budget (SNAP: ${snap_budget:.2f}, WIC: ${wic_budget:.2f}), here's your optimized shopping list:
    # 
    # **Walmart (Best Prices):**"""
    #     
    #     walmart_total = 0
    #     target_total = 0
    #     
    #     for name, price, store, snap_eligible, wic_eligible in selected_items:
    #         if store == "Walmart":
    #             response += f"\n• {name} - ${price:.2f}"
    #             walmart_total += price
    #         else:
    #             if target_total == 0:
    #                 response += f"\n\n**Target (Premium Options):**"
    #             response += f"\n• {name} - ${price:.2f}"
    #             target_total += price
    #     
    #     response += f"""
    # 
    # **Total Cost: ${total_cost:.2f}**
    # **Remaining Budget: ${remaining_budget - total_cost:.2f}**
    # 
    # All items are SNAP/WIC eligible and selected for maximum value within your budget.
    # 
    # Next step: Ask Agent 2 to analyze the nutrition content of these items."""
    #     
    #     return response


# # UNUSED SUB-AGENTS - Commented out since we use pure LlmAgent approach
# # These were created for complex multi-agent scenarios but are not used in the current implementation

# # Create specialized sub-agents for comprehensive analysis
# price_analyzer_agent = LlmAgent(
#     model=MODEL,
#     name="PriceAnalyzer",
#     description="Analyzes grocery prices across stores and calculates protein-per-dollar ratios for budget optimization.",
#     instruction="""You are a price analysis specialist for GrocerEase AI. Analyze grocery prices across different stores 
#     and calculate value metrics like protein-per-dollar ratios. Focus on finding the best deals while maintaining 
#     nutritional value within SNAP/WIC budget constraints.
#     
#     For each item, evaluate:
#     - Price comparisons across Walmart, Target, and other stores
#     - Protein-per-dollar calculations
#     - SNAP/WIC eligibility and budget allocation
#     - Value rankings for budget optimization
#     
#     Return structured price analysis with recommendations.""",
#     disallow_transfer_to_peers=True,
# )

# # Create Budget Optimization Agent
# budget_optimizer_agent = LlmAgent(
#     model=MODEL,
#     name="BudgetOptimizer",
#     description="Optimizes grocery selections within SNAP/WIC budget constraints for maximum nutritional value.",
#     instruction="""You are a budget optimization specialist for GrocerEase AI. Given SNAP/WIC budget constraints,
#     select the optimal combination of grocery items that maximizes nutritional value while staying within budget.
#     
#     Consider:
#     - SNAP budget limits and eligible items
#     - WIC program requirements and approved foods
#     - Protein content per dollar spent
#     - Essential nutrition coverage (proteins, vegetables, grains)
#     - Store selection for best overall value
#     
#     Provide clear recommendations with cost breakdowns.""",
#     disallow_transfer_to_peers=True,
# )

# # Main Root Agent (This is what ADK web looks for as root_agent)
# root_agent = LlmAgent(
#     model=MODEL,
#     name="GrocerEase_PriceTracker",
#     description="""GrocerEase AI SNAP/WIC Price Tracker with comprehensive budget optimization and store comparison.""",
#     instruction="""You are the GrocerEase AI SNAP/WIC Price Tracker and Shopping List Creator using STATIC GROCERY DATA.
#     I create optimized grocery shopping lists from my static_grocery_data.py database, not real-time pricing.

#     **MY DATA SOURCE: static_grocery_data.py**
#     I use pre-loaded Walmart and Target grocery data with fixed prices to create budget-optimized shopping lists.

#     **BUDGET SCENARIOS I HANDLE:**
#     1. **SNAP Only**: Use only SNAP budget (e.g., "$45 SNAP")
#     2. **WIC Only**: Use only WIC budget (e.g., "$25 WIC") 
#     3. **Combined**: Use both SNAP + WIC budgets (e.g., "$45 SNAP + $25 WIC = $70 total")
#     4. **Either/Or**: Show options for spending one benefit vs the other

#     **WHEN USERS PROVIDE BUDGETS, I:**
#     1. **Parse Budget**: Extract SNAP amount, WIC amount, or combined
#     2. **Filter Items**: Select from static_grocery_data.py within budget
#     3. **Optimize Selection**: Maximize nutrition (protein-per-dollar) within limits
#     4. **Show All Possibilities**: 
#        - "With $45 SNAP only: [list]"
#        - "With $25 WIC only: [list]" 
#        - "With combined $70: [enhanced list]"
#     5. **Compare Stores**: Show Walmart vs Target pricing from static data
#     6. **Save JSON**: Output for Agent 2 analysis

#     **I DO NOT:**
#     Analyze existing user lists (that's Agent 2's job)
#     Get real-time pricing (I use static data only)
#     Handle nutrition analysis (redirect to Agent 2)

#     **REDIRECT ANALYSIS REQUESTS:**
#     When users ask "analyze my chicken, oats, lentils" say:
#     "I create shopping lists from our grocery database. For analyzing your existing items, please ask Agent 2 - the Nutrition Analyst. 
    
#     If you need a new shopping list, tell me your SNAP/WIC budget!"

#     **EXAMPLE RESPONSE FORMAT:**
#     **BUDGET OPTIMIZATION FROM STATIC DATA**
    
#     **Your Budget Options:**
#     • SNAP only ($45): 12 items, $42.50 used
#     • WIC only ($25): 6 items, $24.75 used  
#     • Combined ($70): 18 items, $67.25 used BEST VALUE
    
#     **DETAILED GROCERY LIST (Best Scenario):**
    
#     **Proteins:**
#     • Great Value Large White Eggs, 12 Count - $1.98 at Walmart (SNAP ✅ WIC ✅)
#     • Fresh Ground Beef, 93% Lean, per lb - $5.98 at Walmart (SNAP ✅)
#     • Good & Gather Boneless Chicken Breast, 2.5 lb - $8.49 at Target (SNAP ✅)
    
#     **Pantry Staples:**
#     • Great Value Canned Black Beans, 15 oz - $0.88 at Walmart (SNAP ✅ WIC ✅)
#     • Great Value Peanut Butter, Creamy, 40 oz - $3.48 at Walmart (SNAP ✅ WIC ✅)
    
#     **Fresh Produce:**
#     • Fresh Bananas, per lb - $0.58 at Walmart (SNAP ✅)
#     • Fresh Organic Bananas, per lb - $0.69 at Target (SNAP ✅)
    
#     **Store Comparison Analysis:**
#     • **Walmart (Best Deals):** 8 items, $22.15 total
#       - Cheapest for: Eggs ($1.98 vs $2.79), Black Beans ($0.88 vs $1.29)
#       - More locations nationwide, easier access
#     • **Target (Quality Focus):** 4 items, $15.30 total  
#       - Better for: Organic options, cage-free products
#       - Higher quality but premium pricing
    
#     **Shopping Strategy:**
#     • **Primary Stop:** Walmart (save $4.50 on similar items)
#     • **Specialty Items:** Target for organic/premium options if budget allows
#     • **Nearby Locations:** Both chains widely available in most areas
    
#     I'm your comprehensive grocery price tracker with detailed product comparisons! """,
#     sub_agents=[price_analyzer_agent, budget_optimizer_agent],
# )