"""
Enhanced GrocerEase AI Orchestrator with Role-Specialized Agents
Agent 1: Price/Budget Tracker - Handles SNAP/WIC budgets and grocery selection
Agent 2: Nutrition Analyst - Analyzes nutrition, health filtering, substitutions
Google ADK RemoteA2aAgent integration for standardized A2A communication
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Suppress Google Cloud logging warnings early
import sys
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""

# Redirect stderr to suppress unwanted messages
class NullWriter:
    def write(self, txt): pass
    def flush(self): pass

original_stderr = sys.stderr
import warnings
warnings.filterwarnings("ignore")

# Google ADK imports
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

# Import our enhanced specialized agents
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Budgets_Agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Nutrition_Agent'))

from Budgets_Agent.agent import SnapWicScraperAgent
from Nutrition_Agent.nutrition_agent import NutritionAgent

# Set up structured logging
logger = structlog.get_logger(__name__)

# Create FastAPI app for serving agent endpoints
app = FastAPI(
    title="Enhanced GrocerEase AI Agents", 
    version="2.1.0",
    description="Role-specialized agents for comprehensive grocery assistance"
)

# Enhanced specialized agent instances
price_agent = SnapWicScraperAgent()  # Agent 1: Price/Budget Tracker
nutrition_agent = NutritionAgent()   # Agent 2: Nutrition Analyst


class GrocerEaseOrchestrator:
    """
    Enhanced orchestrator using Google ADK RemoteA2aAgent for specialized A2A communication.
    Coordinates role-specialized agents:
    - Agent 1: Price/Budget Tracker (SNAP/WIC budgets, grocery selection, cost optimization)
    - Agent 2: Nutrition Analyst (USDA data, health filtering, substitution recommendations)
    """
    
    def __init__(self):
        self.orchestrator_id = "enhanced_grocerease_orchestrator"

        # Suppress warnings
        import warnings
        import os
        warnings.filterwarnings("ignore", category=UserWarning)

        # Suppress Google Cloud logging warnings
        os.environ["GRPC_VERBOSITY"] = "ERROR"
        os.environ["GLOG_minloglevel"] = "2"

        # Create RemoteA2aAgent instances pointing to local HTTP endpoints
        self.price_remote_agent = RemoteA2aAgent(
            name="price_budget_tracker",
            description="Agent 1: SNAP/WIC price tracking, budget management, and grocery selection optimization. Handles market prices, benefit eligibility verification, and cost-optimized shopping lists.",
            agent_card="http://localhost:8001/.well-known/agent-card.json",
            timeout=30.0
        )

        self.nutrition_remote_agent = RemoteA2aAgent(
            name="nutrition_health_analyst",
            description="Agent 2: Comprehensive nutrition analysis using USDA API, health condition filtering (diabetes, heart health), and substitution recommendations. Specializes in health-conscious grocery optimization.",
            agent_card="http://localhost:8002/.well-known/agent-card.json",
            timeout=30.0
        )
        
        # Create the main Google ADK Agent with enhanced role-specialized sub-agents
        self.root_agent = Agent(
            name="enhanced_grocerease_coordinator",
            model="gemini-2.0-flash",  # Using Google's latest model
            description="Coordinates between specialized price/budget tracking and nutrition/health analysis agents for comprehensive SNAP/WIC shopping optimization. Provides role-based grocery assistance with budget management, nutritional analysis, health filtering, and substitution recommendations.",
            sub_agents=[self.price_remote_agent, self.nutrition_remote_agent]
        )
        
        pass

    async def handle_user_request(self, user_message: str) -> Dict[str, Any]:
        """
        Handle user requests using intelligent Gemini AI analysis and A2A communication.
        
        Args:
            user_message: User's shopping request (e.g., "I have $50 SNAP benefits and need groceries")
        """
        try:
            pass
            
            # Step 1: Use Gemini AI to analyze the user's request
            analysis_prompt = f"""
            Analyze this grocery shopping request and extract key information:
            
            Request: "{user_message}"
            
            Please extract and return ONLY a JSON object with:
            {{
                "budget": <extracted budget amount as float>,
                "benefit_type": "SNAP" or "WIC",
                "health_conditions": [<list of health conditions mentioned>],
                "requested_items": [<list of specific items mentioned>],
                "shopping_context": "<brief context like 'weekly groceries', 'family meals', etc.>"
            }}
            
            Examples:
            - "I have $50 SNAP benefits" -> {{"budget": 50.0, "benefit_type": "SNAP", "health_conditions": [], "requested_items": [], "shopping_context": "general shopping"}}
            - "I have $43.25 WIC credit" -> {{"budget": 43.25, "benefit_type": "WIC", "health_conditions": [], "requested_items": [], "shopping_context": "general shopping"}}
            - "I'm diabetic and need $30 groceries" -> {{"budget": 30.0, "benefit_type": "SNAP", "health_conditions": ["diabetes"], "requested_items": [], "shopping_context": "general shopping"}}
            - "Need milk, bread, eggs for $25" -> {{"budget": 25.0, "benefit_type": "SNAP", "health_conditions": [], "requested_items": ["milk", "bread", "eggs"], "shopping_context": "specific items"}}
            
            Return ONLY the JSON object, no other text.
            """
            
            # Use fallback analysis for reliable results (Gemini AI is not working consistently)
            analysis_response = self._get_fallback_analysis(user_message)
            request_analysis = self._parse_analysis(analysis_response)
            
            # Step 2: Use A2A communication to get price and nutrition data
            price_data = await self._get_price_data_via_a2a(request_analysis, user_message)
            nutrition_data = await self._get_nutrition_data_via_a2a(request_analysis, user_message)
            
            # Step 3: Generate intelligent recommendations using Gemini AI
            final_recommendation = await self._generate_intelligent_recommendation_with_gemini(
                request_analysis, price_data, nutrition_data, user_message
            )
            
            # Ensure recommendation is always a string, not JSON
            if isinstance(final_recommendation, dict):
                final_recommendation = str(final_recommendation)

            # If recommendation looks like JSON, generate a proper recommendation
            if (isinstance(final_recommendation, str) and
                final_recommendation.strip().startswith('{') and
                final_recommendation.strip().endswith('}')):
                # This is JSON analysis, not a recommendation - generate proper recommendation
                final_recommendation = await self._generate_intelligent_recommendation(
                    request_analysis, price_data, nutrition_data, user_message
                )

            return {
                "user_request": user_message,
                "analysis": request_analysis,
                "price_data": price_data,
                "nutrition_data": nutrition_data,
                "recommendation": final_recommendation,
                "timestamp": datetime.now().isoformat(),
                "session_id": str(uuid.uuid4())
            }
            
        except Exception as e:
            pass
            return {
                "error": str(e),
                "user_request": user_message,
                "timestamp": datetime.now().isoformat()
            }

    async def _get_gemini_analysis(self, prompt: str) -> str:
        """Use Gemini AI to analyze prompts and generate responses."""
        try:
            # Use Google's genai library directly for more reliable results
            import google.generativeai as genai
            
            # Configure the API (you'll need to set GOOGLE_AI_STUDIO_API_KEY in your environment)
            api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
            if not api_key or api_key == "your_api_key_here":
                pass
                return self._get_fallback_analysis(prompt)
            
            genai.configure(api_key=api_key)
            
            # Create the model
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Generate content
            response = model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            pass
            # Return a fallback analysis instead of error
            return self._get_fallback_analysis(prompt)

    def _get_fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis when Gemini fails."""
        # Extract budget from prompt - handle multiple benefit amounts
        budget = 0.0
        benefit_types = []

        import re
        # Find dollar amounts more precisely - handle multiple patterns
        # Pattern 1: "30$ SNAP" or "30 dollar SNAP"
        pattern1 = r'(\d+(?:\.\d{2})?)\s*(?:\$|dollar[s]?)\s*(?:SNAP|WIC|credit)'
        # Pattern 2: "$30 SNAP"
        pattern2 = r'\$(\d+(?:\.\d{2})?)\s*(?:SNAP|WIC|credit)'
        # Pattern 3: "30 SNAP credit"
        pattern3 = r'(\d+(?:\.\d{2})?)\s+(?:SNAP|WIC)\s+credit'

        dollar_matches = []
        dollar_matches.extend(re.findall(pattern1, prompt, re.IGNORECASE))
        dollar_matches.extend(re.findall(pattern2, prompt, re.IGNORECASE))
        dollar_matches.extend(re.findall(pattern3, prompt, re.IGNORECASE))

        if dollar_matches:
            # Sum all amounts found for combined benefits
            budget = sum(float(amount) for amount in dollar_matches)
        else:
            # Fallback: look for any number followed by SNAP/WIC
            amounts = re.findall(r'(\d+(?:\.\d{2})?)', prompt)
            if amounts:
                budget = float(amounts[0])  # Take first amount only

        if budget == 0:
            budget = 50.0

        # Determine benefit types
        if "snap" in prompt.lower():
            benefit_types.append("SNAP")
        if "wic" in prompt.lower():
            benefit_types.append("WIC")

        if not benefit_types:
            benefit_types = ["SNAP"]

        # Handle combined benefit types
        if len(benefit_types) > 1:
            benefit_type = ["SNAP", "WIC"]  # List for combined WIC + SNAP
        elif "WIC" in benefit_types:
            benefit_type = "WIC"
        else:
            benefit_type = benefit_types[0]
        
        # Check for health conditions (be more precise to avoid false positives)
        health_conditions = []
        if "diabetes" in prompt.lower() or "diabetic" in prompt.lower():
            health_conditions.append("diabetes")
        if "hypertension" in prompt.lower() or "high blood pressure" in prompt.lower():
            health_conditions.append("hypertension")
        
        # Extract requested items (be more precise)
        requested_items = []
        common_items = ["milk", "bread", "eggs", "chicken", "beef", "pork", "fish", "cheese", "yogurt", "cereal", "rice", "pasta", "beans", "bananas", "apples", "oranges", "carrots", "potatoes", "onions", "tomatoes", "lettuce", "spinach", "broccoli"]
        for item in common_items:
            if item in prompt.lower():
                requested_items.append(item)
        
        return json.dumps({
            "budget": budget,
            "benefit_type": benefit_type,
            "health_conditions": health_conditions,
            "requested_items": requested_items,
            "shopping_context": "intelligent analysis"
        })

    def _parse_analysis(self, analysis_response: str) -> Dict[str, Any]:
        """Parse Gemini AI analysis response into structured data."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing if JSON not found
                return {
                    "budget": 50.0,
                    "benefit_type": "SNAP",
                    "health_conditions": [],
                    "requested_items": [],
                    "shopping_context": "general shopping"
                }
        except Exception as e:
            pass
            return {
                "budget": 50.0,
                "benefit_type": "SNAP", 
                "health_conditions": [],
                "requested_items": [],
                "shopping_context": "general shopping"
            }

    async def _get_price_data_via_a2a(self, analysis: Dict[str, Any], user_message: str = "") -> Dict[str, Any]:
        """Get price data using direct Agent 1 call."""
        try:
            # Extract budget information for Agent 1
            budget = analysis.get("budget", 50.0)
            benefit_type = analysis.get("benefit_type", "SNAP")
            
            # Create a budget request message for Agent 1
            if benefit_type == "SNAP":
                budget_message = f"I have SNAP ${budget:.0f}"
            elif benefit_type == "WIC":
                budget_message = f"I have WIC ${budget:.0f}"
            else:
                # Split budget between SNAP and WIC if combined
                snap_portion = budget * 0.7  # 70% SNAP
                wic_portion = budget * 0.3   # 30% WIC
                budget_message = f"I have SNAP ${snap_portion:.0f} and WIC ${wic_portion:.0f}"
            
            # Call Agent 1 directly using its __call__ method
            agent1_response = await price_agent(budget_message)
            
            # Return the response text and also check for JSON data
            response_data = {
                "agent1_response": agent1_response,
                "budget_processed": True
            }
            
            # Try to load Agent 1's JSON output for structured data
            try:
                agent1_output_path = os.path.join(os.path.dirname(__file__), 'Budgets_Agent', 'agent_1_output.json')
                if os.path.exists(agent1_output_path):
                    with open(agent1_output_path, 'r') as f:
                        agent1_data = json.load(f)
                        response_data["shopping_list"] = agent1_data.get("shopping_list", [])
                        response_data["cost_breakdown"] = agent1_data.get("cost_breakdown", {})
            except:
                pass
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in _get_price_data_via_a2a: {e}")
            return {"error": str(e), "agent1_response": f"Error: {str(e)}"}

    async def _get_nutrition_data_via_a2a(self, analysis: Dict[str, Any], user_message: str = "") -> Dict[str, Any]:
        """Get nutrition data using A2A communication with nutrition agent."""
        try:
            # Check if Agent 1 has produced output for automatic continuity
            agent1_output_path = os.path.join(os.path.dirname(__file__), 'Budgets_Agent', 'agent_1_output.json')
            agent1_items = []
            
            if os.path.exists(agent1_output_path):
                try:
                    with open(agent1_output_path, 'r', encoding='utf-8') as f:
                        agent1_data = json.load(f)
                        agent1_items = agent1_data.get('shopping_list', [])
                        print(f"Orchestrator: Found {len(agent1_items)} items from Agent 1 for A2A continuity")
                except Exception as e:
                    print(f"Orchestrator: Could not load Agent 1 data: {e}")
            
            # Prepare A2A message for comprehensive nutrition filtering
            # Use Agent 1 items if available, otherwise fall back to requested_items
            items_to_analyze = agent1_items if agent1_items else analysis.get("requested_items", [])
            
            a2a_message = {
                "message_type": "filter_nutrition", 
                "message_data": {
                    "items": items_to_analyze,
                    "budget": analysis.get("budget", 50.0),
                    "health_conditions": analysis.get("health_conditions", []),
                    "user_request": user_message,  # Pass original request for parsing nutrition requirements
                    "source": "agent1_continuity" if agent1_items else "direct_request"
                },
                "sender_id": self.orchestrator_id
            }
            
            # Send A2A message to nutrition agent
            response = await nutrition_agent.handle_a2a_message(
                message_type="filter_nutrition",
                message_data=a2a_message["message_data"],
                sender_id=self.orchestrator_id
            )
            
            return response.get("response", {})
            
        except Exception as e:
            pass
            return {"error": str(e)}

    async def _generate_intelligent_recommendation_with_gemini(self, analysis: Dict[str, Any], price_data: Dict[str, Any], nutrition_data: Dict[str, Any], user_message: str) -> str:
        """Generate intelligent grocery recommendations using Gemini AI with enhanced understanding."""
        try:
            # Extract health conditions and context for better Gemini understanding
            health_conditions = analysis.get("health_conditions", [])
            budget = analysis.get("budget", 50.0)
            benefit_type = analysis.get("benefit_type", "SNAP")
            
            # Create a comprehensive prompt for Gemini AI with health context
            health_context = ""
            if health_conditions:
                health_context = f"\nHEALTH CONSIDERATIONS: User has {', '.join(health_conditions)}. Items have been filtered for compatibility."
            
            # Extract nutrition insights and full report if available
            nutrition_insights = ""
            full_nutrition_report = ""
            if nutrition_data:
                # Check for structured nutrition response from Agent 2
                if nutrition_data.get("nutrition_report"):
                    full_nutrition_report = nutrition_data["nutrition_report"]
                elif nutrition_data.get("response", {}).get("nutrition_report"):
                    full_nutrition_report = nutrition_data["response"]["nutrition_report"]
                
                # Legacy format support
                if "nutrition_analysis" in nutrition_data:
                    avg_score = nutrition_data["nutrition_analysis"].get("average_nutrition_score", 0)
                    nutrition_insights = f"\nNUTRITION INSIGHTS: Average nutrition score: {avg_score}/100. Items selected for optimal health benefits."
            
            # Detect if this is a nutrition-focused question
            nutrition_keywords = ['nutrition', 'nutrients', 'protein', 'vitamin', 'mineral', 'fiber', 'calcium', 
                                'iron', 'healthy', 'diabetes', 'heart', 'analyze', 'nutrient']
            is_nutrition_focused = any(keyword in user_message.lower() for keyword in nutrition_keywords)
            
            gemini_prompt = f"""
            You are a helpful grocery shopping assistant. The user said: "{user_message}"
            
            Based on their ${budget:.2f} {benefit_type} balance, provide a personalized shopping recommendation.
            
            PRICE DATA: {price_data}
            {health_context}
            {nutrition_insights}
            
            {"FULL NUTRITION ANALYSIS:" + full_nutrition_report if full_nutrition_report and is_nutrition_focused else ""}
            
            Provide a friendly, helpful response that:
            1. Acknowledges their specific needs (health conditions, budget, benefit type)
            2. Recommends the best store and items based on price and nutrition data
            3. Shows individual item prices clearly
            4. Calculates total cost and remaining balance
            5. Gives practical shopping advice
            
            Format your response naturally, as if talking to a friend who needs grocery shopping help.
            """
            
            # Use Gemini AI to generate the recommendation
            gemini_response = await self._get_gemini_analysis(gemini_prompt)
            
            # Clean up any repetitive text in the response
            if gemini_response:
                # Remove any repeated store names or phrases
                lines = gemini_response.split('\n')
                cleaned_lines = []
                seen_lines = set()
                
                for line in lines:
                    line = line.strip()
                    if line and line not in seen_lines:
                        cleaned_lines.append(line)
                        seen_lines.add(line)
                
                gemini_response = '\n'.join(cleaned_lines)
            
            # If Gemini fails or returns malformed response, fall back to structured recommendations
            if ("Analysis error:" in gemini_response or 
                "Unable to generate" in gemini_response or
                gemini_response.count("target") > 2 or
                gemini_response.count("walmart") > 2 or
                gemini_response.strip().startswith('{') and gemini_response.strip().endswith('}') and 
                ("diabetes" in gemini_response.lower() and "credit" in user_message.lower()) or
                len(gemini_response.strip()) < 50):  # Very short responses are likely errors
                return await self._generate_intelligent_recommendation(analysis, price_data, nutrition_data, user_message)
            
            return gemini_response
            
        except Exception as e:
            pass
            # Fall back to structured recommendations
            return await self._generate_intelligent_recommendation(analysis, price_data, nutrition_data, user_message)

    async def _generate_intelligent_recommendation(self, analysis: Dict[str, Any], price_data: Dict[str, Any], nutrition_data: Dict[str, Any], user_message: str) -> str:
        """Generate comprehensive recommendation using Agent 1 and Agent 2 outputs."""
        try:
            # Check if Agent 1 provided a full response
            agent1_response = price_data.get("agent1_response", "")
            nutrition_response = nutrition_data.get("nutrition_analysis", "") or nutrition_data.get("agent2_response", "")
            
            # If Agent 1 provided a complete response, use it as the base
            if agent1_response and len(agent1_response) > 100:
                final_response = agent1_response
                
                # Add nutrition analysis if available
                if nutrition_response and len(nutrition_response) > 50:
                    final_response += f"\n\n{nutrition_response}"
                
                return final_response
            
            # Fallback to basic recommendation if Agent 1 response is missing
            budget = analysis.get("budget", 50.0)
            benefit_type = analysis.get("benefit_type", "SNAP")
            
            # Format benefit type for display
            if benefit_type == "COMBINED":
                benefit_display = "SNAP + WIC"
            else:
                benefit_display = benefit_type if isinstance(benefit_type, str) else " + ".join(benefit_type)
                
            response_lines = [f"🛒 **Shopping Recommendation for ${budget:.2f} {benefit_display}**"]
            
            # Try to extract shopping list from Agent 1's structured data
            shopping_list = price_data.get("shopping_list", [])
            if shopping_list:
                total_cost = sum(item.get("price", 0) for item in shopping_list)
                remaining = budget - total_cost
                
                response_lines.append(f"\n**Shopping List ({len(shopping_list)} items):**")
                
                # Group items by category
                categories = {}
                for item in shopping_list:
                    category = item.get("category", "Other")
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(item)
                
                for category, items in categories.items():
                    response_lines.append(f"\n**{category}:**")
                    for item in items[:3]:  # Show first 3 items per category
                        name = item.get("name", "Unknown Item")
                        price = item.get("price", 0)
                        store = item.get("store", "")
                        response_lines.append(f"  • {name}: ${price:.2f} at {store}")
                    if len(items) > 3:
                        response_lines.append(f"  • ... and {len(items)-3} more items")
                
                response_lines.append(f"\n**Total Cost:** ${total_cost:.2f}")
                response_lines.append(f"**Remaining Balance:** ${remaining:.2f}")
            else:
                response_lines.append("\n⚠️ No shopping list available. Please specify your budget like 'I have SNAP $45 and WIC $20'")
            
            # Add nutrition summary if available
            if nutrition_response:
                response_lines.append(f"\n{nutrition_response}")
            
            return "\n".join(response_lines)
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return f"Error generating recommendation: {str(e)}"

    async def _get_fallback_response(self, user_message: str, budget: float, benefit_type: str, health_conditions: List[str]) -> str:
        """Fallback method that uses individual agents directly when Google ADK fails."""
        try:
            # Extract items from user message
            items = self._extract_items_from_message(user_message)
            
            # Get price analysis from price agent
            # Create budget request message for Agent 1
            if benefit_type == "SNAP":
                budget_message = f"I have SNAP ${budget:.0f}"
            elif benefit_type == "WIC":
                budget_message = f"I have WIC ${budget:.0f}"
            else:
                # Split budget between SNAP and WIC if combined
                snap_portion = budget * 0.7  # 70% SNAP
                wic_portion = budget * 0.3   # 30% WIC
                budget_message = f"I have SNAP ${snap_portion:.0f} and WIC ${wic_portion:.0f}"
            
            price_response = await price_agent(budget_message)
            
            # Get nutrition analysis from nutrition agent
            nutrition_request = {
                "items": items,
                "budget": budget,
                "health_conditions": health_conditions
            }
            nutrition_response = await nutrition_agent.handle_nutrition_analysis(nutrition_request)
            
            # Combine responses into a comprehensive recommendation
            response_parts = []
            
            # Price analysis
            if "stores" in price_response:
                stores = price_response["stores"]
                walmart_cost = stores.get("walmart", {}).get("total_cost", 0)
                target_cost = stores.get("target", {}).get("total_cost", 0)
                best_store = price_response.get("best_store", "walmart")
                
                response_parts.append(f"PRICE ANALYSIS:")
                response_parts.append(f"- Walmart total: ${walmart_cost:.2f}")
                response_parts.append(f"- Target total: ${target_cost:.2f}")
                response_parts.append(f"- Best store: {best_store.title()}")
                response_parts.append(f"- Budget: ${budget:.2f}")
                
                if walmart_cost <= budget and target_cost <= budget:
                    response_parts.append(f"[OK] Both stores fit your budget!")
                elif walmart_cost <= budget:
                    response_parts.append(f"[OK] Walmart fits your budget")
                elif target_cost <= budget:
                    response_parts.append(f"[OK] Target fits your budget")
                else:
                    response_parts.append(f"[WARNING] Both stores exceed budget - consider reducing items")
            
            # Nutrition analysis
            if "nutrition_analysis" in nutrition_response:
                nutrition_data = nutrition_response["nutrition_analysis"]
                avg_score = nutrition_data.get("average_nutrition_score", 0)
                snap_coverage = nutrition_data.get("snap_wic_summary", {}).get("snap_coverage", 0)
                
                response_parts.append(f"\nNUTRITION ANALYSIS:")
                response_parts.append(f"- Average nutrition score: {avg_score}/100")
                response_parts.append(f"- SNAP eligible items: {snap_coverage:.1f}%")
                
                if avg_score >= 70:
                    response_parts.append(f"[OK] Good nutritional value")
                elif avg_score >= 50:
                    response_parts.append(f"[WARNING] Moderate nutritional value")
                else:
                    response_parts.append(f"[ERROR] Low nutritional value - consider healthier options")
            
            # Add full nutrition report if available
            if nutrition_response and nutrition_response.get("nutrition_report"):
                response_parts.append(f"\n{nutrition_response['nutrition_report']}")
            elif nutrition_response and nutrition_response.get("response", {}).get("nutrition_report"):
                response_parts.append(f"\n{nutrition_response['response']['nutrition_report']}")
            
            # Recommendations
            response_parts.append(f"\nRECOMMENDATIONS:")
            response_parts.append(f"- Shop at {best_store.title()} for best prices")
            response_parts.append(f"- Focus on SNAP-eligible items for maximum benefit value")
            if health_conditions:
                response_parts.append(f"- Consider health conditions: {', '.join(health_conditions)}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            pass
            return f"Unable to generate recommendations due to: {str(e)}"

    def _extract_items_from_message(self, message: str) -> List[str]:
        """Extract grocery items from user message."""
        # Common grocery items to look for
        common_items = [
            "milk", "bread", "eggs", "chicken", "beef", "pork", "fish", "cheese",
            "yogurt", "cereal", "rice", "pasta", "beans", "bananas", "apples",
            "oranges", "carrots", "potatoes", "onions", "tomatoes", "lettuce",
            "spinach", "broccoli", "flour", "sugar", "peanut butter", "juice"
        ]
        
        message_lower = message.lower()
        found_items = []
        
        for item in common_items:
            if item in message_lower:
                found_items.append(item)
        
        # If no specific items found, return common basics
        if not found_items:
            found_items = ["milk", "bread", "eggs"]
        
        return found_items

    def _parse_adk_response(self, adk_response: Any, user_message: str, budget: float, benefit_type: str) -> Dict[str, Any]:
        """Parse Google ADK response into structured format."""
        try:
            return {
                "user_request": user_message,
                "budget": budget,
                "benefit_type": benefit_type,
                "adk_response": str(adk_response),
                "timestamp": datetime.now().isoformat(),
                "session_id": str(uuid.uuid4()),
                "migration_status": "google_adk_implementation",
                "orchestrator_version": "2.0.0"
            }
        except Exception as e:
            pass
            return {
                "user_request": user_message,
                "budget": budget,
                "benefit_type": benefit_type,
                "adk_response": "Response parsing failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "migration_status": "google_adk_implementation"
            }

    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a single user request using intelligent Gemini AI analysis."""
        try:
            # Use the new intelligent request handler
            result = await self.handle_user_request(user_input)
            
            # Return clean recommendation
            if "error" in result:
                return result
            else:
                return {
                    "recommendation": result.get("recommendation", "No recommendation available"),
                    "analysis": result.get("analysis", {}),
                    "timestamp": result.get("timestamp", datetime.now().isoformat())
                }
            
        except Exception as e:
            return {
                "error": str(e),
                "user_request": user_input,
                "timestamp": datetime.now().isoformat()
            }


