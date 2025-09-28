"""Agent 1: SNAP/WIC Price & Budget Tracker with static grocery data."""

import os
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
import logging

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Import static grocery data with proper path handling
try:
    # Try relative import first (for local testing)
    import static_grocery_data
except ImportError:
    # Try absolute import for ADK environment
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    sys.path.insert(0, current_dir)
    import static_grocery_data

# Load environment variables
load_dotenv()

# Model configuration
MODEL = "gemini-2.0-flash-001"


class SnapWicScraperAgent(LlmAgent):
    """
    Agent 1: SNAP/WIC Price & Budget Tracker
    
    Responsibilities:
    - Track SNAP/WIC budgets and remaining balances
    - Find grocery items within budget constraints
    - Calculate costs and optimize selections
    - Output JSON for Agent 2 nutrition analysis
    - Redirect nutrition questions to Agent 2
    """

    def __init__(self):
        super().__init__(
            name="SNAP_WIC_Price_Tracker",
            model=MODEL,
            description="Agent 1: Handles SNAP/WIC budgets, price tracking, and grocery selection within budget constraints.",
            instruction="""You are Agent 1 - the SNAP/WIC Price & Budget Tracker for GrocerEase AI.

**YOUR ROLE:** Handle SNAP/WIC budgets, grocery prices, and budget-optimized shopping lists.

**I HANDLE:**
• SNAP/WIC budget tracking and remaining balances
• Grocery item selection within budget constraints  
• Price comparisons and cost calculations
• Shopping list optimization for maximum value
• JSON output generation for nutrition analysis

**I DO NOT HANDLE nutrition questions - redirect to Agent 2:**
When users ask about nutrition, health, diabetes, heart health, or food substitutions, respond:
"For nutrition analysis, health filtering, and substitution recommendations, please ask Agent 2 - the Nutrition Analyst. I focus on budgets and prices."

**EXAMPLE RESPONSE:**
For budget request: "I found 15 items within your $45 SNAP budget:
• Total cost: $42.50
• SNAP remaining: $2.50
• Items saved for Agent 2 nutrition analysis"

For nutrition question: "I handle budgets and prices. For nutrition analysis and health recommendations, please ask Agent 2 - the Nutrition Analyst."

Stay focused on SNAP/WIC budgets, prices, and shopping lists."""
        )

    async def handle_budget_request(self, snap_budget: float, wic_budget: float, preferences: str = "") -> Dict[str, Any]:
        """
        MAIN FUNCTION: Handle user's SNAP/WIC budget and return ALL POSSIBLE spending scenarios
        
        Agent 1 Responsibilities:
        - Use static_grocery_data.py for consistent pricing
        - Show SNAP-only, WIC-only, and combined budget possibilities  
        - Optimize selections for maximum nutrition within each scenario
        - Generate complete shopping lists for each budget option
        - Save comprehensive data for Agent 2 analysis
        
        Args:
            snap_budget: User's SNAP benefit amount ($)
            wic_budget: User's WIC benefit amount ($)  
            preferences: Optional user preferences/dietary needs
            
        Returns:
            JSON with ALL budget scenarios and optimized shopping lists
        """
        try:
            # Get all available grocery data from static file
            all_data = static_grocery_data.get_all_static_groceries()
            
            # Prepare items with enhanced details
            all_items = []
            for store_name, store_data in all_data.items():
                for item in store_data:
                    enhanced_item = item.copy()
                    enhanced_item['store'] = store_name
                    enhanced_item['price'] = item.get('promo_price') or item.get('regular_price') or 2.99
                    enhanced_item['protein_per_dollar'] = 3.0  # Default protein ratio
                    all_items.append(enhanced_item)
            
            # Create different budget scenarios
            scenarios = {}
            
            # Scenario 1: SNAP only
            if snap_budget > 0:
                snap_eligible = [item for item in all_items if item.get('snap_eligible', False)]
                snap_list = self._optimize_grocery_selection(snap_eligible, [], snap_budget, 0, preferences)
                scenarios['snap_only'] = {
                    'budget': snap_budget,
                    'items': snap_list,
                    'total_cost': sum(item['price'] for item in snap_list),
                    'remaining': snap_budget - sum(item['price'] for item in snap_list),
                    'item_count': len(snap_list)
                }
            
            # Scenario 2: WIC only  
            if wic_budget > 0:
                wic_eligible = [item for item in all_items if item.get('wic_eligible', False)]
                wic_list = self._optimize_grocery_selection([], wic_eligible, 0, wic_budget, preferences)
                scenarios['wic_only'] = {
                    'budget': wic_budget,
                    'items': wic_list,
                    'total_cost': sum(item['price'] for item in wic_list),
                    'remaining': wic_budget - sum(item['price'] for item in wic_list),
                    'item_count': len(wic_list)
                }
            
            # Scenario 3: Combined SNAP + WIC
            if snap_budget > 0 and wic_budget > 0:
                combined_budget = snap_budget + wic_budget
                snap_eligible = [item for item in all_items if item.get('snap_eligible', False)]
                wic_eligible = [item for item in all_items if item.get('wic_eligible', False)]
                combined_list = self._optimize_grocery_selection(snap_eligible, wic_eligible, snap_budget, wic_budget, preferences)
                scenarios['combined'] = {
                    'budget': combined_budget,
                    'snap_portion': snap_budget,
                    'wic_portion': wic_budget,
                    'items': combined_list,
                    'total_cost': sum(item['price'] for item in combined_list),
                    'remaining': combined_budget - sum(item['price'] for item in combined_list),
                    'item_count': len(combined_list)
                }
            
            # Use the best scenario (combined if available, otherwise the larger single budget)
            best_scenario_key = 'combined' if 'combined' in scenarios else ('snap_only' if snap_budget >= wic_budget else 'wic_only')
            best_scenario = scenarios[best_scenario_key]
            
            # Log the selection
            logger.info(f"Budget scenarios generated: {list(scenarios.keys())}")
            logger.info(f"Best scenario ({best_scenario_key}): {best_scenario['item_count']} items, ${best_scenario['total_cost']:.2f}")
            
            # Save comprehensive data for Agent 2
            output_data = {
                'shopping_list': best_scenario['items'],
                'all_scenarios': scenarios,
                'cost_breakdown': {
                    'total_cost': best_scenario['total_cost'],
                    'snap_budget': snap_budget,
                    'wic_budget': wic_budget,
                    'remaining_snap': snap_budget - sum(item['price'] for item in best_scenario['items'] if item.get('snap_eligible', False)),
                    'remaining_wic': wic_budget - sum(item['price'] for item in best_scenario['items'] if item.get('wic_eligible', False)),
                    'best_scenario': best_scenario_key
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to JSON for Agent 2
            output_path = os.path.join(os.path.dirname(__file__), 'agent_1_output.json')
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Agent 1 output saved with all scenarios, best: {best_scenario_key}")
            
            return output_data
            
        except Exception as e:
            logger.error(f"Error in handle_budget_request: {e}")
            return {
                'shopping_list': [],
                'all_scenarios': {},
                'cost_breakdown': {'total_cost': 0, 'error': str(e)},
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate optimal shopping list within budget
            shopping_list = self._optimize_grocery_selection(
                snap_items=snap_eligible,
                wic_items=wic_eligible, 
                snap_budget=snap_budget,
                wic_budget=wic_budget,
                preferences=preferences
            )
            
            # Calculate totals and remaining balances
            snap_total = sum(item['price'] for item in shopping_list if item.get('payment_type') == 'SNAP')
            wic_total = sum(item['price'] for item in shopping_list if item.get('payment_type') == 'WIC')
            
            result = {
                "agent_source": "Agent_1_Price_Tracker",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "input_budget": {
                    "snap_budget": snap_budget,
                    "wic_budget": wic_budget,
                    "total_budget": snap_budget + wic_budget
                },
                "shopping_list": shopping_list,
                "cost_breakdown": {
                    "snap_used": snap_total,
                    "wic_used": wic_total,
                    "total_cost": snap_total + wic_total
                },
                "remaining_balance": {
                    "snap_remaining": snap_budget - snap_total,
                    "wic_remaining": wic_budget - wic_total,
                    "total_remaining": (snap_budget + wic_budget) - (snap_total + wic_total)
                },
                "summary": {
                    "total_items": len(shopping_list),
                    "snap_items": len([item for item in shopping_list if item.get('payment_type') == 'SNAP']),
                    "wic_items": len([item for item in shopping_list if item.get('payment_type') == 'WIC']),
                    "stores_involved": list(set(item.get('store', '') for item in shopping_list))
                },
                "ready_for_agent_2": True,
                "agent_2_instructions": {
                    "next_step": "Nutrition analysis and health filtering available",
                    "capabilities": [
                        "USDA nutrition data lookup for all items",
                        "Diabetes-friendly filtering", 
                        "Heart-healthy options",
                        "Nutritional density analysis",
                        "Healthy substitution recommendations"
                    ]
                }
            }
            
            # Save result to JSON file for Agent 2 to consume
            output_path = os.path.join(os.path.dirname(__file__), '..', 'agent_1_output.json')
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
                
            logger.info(f"Agent 1 output saved with {len(shopping_list)} items, total cost ${snap_total + wic_total:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Budget request handling failed: {e}")
            return {
                "agent_source": "Agent_1_Price_Tracker",
                "status": "error",
                "error": str(e),
                "message": "Failed to process budget request"
            }

    def _optimize_grocery_selection(self, snap_items: List[Dict], wic_items: List[Dict], 
                                   snap_budget: float, wic_budget: float, preferences: str = "") -> List[Dict]:
        """
        Optimize grocery selection to maximize value within SNAP/WIC budgets
        
        Strategy:
        1. Prioritize essential items (proteins, grains, vegetables)
        2. Sort by price efficiency to maximize quantity
        3. Ensure balanced nutrition categories
        4. Stay within budget constraints for each program
        """
        shopping_list = []
        
        # Define essential categories for balanced nutrition
        essential_categories = {
            'protein': ['Dairy', 'Meat', 'Pantry'],  # eggs, beans, protein powder
            'produce': ['Fresh Produce'],
            'grains': ['Pantry', 'Bakery']
        }
        
        # Sort items by price efficiency (lower price first for maximum quantity)
        snap_items_sorted = sorted(snap_items, key=lambda x: x.get('price') or 999)
        wic_items_sorted = sorted(wic_items, key=lambda x: x.get('price') or 999)
        
        # Allocate SNAP items with category balance
        snap_spent = 0.0
        category_count = {'protein': 0, 'produce': 0, 'grains': 0, 'other': 0}
        
        for item in snap_items_sorted:
            item_price = item.get('price') or 0
            if item_price > 0 and snap_spent + item_price <= snap_budget:
                # Determine item category
                item_category = item.get('category', 'Other')
                category_type = 'other'
                
                for cat_type, cat_list in essential_categories.items():
                    if item_category in cat_list:
                        category_type = cat_type
                        break
                
                # Add item with balanced category distribution
                item_copy = item.copy()
                item_copy['payment_type'] = 'SNAP'
                item_copy['category_type'] = category_type
                shopping_list.append(item_copy)
                
                snap_spent += item_price
                category_count[category_type] += 1
        
        # Allocate WIC items (typically more restricted categories)
        wic_spent = 0.0
        for item in wic_items_sorted:
            item_price = item.get('price') or 0
            if item_price > 0 and wic_spent + item_price <= wic_budget:
                item_copy = item.copy()
                item_copy['payment_type'] = 'WIC'
                
                # Determine category type for WIC items too
                item_category = item.get('category', 'Other')
                category_type = 'other'
                
                for cat_type, cat_list in essential_categories.items():
                    if item_category in cat_list:
                        category_type = cat_type
                        break
                
                item_copy['category_type'] = category_type
                shopping_list.append(item_copy)
                wic_spent += item_price
        
        logger.info(f"Selected {len(shopping_list)} items: SNAP ${snap_spent:.2f}, WIC ${wic_spent:.2f}")
        logger.info(f"Category distribution: {category_count}")
        
        return shopping_list

    async def __call__(self, user_input: str) -> str:
        """
        AGENT 1: Price & Benefits Tracker
        - Tracks market prices from Walmart/Target + grocery data
        - Manages SNAP/WIC budget allocation  
        - Ensures all items are benefits-eligible
        - Outputs grocery list with prices + remaining balances
        """
        try:
            # Check if user is asking about nutrition - redirect to Agent 2
            user_input_lower = user_input.lower()
            if any(word in user_input_lower for word in ['nutrition', 'healthy', 'diabetes', 'heart', 'sodium', 'sugar', 'protein', 'vitamin']):
                return """❌ **I'm Agent 1 - Price & Benefits Tracker**

I handle:
🛒 **SNAP/WIC budget tracking**
💰 **Price comparison across stores**  
📊 **Benefits eligibility verification**
🏪 **Shopping list generation within budget**

❓ **For nutrition questions, please ask Agent 2 (Nutrition Agent)** who can:
• Analyze nutritional content of foods
• Filter for diabetes-friendly options
• Check heart-healthy choices
• Provide USDA nutrition data

Please provide your SNAP/WIC benefits like:
- "I have SNAP $30 and WIC $10"
- "My SNAP is $50, WIC $15"  """
            
            # Parse SNAP and WIC amounts from user input
            snap_amount, wic_amount = self._parse_budget_from_input(user_input)
            
            if snap_amount == 0 and wic_amount == 0:
                return """🛒 **Agent 1 - Price & Benefits Tracker**

I track market prices and manage your SNAP/WIC benefits to find the best groceries within budget.

📝 **Please provide your benefits:**
- "I have SNAP $30 and WIC $10"
- "My SNAP is $50"  
- "I have WIC $25"
- "SNAP: $40, WIC: $15"

📊 **What I do:**
• Find SNAP/WIC eligible items from Walmart & Target
• Track real prices and calculate optimal shopping lists
• Ensure you stay within benefits limits
• Generate JSON output for nutrition analysis

🔄 **Next step:** After I generate your shopping list, Agent 2 can analyze nutrition content."""
            
            # Process the budget request
            result = await self.handle_budget_request(snap_amount, wic_amount, user_input)
            
            if not result or not result.get('shopping_list'):
                return f"Sorry, I couldn't create a shopping list. Please check your budget amount."
            
            # Format response for user using the new data structure
            shopping_list = result['shopping_list']
            cost_breakdown = result.get('cost_breakdown', {})
            all_scenarios = result.get('all_scenarios', {})
            
            total_cost = cost_breakdown.get('total_cost', 0)
            snap_used = sum(item['price'] for item in shopping_list if item.get('snap_eligible', False))
            wic_used = sum(item['price'] for item in shopping_list if item.get('wic_eligible', False))
            snap_remaining = cost_breakdown.get('remaining_snap', snap_amount - snap_used)
            wic_remaining = cost_breakdown.get('remaining_wic', wic_amount - wic_used)
            
            response = f"""🛒 **SNAP/WIC Shopping List Generated by Agent 1**

📊 **Your Budget:**
• SNAP: ${snap_amount:.2f}
• WIC: ${wic_amount:.2f}
• Total: ${snap_amount + wic_amount:.2f}

🛍️ **Benefits-Eligible Shopping List ({len(shopping_list)} items):**
"""
            
            # Group items by category for better organization
            categories = {}
            for item in shopping_list:
                category = item.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            # Display items by category
            for category_name, category_items in categories.items():
                response += f"\n**{category_name}:**\n"
                for item in category_items:
                    store = item.get('store', 'Unknown')
                    name = item.get('name', 'Unknown item')
                    price = item.get('price', 0)
                    payment = item.get('payment_type', 'Unknown')
                    brand = item.get('brand', '')
                    size = item.get('size', '')
                    snap_eligible = "✅" if item.get('snap_eligible', False) else "❌"
                    wic_eligible = "✅" if item.get('wic_eligible', False) else "❌"
                    
                    # Format item details with complete information
                    item_details = f"{name}"
                    if brand and brand != 'Fresh':
                        item_details = f"{brand} {name}"
                    if size:
                        item_details += f", {size}"
                    
                    response += f"  • {item_details}\n"
                    response += f"    💰 ${price:.2f} at {store} | SNAP {snap_eligible} WIC {wic_eligible} | Paid with {payment}\n"
            
            response += f"""
💰 **Cost Breakdown:**
• SNAP used: ${snap_used:.2f}
• WIC used: ${wic_used:.2f}  
• Total cost: ${total_cost:.2f}

🏦 **Remaining Balance:**
• SNAP remaining: ${snap_remaining:.2f}
• WIC remaining: ${wic_remaining:.2f}
• Total remaining: ${snap_remaining + wic_remaining:.2f}

🏪 **Store Comparison & Savings:**"""
            
            # Add enhanced store breakdown with comparison
            store_costs = {}
            store_items_count = {}
            store_items_list = {}
            
            for item in shopping_list:
                store = item.get('store', 'Unknown')
                price = item.get('price', 0)
                name = item.get('name', 'Item')
                
                if store not in store_costs:
                    store_costs[store] = 0
                    store_items_count[store] = 0
                    store_items_list[store] = []
                    
                store_costs[store] += price
                store_items_count[store] += 1
                store_items_list[store].append(f"{name} (${price:.2f})")
            
            # Determine which store is cheaper
            if store_costs:
                cheapest_store = min(store_costs.items(), key=lambda x: x[1] / store_items_count[x[0]])
                
                for store, cost in store_costs.items():
                    store_items = store_items_count[store]
                    avg_price = cost / store_items if store_items > 0 else 0
                    
                    # Add store designation
                    store_note = ""
                    if store.lower() == cheapest_store[0].lower():
                        store_note = " (💰 Best Average Price)"
                    elif store.lower() == "walmart":
                        store_note = " (🏪 Most Locations Nationwide)"
                    elif store.lower() == "target": 
                        store_note = " (🎯 Premium Quality Options)"
                    
                    response += f"\n\n**{store.title()}{store_note}:**"
                    response += f"\n  📊 {store_items} items, ${cost:.2f} total (avg: ${avg_price:.2f}/item)"
                    response += f"\n  🛍️ Best deals: {', '.join(store_items_list[store][:3])}"
                    if len(store_items_list[store]) > 3:
                        response += f" + {len(store_items_list[store])-3} more"
                
                # Add savings recommendation with specific comparisons
                total_walmart = store_costs.get('Walmart', 0)
                total_target = store_costs.get('Target', 0)
                if total_walmart > 0 and total_target > 0:
                    if total_walmart < total_target:
                        savings = total_target - total_walmart
                        response += f"\n\n💡 **Money-Saving Tip:** Shopping at Walmart saves ${savings:.2f} vs Target"
                        response += f"\n   └─ **Why Walmart?** Lower everyday prices, more SNAP-friendly options"
                    elif total_target < total_walmart:
                        savings = total_walmart - total_target
                        response += f"\n\n💡 **Quality Tip:** Target costs ${savings:.2f} more but offers premium/organic options"
                        response += f"\n   └─ **Why Target?** Better quality, organic selections, cleaner stores"
            
            response += f"""

📍 **Nearby Store Locations & Access:**
• **Walmart Supercenters:** 
  - Most locations nationwide (4,700+ stores)
  - Extended hours (many 24/7)
  - Larger grocery selection, lower prices
  - Best for: Budget shopping, bulk purchases
  
• **Target Stores:**
  - Premium shopping experience (1,900+ stores) 
  - Clean, organized layout
  - Better organic/natural options
  - Best for: Quality items, healthier choices

🚗 **Shopping Strategy Recommendations:**
1. **Primary Shop:** Choose store with most items from your list
2. **Price Conscious:** Start with Walmart for staples
3. **Quality Focus:** Upgrade select items at Target if budget allows
4. **Location:** Pick closest store to save gas money

📁 **Complete details saved to `agent_1_output.json`**
🔄 **Ready for Agent 2 nutrition analysis!**

💡 **Next:** Ask Agent 2 about nutrition content, diabetes compatibility, or health recommendations!"""
            
            return response
            
        except Exception as e:
            logger.error(f"User input handling failed: {e}")
            return f"I encountered an error processing your request: {str(e)}"

    def _parse_budget_from_input(self, user_input: str) -> tuple[float, float]:
        """
        Parse SNAP and WIC dollar amounts from user input
        
        Returns:
            tuple: (snap_amount, wic_amount)
        """
        import re
        
        user_input = user_input.upper()
        snap_amount = 0.0
        wic_amount = 0.0
        
        # Look for SNAP amounts - enhanced patterns
        snap_patterns = [
            r'SNAP\s*\$?(\d+(?:\.\d{2})?)',
            r'SNAP[:\s]+\$?(\d+(?:\.\d{2})?)',
            r'\$(\d+(?:\.\d{2})?)\s+SNAP',
            r'(\d+)\s*DOLLAR[S]?\s*SNAP',
            r'(\d+)\s*SNAP',
            r'SNAP.*?(\d+)'
        ]
        
        for pattern in snap_patterns:
            match = re.search(pattern, user_input)
            if match:
                snap_amount = float(match.group(1))
                break
        
        # Look for WIC amounts - enhanced patterns
        wic_patterns = [
            r'WIC\s*\$?(\d+(?:\.\d{2})?)',
            r'WIC[:\s]+\$?(\d+(?:\.\d{2})?)',
            r'\$(\d+(?:\.\d{2})?)\s+WIC',
            r'(\d+)\s*DOLLAR[S]?\s*WIC',
            r'(\d+)\s*WIC',
            r'WIC.*?(\d+)'
        ]
        
        for pattern in wic_patterns:
            match = re.search(pattern, user_input)
            if match:
                wic_amount = float(match.group(1))
                break
        
        return snap_amount, wic_amount


# Create specialized sub-agents for comprehensive analysis
price_analyzer_agent = LlmAgent(
    model=MODEL,
    name="PriceAnalyzer",
    description="Analyzes grocery prices across stores and calculates protein-per-dollar ratios for budget optimization.",
    instruction="""You are a price analysis specialist for GrocerEase AI. Analyze grocery prices across different stores 
    and calculate value metrics like protein-per-dollar ratios. Focus on finding the best deals while maintaining 
    nutritional value within SNAP/WIC budget constraints.
    
    For each item, evaluate:
    - Price comparisons across Walmart, Target, and other stores
    - Protein-per-dollar calculations
    - SNAP/WIC eligibility and budget allocation
    - Value rankings for budget optimization
    
    Return structured price analysis with recommendations.""",
    disallow_transfer_to_peers=True,
)

# Create Budget Optimization Agent
budget_optimizer_agent = LlmAgent(
    model=MODEL,
    name="BudgetOptimizer",
    description="Optimizes grocery selections within SNAP/WIC budget constraints for maximum nutritional value.",
    instruction="""You are a budget optimization specialist for GrocerEase AI. Given SNAP/WIC budget constraints,
    select the optimal combination of grocery items that maximizes nutritional value while staying within budget.
    
    Consider:
    - SNAP budget limits and eligible items
    - WIC program requirements and approved foods
    - Protein content per dollar spent
    - Essential nutrition coverage (proteins, vegetables, grains)
    - Store selection for best overall value
    
    Prioritize high-protein, low-cost items that provide maximum nutrition per dollar.""",
    disallow_transfer_to_peers=True,
)

# Main Root Agent (This is what ADK web looks for as root_agent)
root_agent = LlmAgent(
    model=MODEL,
    name="GrocerEase_PriceTracker",
    description="""GrocerEase AI SNAP/WIC Price Tracker with comprehensive budget optimization and store comparison.""",
    instruction="""You are the GrocerEase AI SNAP/WIC Price Tracker and Shopping List Creator using STATIC GROCERY DATA.
    I create optimized grocery shopping lists from my static_grocery_data.py database, not real-time pricing.

    **🎯 MY DATA SOURCE: static_grocery_data.py**
    I use pre-loaded Walmart and Target grocery data with fixed prices to create budget-optimized shopping lists.

    **💰 BUDGET SCENARIOS I HANDLE:**
    1. **SNAP Only**: Use only SNAP budget (e.g., "$45 SNAP")
    2. **WIC Only**: Use only WIC budget (e.g., "$25 WIC") 
    3. **Combined**: Use both SNAP + WIC budgets (e.g., "$45 SNAP + $25 WIC = $70 total")
    4. **Either/Or**: Show options for spending one benefit vs the other

    **🛒 WHEN USERS PROVIDE BUDGETS, I:**
    1. **Parse Budget**: Extract SNAP amount, WIC amount, or combined
    2. **Filter Items**: Select from static_grocery_data.py within budget
    3. **Optimize Selection**: Maximize nutrition (protein-per-dollar) within limits
    4. **Show All Possibilities**: 
       - "With $45 SNAP only: [list]"
       - "With $25 WIC only: [list]" 
       - "With combined $70: [enhanced list]"
    5. **Compare Stores**: Show Walmart vs Target pricing from static data
    6. **Save JSON**: Output for Agent 2 analysis

    **I DO NOT:**
    ❌ Analyze existing user lists (that's Agent 2's job)
    ❌ Get real-time pricing (I use static data only)
    ❌ Handle nutrition analysis (redirect to Agent 2)

    **REDIRECT ANALYSIS REQUESTS:**
    When users ask "analyze my chicken, oats, lentils" say:
    "I create shopping lists from our grocery database. For analyzing your existing items, please ask Agent 2 - the Nutrition Analyst. 
    
    If you need a new shopping list, tell me your SNAP/WIC budget!"

    **EXAMPLE RESPONSE FORMAT:**
    💰 **BUDGET OPTIMIZATION FROM STATIC DATA**
    
    📊 **Your Budget Options:**
    • SNAP only ($45): 12 items, $42.50 used
    • WIC only ($25): 6 items, $24.75 used  
    • Combined ($70): 18 items, $67.25 used ✅ BEST VALUE
    
    🛍️ **DETAILED GROCERY LIST (Best Scenario):**
    
    **Proteins:**
    • Great Value Large White Eggs, 12 Count - $1.98 at Walmart (SNAP ✅ WIC ✅)
    • Fresh Ground Beef, 93% Lean, per lb - $5.98 at Walmart (SNAP ✅)
    • Good & Gather Boneless Chicken Breast, 2.5 lb - $8.49 at Target (SNAP ✅)
    
    **Pantry Staples:**
    • Great Value Canned Black Beans, 15 oz - $0.88 at Walmart (SNAP ✅ WIC ✅)
    • Great Value Peanut Butter, Creamy, 40 oz - $3.48 at Walmart (SNAP ✅ WIC ✅)
    
    **Fresh Produce:**
    • Fresh Bananas, per lb - $0.58 at Walmart (SNAP ✅)
    • Fresh Organic Bananas, per lb - $0.69 at Target (SNAP ✅)
    
    🏪 **Store Comparison Analysis:**
    • **Walmart (💰 Best Deals):** 8 items, $22.15 total
      - Cheapest for: Eggs ($1.98 vs $2.79), Black Beans ($0.88 vs $1.29)
      - More locations nationwide, easier access
    • **Target (🎯 Quality Focus):** 4 items, $15.30 total  
      - Better for: Organic options, cage-free products
      - Higher quality but premium pricing
    
    📍 **Shopping Strategy:**
    • **Primary Stop:** Walmart (save $4.50 on similar items)
    • **Specialty Items:** Target for organic/premium options if budget allows
    • **Nearby Locations:** Both chains widely available in most areas
    
    I'm your comprehensive grocery price tracker with detailed product comparisons! """,
    sub_agents=[price_analyzer_agent, budget_optimizer_agent],
)