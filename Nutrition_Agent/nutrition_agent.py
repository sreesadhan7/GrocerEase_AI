"""
Nutrition Agent - Agent 2 for GrocerEase AI
Uses USDA API + LlmAgent for intelligent nutrition analysis
"""

import json
import os
import asyncio
import aiohttp
from typing import List, Dict, Any
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import logging

# Load environment variables
load_dotenv()

# USDA API Configuration
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")  # Get from .env file
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Model configuration
MODEL = "gemini-2.0-flash-exp"

class NutritionAgent(LlmAgent):
    """
    Agent 2: Nutrition Analyst using USDA API + LlmAgent
    
    Fetches real nutrition data from USDA FoodData Central and uses LlmAgent
    for intelligent analysis, health recommendations, and substitution advice.
    """

    def __init__(self):
        super().__init__(
            name="USDA_Nutrition_Analyzer",
            model=MODEL,
            description="Agent 2: Analyzes nutrition using USDA data and provides health recommendations",
            instruction="""You are Agent 2 - the USDA Nutrition Analyst for GrocerEase AI.

**YOUR ROLE:** Provide comprehensive nutrition analysis using official USDA nutrition data.

**CAPABILITIES:**
- Fetch real nutrition data from USDA FoodData Central API
- Analyze nutrition facts for health compatibility
- Provide condition-specific recommendations (diabetes, heart health, etc.)
- Suggest cost-effective substitutions
- Calculate nutrient density and cost-effectiveness

**USDA DATA INTEGRATION:**
- Official nutrition facts from USDA FoodData Central
- Accurate macronutrient and micronutrient data
- Real-time nutrition information for any food item
- Professional-grade nutrition analysis

**ANALYSIS APPROACH:**
1. **USDA Data Fetching:** Get official nutrition facts for each item
2. **Health Compatibility:** Score items for specific health conditions
3. **Nutrient Density:** Calculate nutrients per dollar spent
4. **Smart Recommendations:** Provide personalized health advice
5. **Substitution Analysis:** Suggest better alternatives when needed

**RESPONSE FORMAT:**
- Professional nutrition analysis with USDA data
- Health compatibility scores and explanations
- Cost-effectiveness calculations
- Actionable recommendations for better health
- Clear, evidence-based advice

**DATA SOURCE:** USDA FoodData Central + SNAP/WIC Program Database

**Try me with:** "Analyze my shopping list for SNAP benefits: Chicken Breast, Whole Wheat Bread, Milk, Eggs" 

I'll provide comprehensive nutrition analysis with SNAP/WIC program optimization!

**AGENT 1 OUTPUT REFERENCE:**
When Agent 1 provides shopping data via {agent1_output}, use that structured data to:
1. Parse the shopping list from agent_response field
2. Extract budget information from budget_info field
3. Analyze each item using USDA nutrition data
4. Provide health recommendations based on the user's specific needs

The agent1_output contains:
- user_input: Original user request
- agent_response: Shopping list with prices and items
- budget_info: SNAP/WIC budget details
- timestamp: When the analysis was performed
- agent_source: "Agent_1_Price_Tracker"

Use this data to provide comprehensive nutrition analysis tailored to the user's budget and shopping list.""",
            tools=[self.analyze_with_llm_only]
        )

    def _sanitize_unicode(self, text: str) -> str:
        """Remove Unicode emojis and characters that cause encoding issues on Windows."""
        import re
        # Remove common Unicode emojis and symbols
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
        return text

    async def fetch_usda_nutrition(self, food_name: str) -> Dict[str, Any]:
        """Fetch nutrition data from USDA API for a specific food item."""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for food item
                search_url = f"{USDA_BASE_URL}/foods/search"
                params = {
                    'api_key': USDA_API_KEY,
                    'query': food_name,
                    'pageSize': 1,
                    'sortBy': 'dataType',
                    'sortOrder': 'asc'
                }
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('foods') and len(data['foods']) > 0:
                            food = data['foods'][0]
                            fdc_id = food.get('fdcId')
                            
                            # Get detailed nutrition data
                            detail_url = f"{USDA_BASE_URL}/food/{fdc_id}"
                            detail_params = {'api_key': USDA_API_KEY}
                            
                            async with session.get(detail_url, params=detail_params) as detail_response:
                                if detail_response.status == 200:
                                    detail_data = await detail_response.json()
                                    return self._parse_usda_data(detail_data, food_name)
                        
                        # Fallback: return basic structure if no USDA data found
                        return self._create_fallback_nutrition(food_name)
                    else:
                        print(f"USDA API error: {response.status}")
                        return self._create_fallback_nutrition(food_name)
                        
        except Exception as e:
            print(f"Error fetching USDA data for {food_name}: {e}")
            return self._create_fallback_nutrition(food_name)

    def _parse_usda_data(self, usda_data: Dict, food_name: str) -> Dict[str, Any]:
        """Parse USDA API response into structured nutrition data."""
        try:
            nutrients = {}
            
            # Extract key nutrients from USDA data
            for nutrient in usda_data.get('foodNutrients', []):
                nutrient_info = nutrient.get('nutrient', {})
                name = nutrient_info.get('name', '').lower()
                amount = nutrient_info.get('amount', 0)
                
                # Map USDA nutrients to our format
                if 'protein' in name:
                    nutrients['protein'] = amount
                elif 'fat' in name and 'total' in name:
                    nutrients['fat'] = amount
                elif 'carbohydrate' in name and 'total' in name:
                    nutrients['carbs'] = amount
                elif 'fiber' in name and 'total' in name:
                    nutrients['fiber'] = amount
                elif 'sugar' in name and 'total' in name:
                    nutrients['sugar'] = amount
                elif 'sodium' in name:
                    nutrients['sodium'] = amount
                elif 'calcium' in name:
                    nutrients['calcium'] = amount
                elif 'iron' in name:
                    nutrients['iron'] = amount
                elif 'vitamin c' in name:
                    nutrients['vitamin_c'] = amount
            
            return {
                'name': food_name,
                'usda_id': usda_data.get('fdcId'),
                'description': usda_data.get('description', food_name),
                'nutrients': nutrients,
                'serving_size': '100g',  # USDA data is per 100g
                'data_source': 'USDA FoodData Central'
            }
            
        except Exception as e:
            print(f"Error parsing USDA data: {e}")
            return self._create_fallback_nutrition(food_name)

    def _create_fallback_nutrition(self, food_name: str) -> Dict[str, Any]:
        """Create estimated nutrition data when USDA API is unavailable."""
        # Basic nutrition estimates for common foods
        estimates = {
            'chicken': {'protein': 25, 'fat': 3, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'sodium': 70},
            'beef': {'protein': 26, 'fat': 15, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'sodium': 60},
            'eggs': {'protein': 13, 'fat': 11, 'carbs': 1, 'fiber': 0, 'sugar': 0, 'sodium': 140},
            'milk': {'protein': 3, 'fat': 3, 'carbs': 5, 'fiber': 0, 'sugar': 5, 'sodium': 40},
            'bread': {'protein': 9, 'fat': 3, 'carbs': 49, 'fiber': 2, 'sugar': 5, 'sodium': 400},
            'rice': {'protein': 7, 'fat': 0, 'carbs': 28, 'fiber': 0, 'sugar': 0, 'sodium': 5},
            'banana': {'protein': 1, 'fat': 0, 'carbs': 23, 'fiber': 3, 'sugar': 12, 'sodium': 1},
            'carrots': {'protein': 1, 'fat': 0, 'carbs': 10, 'fiber': 3, 'sugar': 5, 'sodium': 69},
            'cheese': {'protein': 25, 'fat': 33, 'carbs': 1, 'fiber': 0, 'sugar': 0, 'sodium': 620}
        }
        
        # Find best match
        food_lower = food_name.lower()
        for key, nutrients in estimates.items():
            if key in food_lower:
                return {
                    'name': food_name,
                    'usda_id': None,
                    'description': f"Estimated nutrition for {food_name}",
                    'nutrients': nutrients,
                    'serving_size': '100g',
                    'data_source': 'Estimated (USDA API unavailable)'
                }
        
        # Default fallback
        return {
            'name': food_name,
            'usda_id': None,
            'description': f"Estimated nutrition for {food_name}",
            'nutrients': {'protein': 5, 'fat': 2, 'carbs': 10, 'fiber': 1, 'sugar': 2, 'sodium': 50},
            'serving_size': '100g',
            'data_source': 'Estimated (USDA API unavailable)'
        }

    async def analyze_with_llm_only(self, shopping_list: List[Dict], user_message: str = "") -> str:
        """Analyze shopping list using LlmAgent intelligence only (no USDA API dependency)."""
        try:
            # Create LlmAgent for nutrition analysis without USDA dependency
            nutrition_analyzer = LlmAgent(
                model=MODEL,
                name="LLM_Nutrition_Analyzer",
                description="Analyzes nutrition using general nutrition knowledge and provides health recommendations",
                instruction=f"""You are a nutrition expert analyzing grocery items using comprehensive nutrition knowledge.

**SHOPPING LIST:**
{json.dumps(shopping_list, indent=2)}

**USER REQUEST:** "{user_message}"

**YOUR TASK:** Provide comprehensive nutrition analysis including:
1. **General Nutrition Facts** for each item based on common knowledge
2. **Health Compatibility Scoring** (diabetes-friendly, heart-healthy, etc.)
3. **Nutrient Density Analysis** (protein, fiber, vitamins per serving)
4. **Cost-Effectiveness Calculations** (nutrients per dollar)
5. **Smart Health Recommendations** based on nutrition science
6. **Overall Health Score** with detailed explanations

**RESPONSE FORMAT:**
**NUTRITION ANALYSIS**

**Item-by-Item Analysis:**
• **[Item Name]:**
  - Protein: Xg per serving (Xg per $1) ✅/⚠️/❌ Rating
  - Fat: Xg (lean/heart-healthy/etc.)
  - Carbs: Xg ✅/⚠️/❌ for diabetes
  - Fiber: Xg ✅/⚠️/❌ for digestion
  - Health Score: X/100 - Brief explanation

**Health Recommendations:**
• Condition-specific advice based on nutrition science
• Cost-effectiveness analysis
• Substitution suggestions if needed

**Overall Assessment:**
• Total nutrition investment analysis
• Health compatibility summary
• Budget efficiency rating

Use your comprehensive nutrition knowledge to provide accurate, professional nutrition analysis."""
            )
            
            # Use Runner to execute LlmAgent
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="nutrition_app",
                user_id="user_123",
                session_id="nutrition_session_123"
            )
            
            runner = Runner(
                agent=nutrition_analyzer,
                app_name="nutrition_app",
                session_service=session_service
            )
            
            # Prepare analysis prompt
            analysis_prompt = f"Analyze this shopping list for nutrition and health: {user_message}"
            user_message_obj = types.Content(
                role='user',
                parts=[types.Part(text=analysis_prompt)]
            )
            
            # Run the agent and collect response
            response_text = "No response received"
            
            async for event in runner.run_async(
                user_id="user_123",
                session_id="nutrition_session_123",
                new_message=user_message_obj
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break
            
            return self._sanitize_unicode(response_text)
            
        except Exception as e:
            print(f"Error in LlmAgent-only analysis: {e}")
            return f"Error analyzing nutrition data: {e}"

    async def analyze_with_usda_and_llm(self, shopping_list: List[Dict], user_message: str = "") -> str:
        """Analyze shopping list using USDA API data and LlmAgent intelligence."""
        try:
            # Fetch USDA data for each item
            usda_data = {}
            for item in shopping_list:
                food_name = item.get('name', '')
                nutrition_data = await self.fetch_usda_nutrition(food_name)
                usda_data[food_name] = nutrition_data
            
            # Create LlmAgent for analysis
            nutrition_analyzer = LlmAgent(
                model=MODEL,
                name="USDA_Nutrition_Analyzer",
                description="Analyzes nutrition using USDA data and provides health recommendations",
                instruction=f"""You are a nutrition expert analyzing grocery items using official USDA nutrition data.

**USDA NUTRITION DATA:**
{json.dumps(usda_data, indent=2)}

**SHOPPING LIST:**
{json.dumps(shopping_list, indent=2)}

**USER REQUEST:** "{user_message}"

**YOUR TASK:** Provide comprehensive nutrition analysis including:
1. **USDA-Verified Nutrition Facts** for each item
2. **Health Compatibility Scoring** (diabetes-friendly, heart-healthy, etc.)
3. **Nutrient Density Analysis** (protein, fiber, vitamins per serving)
4. **Cost-Effectiveness Calculations** (nutrients per dollar)
5. **Smart Health Recommendations** based on the data
6. **Overall Health Score** with detailed explanations

**RESPONSE FORMAT:**
**USDA NUTRITION ANALYSIS**

**Item-by-Item Analysis:**
• **[Item Name] (USDA Data):**
  - Protein: Xg per 100g (Xg per $1) ✅/⚠️/❌ Rating
  - Fat: Xg (lean/heart-healthy/etc.)
  - Carbs: Xg ✅/⚠️/❌ for diabetes
  - Fiber: Xg ✅/⚠️/❌ for digestion
  - Health Score: X/100 - Brief explanation

**Health Recommendations:**
• Condition-specific advice based on USDA data
• Cost-effectiveness analysis
• Substitution suggestions if needed

**Overall Assessment:**
• Total nutrition investment analysis
• Health compatibility summary
• Budget efficiency rating

Use the official USDA data to provide accurate, professional nutrition analysis."""
            )
            
            # Use Runner to execute LlmAgent
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="nutrition_app",
                user_id="user_123",
                session_id="nutrition_session_123"
            )
            
            runner = Runner(
                agent=nutrition_analyzer,
                app_name="nutrition_app",
                session_service=session_service
            )
            
            # Prepare analysis prompt
            analysis_prompt = f"Analyze this shopping list using the provided USDA nutrition data: {user_message}"
            user_message_obj = types.Content(
                role='user',
                parts=[types.Part(text=analysis_prompt)]
            )
            
            # Run the agent and collect response
            response_text = "No response received"
            
            async for event in runner.run_async(
                user_id="user_123",
                session_id="nutrition_session_123",
                new_message=user_message_obj
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break
            
            return self._sanitize_unicode(response_text)
            
        except Exception as e:
            print(f"Error in USDA + LlmAgent analysis: {e}")
            return f"Error analyzing nutrition data: {e}"

    async def __call__(self, message: str, agent1_output: Dict[str, Any] = None) -> str:
        """Main entry point for nutrition analysis."""
        try:
            # Use agent1_output if provided, otherwise try to load from file (fallback)
            if agent1_output:
                shopping_data = agent1_output
            else:
                shopping_data = self.load_shopping_data()
            
            if not shopping_data:
                return self._sanitize_unicode("No shopping data available from Agent 1. Please run Agent 1 first.")
            
            # Extract shopping list from agent_response
            agent_response = shopping_data.get('agent_response', '')
            
            if not agent_response:
                return self._sanitize_unicode("No shopping list found in Agent 1 response.")
            
            # Parse the shopping list from the agent response text
            shopping_list = await self._parse_shopping_list_from_response(agent_response)
            
            if not shopping_list:
                return self._sanitize_unicode("Could not parse shopping list from Agent 1 response.")
            
            # Analyze the shopping list using LlmAgent only (no USDA API dependency)
            response = await self.analyze_with_llm_only(shopping_list, message)
            return self._sanitize_unicode(response)
            
        except Exception as e:
            error_msg = f"Error in nutrition analysis: {e}"
            return self._sanitize_unicode(error_msg)

    async def _parse_shopping_list_from_response(self, agent_response: str) -> List[Dict]:
        """Parse shopping list from Agent 1's response text using LlmAgent"""
        try:
            # Create a parser agent to extract shopping list items
            parser_agent = LlmAgent(
                model=MODEL,
                name="ShoppingListParser",
                description="Parses shopping list items from text",
                instruction=f"""Parse this shopping list text and extract items with prices:

{agent_response}

Return ONLY a JSON array of items in this format:
[
  {{
    "name": "Item Name",
    "price": 0.00,
    "store": "Store Name",
    "category": "category"
  }}
]

Categories should be: protein, grains, produce, dairy, or other
Store should be: Walmart, Target, or other

If no items found, return: []"""
            )
            
            # Use Runner to get parsed items
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
                parts=[types.Part(text="Parse the shopping list")]
            )
            
            parse_response = "[]"
            async for event in runner.run_async(
                user_id="user_123",
                session_id="parser_session_123",
                new_message=parse_message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        parse_response = event.content.parts[0].text
                        break
            
            # Parse the JSON response
            import json
            try:
                shopping_list = json.loads(parse_response)
                return shopping_list if isinstance(shopping_list, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            print(f"Error parsing shopping list: {e}")
            return []

    def load_shopping_data(self) -> Dict[str, Any]:
        """Load shopping data saved by Agent 1."""
        try:
            data_file = "Budgets_Agent/agent_1_output.json"
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading shopping data: {e}")
            return {}


# Create specialized sub-agents for comprehensive analysis
nutrition_analyzer_agent = LlmAgent(
    model=MODEL,
    name="Nutrition_Analyzer",
    description="Analyzes nutrition content and health impact of grocery items",
    instruction="""You are a nutrition expert analyzing grocery items for health compatibility.

**YOUR EXPERTISE:**
- Macronutrient analysis (protein, carbs, fat, fiber)
- Micronutrient assessment (vitamins, minerals)
- Health condition compatibility (diabetes, heart health, etc.)
- Cost-effectiveness calculations (nutrients per dollar)
- Meal planning and portion recommendations

**ANALYSIS APPROACH:**
1. **Nutrition Facts Review:** Analyze macronutrient and micronutrient content
2. **Health Scoring:** Rate items for specific health conditions
3. **Cost Analysis:** Calculate nutritional value per dollar spent
4. **Recommendations:** Provide actionable health advice
5. **Substitution Suggestions:** Recommend better alternatives when needed

**RESPONSE FORMAT:**
- Professional nutrition analysis with specific metrics
- Health compatibility scores with explanations
- Cost-effectiveness calculations
- Clear, actionable recommendations
- Evidence-based health advice

Provide comprehensive nutrition analysis for optimal health outcomes."""
)

substitution_agent = LlmAgent(
    model=MODEL,
    name="Substitution_Expert",
    description="Provides smart substitution recommendations for better nutrition and cost",
    instruction="""You are a nutrition and cost optimization expert providing smart substitution recommendations.

**YOUR EXPERTISE:**
- Nutrition-based substitutions (better health outcomes)
- Cost-effective alternatives (same nutrition, lower price)
- Quality upgrades (better nutrition, slightly higher price)
- Dietary restriction accommodations (allergies, preferences)
- Seasonal and availability considerations

**SUBSTITUTION CATEGORIES:**
1. **Health Upgrades:** Better nutrition profile, similar cost
2. **Cost Savers:** Same nutrition, lower price
3. **Quality Improvements:** Premium options with better nutrition
4. **Dietary Accommodations:** Allergen-free or preference-based alternatives
5. **Seasonal Alternatives:** Fresh, local, or seasonal options

**ANALYSIS APPROACH:**
- Compare nutrition profiles (macros, micros, additives)
- Calculate cost per nutrient ratios
- Consider preparation methods and cooking impact
- Factor in availability and seasonality
- Provide clear before/after comparisons

**RESPONSE FORMAT:**
- Specific substitution recommendations with reasoning
- Nutrition comparison (before vs after)
- Cost impact analysis
- Preparation tips and cooking considerations
- Clear implementation guidance

Provide smart, practical substitution recommendations for better health and value."""
)

# Main Root Agent (This is what ADK web looks for as root_agent)
root_agent = LlmAgent(
    model=MODEL,
    name="Nutrition_Root_Agent",
    description="Main nutrition analysis agent coordinating specialized sub-agents",
    instruction="""You are the main Nutrition Analysis Agent for GrocerEase AI, coordinating specialized nutrition experts.

**YOUR ROLE:** Orchestrate comprehensive nutrition analysis using USDA data and specialized sub-agents.

**COORDINATION APPROACH:**
1. **USDA Data Integration:** Fetch official nutrition facts from USDA FoodData Central
2. **Specialized Analysis:** Delegate to nutrition analyzer and substitution expert
3. **Comprehensive Reporting:** Combine insights into actionable recommendations
4. **Health Focus:** Prioritize health outcomes and cost-effectiveness
5. **User Guidance:** Provide clear, implementable advice

**ANALYSIS WORKFLOW:**
- Load shopping list from Agent 1 (Budget Tracker)
- Fetch USDA nutrition data for each item
- Analyze nutrition content and health impact
- Calculate cost-effectiveness and nutrient density
- Provide substitution recommendations
- Generate comprehensive health report

**RESPONSE STRUCTURE:**
- Executive summary of nutrition analysis
- Item-by-item USDA nutrition facts
- Health compatibility scoring
- Cost-effectiveness analysis
- Smart substitution recommendations
- Actionable health advice

**DATA SOURCE:** USDA FoodData Central + SNAP/WIC Program Database

    **Try me with:** "Analyze my shopping list for SNAP benefits: Chicken Breast, Whole Wheat Bread, Milk, Eggs" 
    
    I'll provide comprehensive nutrition analysis with SNAP/WIC program optimization! """,
    sub_agents=[nutrition_analyzer_agent, substitution_agent],
)