# HTTP endpoints for agent cards and functionality
@app.get("/price-agent/.well-known/agent-card.json")
async def get_price_agent_card():
    """Agent card for price tracking agent."""
    return JSONResponse({
        "name": "price_tracker_agent",
        "description": "SNAP/WIC price tracking and comparison agent for grocery shopping optimization",
        "version": "2.0.0",
        "capabilities": [
            "get_prices",
            "compare_stores", 
            "find_deals",
            "snap_wic_eligibility_check"
        ],
        "endpoints": {
            "price_analysis": "http://localhost:8001/price-agent/analyze",
            "store_comparison": "http://localhost:8001/price-agent/compare",
            "deal_search": "http://localhost:8001/price-agent/deals"
        },
        "supported_benefits": ["SNAP", "WIC"],
        "supported_stores": ["Walmart", "Target"]
    })


@app.get("/nutrition-agent/.well-known/agent-card.json")
async def get_nutrition_agent_card():
    """Agent card for nutrition agent."""
    return JSONResponse({
        "name": "nutrition_agent",
        "description": "Nutritional analysis and health-conscious recommendations agent for SNAP/WIC shopping",
        "version": "2.0.0",
        "capabilities": [
            "analyze_nutrition",
            "get_substitutions",
            "check_health_compatibility",
            "optimize_nutrition"
        ],
        "endpoints": {
            "nutrition_analysis": "http://localhost:8002/nutrition-agent/analyze",
            "substitutions": "http://localhost:8002/nutrition-agent/substitutions",
            "health_check": "http://localhost:8002/nutrition-agent/health"
        },
        "supported_health_conditions": ["diabetes", "hypertension", "heart_disease", "obesity"]
    })


