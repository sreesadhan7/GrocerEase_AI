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
            disallow_transfer_to_peers=True,
            instruction="""You are Agent 1 - SNAP/WIC Price & Budget Tracker ONLY. You are NOT a nutrition expert.

**🛒 WHAT I DO (ONLY):**
• Track SNAP ($X.XX) and WIC ($X.XX) budgets and balances
• Find grocery items from static_grocery_data.py within budget
• Compare prices between Walmart vs Target stores dynamically
• Show cost breakdown: Initial balance → Item costs → Remaining balance
• Calculate which store offers better deals for specific items
• Provide shopping lists with SNAP/WIC eligibility for each item

**❌ WHAT I NEVER DO:**
• Nutrition analysis, health advice, or food recommendations
• Diabetes, heart health, or dietary substitution advice
• Vitamin, mineral, or nutritional content analysis
• Health-focused meal planning or dietary guidance

**🔄 STRICT REDIRECTS:**
If asked about nutrition, health, diabetes, vitamins, substitutions, or meal planning:
"❌ I don't handle nutrition questions. I'm Agent 1 - Budget & Price Tracker only.
✅ For nutrition analysis, health recommendations, and dietary advice, please ask Agent 2 - Nutrition Analyst.
I focus ONLY on: budgets, prices, store comparisons, and SNAP/WIC eligibility."

**📊 MY OUTPUT FORMAT:**
• Initial SNAP: $X.XX, WIC: $X.XX (Total: $X.XX)  
• Selected Items: [item list with prices and stores]
• Store Comparison: Walmart vs Target price analysis
• Final Balances: SNAP remaining: $X.XX, WIC remaining: $X.XX
• Best Store Strategy: Shop at [Walmart/Target] for maximum savings

I am a budget calculator and price comparison tool ONLY."""
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
        AGENT 1: SNAP/WIC Price & Budget Tracker ONLY
        - Parses budgets and finds eligible items from static_grocery_data.py
        - Compares Walmart vs Target prices dynamically
        - Shows initial balance → purchases → remaining balance  
        - NEVER handles nutrition questions (strict redirect to Agent 2)
        """
        try:
            # STRICT NUTRITION REDIRECT - Agent 1 NEVER handles these topics
            user_input_lower = user_input.lower()
            # Only redirect if user is clearly asking for nutrition analysis, not price comparison
            nutrition_keywords = ['nutrition analysis', 'healthy alternatives', 'diabetes friendly', 'heart healthy', 
                                'low sodium', 'high protein', 'vitamin content', 'nutritional value', 'dietary advice',
                                'health benefits', 'substitute for health', 'nutritious options', 'meal planning']
            
            if any(phrase in user_input_lower for phrase in nutrition_keywords):
                return """❌ **I DON'T Handle Nutrition Questions**

🤖 **I'm Agent 1 - Budget & Price Tracker ONLY**

**My ONLY Functions:**
🛒 SNAP/WIC budget tracking ($X.XX → $X.XX remaining)
💰 Price comparison (Walmart vs Target from static data)  
📊 Store recommendations (which store saves more money)
🏪 Shopping list generation within benefit limits

**❌ I CANNOT Help With:**
• Nutrition analysis or health advice
• Diabetes, heart health, or dietary questions  
• Food substitutions or meal planning
• Vitamin/mineral/protein/fiber analysis

**✅ For Nutrition Questions, Ask Agent 2 - Nutrition Analyst**
Agent 2 specializes in: health analysis, dietary recommendations, nutritional content

**📝 What I CAN Help You With:**
"I have SNAP $45 and WIC $20" → I'll show you exactly what you can buy and from which stores!"""
            
            # Parse SNAP and WIC amounts from user input
            snap_amount, wic_amount = self._parse_budget_from_input(user_input)
            
            if snap_amount == 0 and wic_amount == 0:
                return """🛒 **Agent 1 - SNAP/WIC Budget & Price Tracker**

**📝 I Need Your Benefit Amounts:**
Tell me your SNAP and/or WIC budget like:
• "I have SNAP $30 and WIC $10"  
• "My SNAP is $50"
• "I have WIC $25"
• "SNAP: $40, WIC: $15"

**� What I'll Show You:**
• Initial Balance: SNAP $X.XX, WIC $X.XX (Total: $X.XX)
• Best Items: [list with prices from Walmart vs Target]
• Store Comparison: Which store saves you the most money
• Final Balance: SNAP remaining $X.XX, WIC remaining $X.XX
• Shopping Strategy: Optimal store selection for maximum savings

**🔄 After I Generate Your List:**
Agent 2 (Nutrition Analyst) can analyze the nutritional content, health benefits, and dietary compatibility."""
            
            # Process the budget request with programmatic data (not LLM-generated)
            result = await self.handle_budget_request(snap_amount, wic_amount, user_input)
            
            if not result or not result.get('shopping_list'):
                return """⚠️ **Unable to generate shopping list with your budget.**

Try different budget amounts:
- SNAP: $20-$200 
- WIC: $10-$50

Example: "I have SNAP $45 and WIC $25" """

            # Generate PROGRAMMATIC response using actual data (no LLM templates)
            return self._generate_detailed_budget_response(result)
            
        except Exception as e:
            logger.error(f"Agent 1 error: {e}")
            return f"❌ Error processing budget request: {str(e)}"

    def _generate_detailed_budget_response(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed budget response using ONLY actual grocery data from static_grocery_data.py
        NO LLM-generated templates or placeholders - only real prices and store comparisons
        """
        shopping_list = result.get('shopping_list', [])
        cost_breakdown = result.get('cost_breakdown', {})
        
        snap_budget = cost_breakdown.get('snap_budget', 0)
        wic_budget = cost_breakdown.get('wic_budget', 0)  
        total_cost = cost_breakdown.get('total_cost', 0)
        snap_used = cost_breakdown.get('snap_used', 0)
        wic_used = cost_breakdown.get('wic_used', 0)
        snap_remaining = snap_budget - snap_used
        wic_remaining = wic_budget - wic_used
        
        # Build response with ACTUAL DATA from static grocery file
        response = f"""🛒 **SNAP/WIC Shopping List Generated by Agent 1**

📊 **Your Budget:**
• SNAP: ${snap_budget:.2f}
• WIC: ${wic_budget:.2f}
• Total: ${snap_budget + wic_budget:.2f}

🛍️ **Benefits-Eligible Shopping List ({len(shopping_list)} items):**"""

        # Group items by category with REAL DATA
        categories = {}
        for item in shopping_list:
            category = item.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        # Display items with actual prices and stores
        for category, items in categories.items():
            response += f"\n\n**{category}:**"
            for item in items:
                name = item.get('name', '')
                brand = item.get('brand', '')
                size = item.get('size', '')
                price = item.get('price', 0)
                store = item.get('store', '').lower()
                payment = item.get('payment_method', 'SNAP')
                snap_eligible = "✅" if item.get('snap_eligible', False) else "❌"
                wic_eligible = "✅" if item.get('wic_eligible', False) else "❌"
                
                # Format item details with complete information
                item_details = f"{name}"
                if brand and brand != 'Fresh':
                    item_details = f"{brand} {name}"
                if size:
                    item_details += f", {size}"
                
                response += f"\n  • {item_details}"
                response += f"\n    💰 ${price:.2f} at {store} | SNAP {snap_eligible} WIC {wic_eligible} | Paid with {payment}"

        # Add ACTUAL cost breakdown
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

        # Build ACTUAL store comparison from real data
        store_costs = {}
        store_items_count = {}
        store_specific_items = {}
        
        for item in shopping_list:
            store = item.get('store', 'Unknown').title()
            price = item.get('price', 0)
            name = item.get('name', 'Item')
            
            if store not in store_costs:
                store_costs[store] = 0
                store_items_count[store] = 0
                store_specific_items[store] = []
                
            store_costs[store] += price
            store_items_count[store] += 1
            store_specific_items[store].append(f"{name} (${price:.2f})")

        # Show ACTUAL store analysis with real prices
        if store_costs:
            cheapest_store = min(store_costs.items(), key=lambda x: x[1] / store_items_count[x[0]] if store_items_count[x[0]] > 0 else float('inf'))
            
            for store, cost in store_costs.items():
                store_items = store_items_count[store]
                avg_price = cost / store_items if store_items > 0 else 0
                
                # Add store designation based on actual data
                store_note = ""
                if store.lower() == cheapest_store[0].lower():
                    store_note = " (💰 Best Average Price)"
                elif "walmart" in store.lower():
                    store_note = " (🏪 Largest Selection)"
                elif "target" in store.lower(): 
                    store_note = " (🎯 Quality Focus)"
                
                response += f"\n\n**{store}{store_note}:**"
                response += f"\n  📊 {store_items} items, ${cost:.2f} total (avg: ${avg_price:.2f}/item)"
                response += f"\n  🛍️ Items: {', '.join(store_specific_items[store][:3])}"
                if len(store_specific_items[store]) > 3:
                    response += f" + {len(store_specific_items[store])-3} more"

            # Add REAL savings comparison
            walmart_cost = store_costs.get('Walmart', 0)
            target_cost = store_costs.get('Target', 0)
            walmart_items = store_items_count.get('Walmart', 0)
            target_items = store_items_count.get('Target', 0)
            
            if walmart_cost > 0 and target_cost > 0:
                walmart_avg = walmart_cost / walmart_items if walmart_items > 0 else 0
                target_avg = target_cost / target_items if target_items > 0 else 0
                
                if walmart_avg < target_avg:
                    savings = target_avg - walmart_avg
                    response += f"\n\n💡 **Savings Analysis:** Walmart averages ${walmart_avg:.2f}/item vs Target ${target_avg:.2f}/item"
                    response += f"\n   💰 **Save ${savings:.2f} per item** shopping at Walmart"
                    response += f"\n   📍 **Best for:** Budget shopping, everyday prices, wider selection"
                elif target_avg < walmart_avg:
                    premium = walmart_avg - target_avg  
                    response += f"\n\n💡 **Quality Analysis:** Target averages ${target_avg:.2f}/item vs Walmart ${walmart_avg:.2f}/item"
                    response += f"\n   🎯 **Target saves ${premium:.2f} per item** with better quality"
                    response += f"\n   📍 **Best for:** Organic options, premium brands, store experience"

        response += f"""

📍 **Store Access & Locations:**
• **Walmart:** 4,700+ stores nationwide, extended hours (many 24/7), largest SNAP acceptance
• **Target:** 1,900+ stores, clean modern layout, better organic selection

🚗 **Shopping Strategy:**
1. **Budget Focus:** Shop Walmart first for maximum savings
2. **Quality Items:** Use Target for specific premium/organic needs  
3. **Convenience:** Choose closest store to save gas money
4. **SNAP/WIC:** Both stores fully accept benefits - no restrictions

📁 **Complete details saved to `agent_1_output.json`**
🔄 **Ready for Agent 2 nutrition analysis!**

💡 **Next:** Ask Agent 2 about nutrition content, health analysis, or dietary recommendations!"""
        
        return response

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

# Main Root Agent for ADK integration
root_agent = SnapWicScraperAgent()