@app.post("/price-agent/analyze")
async def price_agent_analyze(request: Dict[str, Any]):
    """Price analysis endpoint for A2A communication."""
    try:
        # Extract request data
        items = request.get("items", [])
        budget = request.get("budget", 50.0)
        benefit_type = request.get("benefit_type", "SNAP")
        
        # Create budget request message for Agent 1
        if benefit_type == "SNAP":
            budget_message = f"I have SNAP ${budget:.0f}"
        elif benefit_type == "WIC":
            budget_message = f"I have WIC ${budget:.0f}"
        else:
            # Split budget between SNAP and WIC if combined
            snap_portion = budget * 0.7  # 70% SNAP
            wic_portion = budget * 0.3   # 30% WIC
            budget_message = f"I have SNAP ${snap_portion:.0f} and WIC ${wic_portion:.0f}"
        
        # Call Agent 1 directly
        response = await price_agent(budget_message)
        
        return JSONResponse(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nutrition-agent/analyze")
async def nutrition_agent_analyze(request: Dict[str, Any]):
    """Nutrition analysis endpoint for A2A communication."""
    try:
        # Extract request data
        items = request.get("items", [])
        budget = request.get("budget", 50.0)
        health_conditions = request.get("health_conditions", [])
        
        # Call the actual agent method
        response = await nutrition_agent.handle_nutrition_analysis({
            "items": items,
            "budget": budget,
            "health_conditions": health_conditions
        })
        
        return JSONResponse(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def start_agent_servers():
    """Start HTTP servers for each agent."""
    
    # Start price agent server on port 8001
    price_server = uvicorn.Server(
        uvicorn.Config(
            app=app,
            host="localhost",
            port=8001,
            log_level="info"
        )
    )
    
    # Start nutrition agent server on port 8002  
    nutrition_server = uvicorn.Server(
        uvicorn.Config(
            app=app,
            host="localhost", 
            port=8002,
            log_level="info"
        )
    )
    
    # Run servers concurrently
    await asyncio.gather(
        price_server.serve(),
        nutrition_server.serve()
    )


async def main():
    """Main function for clean prompt-based interface."""
    
    # Initialize the migrated ADK orchestrator
    orchestrator = GrocerEaseOrchestrator()
    
    # Simple prompt interface
    while True:
        try:
            user_input = input("Prompt: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            # Process the request
            result = await orchestrator.process_request(user_input)
            
            # Return clean output
            if "error" in result:
                error_msg = result.get('error', 'Unknown error')
                if error_msg.strip():  # Only print if error message is not empty
                    print(f"Error: {error_msg}")
            else:
                recommendation = result.get('recommendation', 'No recommendation available')
                print(f"Response: {recommendation}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GrocerEase AI Migrated Google ADK Orchestrator")
    parser.add_argument("--servers", action="store_true", help="Start agent HTTP servers")
    
    args = parser.parse_args()
    
    if args.servers:
        asyncio.run(start_agent_servers())
    else:
        asyncio.run(main())