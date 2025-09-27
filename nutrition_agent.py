# GrocerEase AI - Root Agent for my_env
# This file should be importable as my_env.root_agent (from my_env.nutrition_agent import root_agent)

from google.adk.agents import LlmAgent
import json
import os
import requests
import time
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model configuration
MODEL = "gemini-2.0-flash-001"

# USDA FoodData Central API Configuration
USDA_API_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
# Get your free API key at: https://fdc.nal.usda.gov/api-key-signup
# Replace DEMO_KEY with your actual API key for production use
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")  

def get_api_key_info():
    """Provide information about getting a USDA API key"""
    if USDA_API_KEY == "DEMO_KEY" or not USDA_API_KEY:
        return """
        🚨 Currently using DEMO_KEY for USDA API (limited to 30 requests/hour)
        
        To set up your USDA API key:
        1. Visit: https://fdc.nal.usda.gov/api-key-signup
        2. Sign up with your email to get your free API key
        3. Open the .env file in your project root
        4. Replace 'your_actual_api_key_here' with your real API key
        5. Restart the application
        
        With a real API key, you get 1,000 requests/hour!
        """
    else:
        return f"✅ Using API key from .env file: {'*' * (len(USDA_API_KEY) - 8)}{USDA_API_KEY[-4:]} (1,000 requests/hour)"

# Simple in-memory cache to avoid repeated API calls
_food_cache = {}
_last_api_call = 0

# Configuration for API reliability
MAX_RETRIES = 2
TIMEOUT_SECONDS = 15

# USDA API Helper Functions
def search_food_usda(query: str) -> Optional[Dict[str, Any]]:
    """Search for food items using USDA FoodData Central API with retry logic"""
    global _last_api_call
    
    # Simple rate limiting - USDA allows 1000 requests/hour
    current_time = time.time()
    if current_time - _last_api_call < 4:  # Wait at least 4 seconds between calls
        time.sleep(4 - (current_time - _last_api_call))
    
    # Check cache first
    cache_key = query.lower().strip()
    if cache_key in _food_cache:
        return _food_cache[cache_key]
    
    # Retry logic for API calls
    for attempt in range(MAX_RETRIES):
        try:
            url = f"{USDA_API_BASE_URL}/foods/search"
            params = {
                'api_key': USDA_API_KEY,
                'query': query,
                'dataType': ['Foundation', 'SR Legacy'],  # Focus on foundational and standard reference data
                'pageSize': 3  # Limit results to top 3 matches
            }
            
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
            _last_api_call = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('foods') and len(data['foods']) > 0:
                    # Return the first (most relevant) match
                    food_item = data['foods'][0]
                    _food_cache[cache_key] = food_item
                    return food_item
            elif response.status_code == 429:  # Rate limit exceeded
                print(f"USDA API rate limit exceeded. Waiting...")
                time.sleep(60)  # Wait 1 minute before retry
                continue
            else:
                print(f"USDA API returned status {response.status_code} for '{query}'")
            
            break  # Exit retry loop if we get a response (even if unsuccessful)
            
        except requests.exceptions.Timeout:
            print(f"USDA API timeout for '{query}' (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            print(f"USDA API connection error for '{query}': {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"Unexpected USDA API error for '{query}': {e}")
            break
    
    return None

def get_food_details_usda(fdc_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed food information by FDC ID"""
    global _last_api_call
    
    current_time = time.time()
    if current_time - _last_api_call < 4:
        time.sleep(4 - (current_time - _last_api_call))
    
    try:
        url = f"{USDA_API_BASE_URL}/food/{fdc_id}"
        params = {'api_key': USDA_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        _last_api_call = time.time()
        
        if response.status_code == 200:
            return response.json()
        
        return None
        
    except Exception as e:
        print(f"USDA API error for FDC ID {fdc_id}: {e}")
        return None

def extract_nutrition_from_usda(food_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract nutrition information from USDA API response"""
    if not food_data or 'foodNutrients' not in food_data:
        return {}
    
    # Map USDA nutrient IDs to our fields
    nutrient_map = {
        208: 'calories',     # Energy (kcal)
        203: 'protein',      # Protein (g)
        291: 'fiber',        # Fiber (g) 
        269: 'sugar',        # Sugars, total (g)
        307: 'sodium'        # Sodium (mg)
    }
    
    nutrition = {}
    for nutrient in food_data['foodNutrients']:
        nutrient_id = nutrient.get('nutrient', {}).get('id')
        if nutrient_id in nutrient_map:
            value = nutrient.get('amount', 0)
            nutrition[nutrient_map[nutrient_id]] = round(value, 1)
    
    # Calculate nutrition score (0-100) based on protein, fiber, and penalties for sugar/sodium
    protein = nutrition.get('protein', 0)
    fiber = nutrition.get('fiber', 0)
    sugar = nutrition.get('sugar', 0)
    sodium = nutrition.get('sodium', 0)
    
    # Base score from protein and fiber content
    score = min(100, (protein * 3) + (fiber * 5))
    
    # Penalties for high sugar and sodium
    if sugar > 10:
        score -= (sugar - 10) * 2
    if sodium > 500:
        score -= (sodium - 500) / 10
        
    nutrition['nutrition_score'] = max(0, min(100, round(score, 1)))
    
    return nutrition

def get_food_nutrition_usda(food_name: str) -> Dict[str, Any]:
    """Get nutrition data for a food item using USDA API"""
    # First search for the food
    search_result = search_food_usda(food_name)
    
    if not search_result:
        # Return default values if not found
        return {
            'calories': 0,
            'protein': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0,
            'nutrition_score': 50,
            'category': 'unknown',
            'price': 2.99,  # Default estimated price
            'protein_per_dollar': 0
        }
    
    # Extract basic nutrition from search result
    nutrition = extract_nutrition_from_usda(search_result)
    
    # Add category classification
    food_category_obj = search_result.get('foodCategory', {})
    if isinstance(food_category_obj, dict):
        food_category = food_category_obj.get('description', '').lower()
    elif isinstance(food_category_obj, str):
        food_category = food_category_obj.lower()
    else:
        food_category = str(food_category_obj).lower() if food_category_obj else ''
    
    # Also check the food description for classification
    food_description = search_result.get('description', '').lower()
    food_text = f"{food_category} {food_description}"
    
    category = 'unknown'
    
    if any(word in food_text for word in ['meat', 'poultry', 'fish', 'egg', 'bean', 'legume', 'chicken', 'beef', 'pork', 'salmon', 'tuna']):
        category = 'protein'
    elif any(word in food_text for word in ['grain', 'bread', 'cereal', 'rice', 'flour', 'wheat', 'oat']):
        category = 'grain'  
    elif any(word in food_text for word in ['vegetable', 'green', 'spinach', 'broccoli', 'carrot', 'lettuce']):
        category = 'vegetable'
    elif any(word in food_text for word in ['fruit', 'apple', 'banana', 'orange', 'berry']):
        category = 'fruit'
    
    nutrition['category'] = category
    
    # Estimate price based on category and protein content
    protein_content = nutrition.get('protein', 0)
    if category == 'protein':
        nutrition['price'] = max(3.99, protein_content * 0.4 + 2.0)
    elif category == 'grain':
        nutrition['price'] = max(1.99, protein_content * 0.2 + 1.5)
    elif category == 'vegetable':
        nutrition['price'] = max(1.49, protein_content * 0.3 + 1.0)
    elif category == 'fruit':
        nutrition['price'] = max(1.29, protein_content * 0.5 + 1.0)
    else:
        nutrition['price'] = 2.99
        
    # Calculate protein per dollar
    if nutrition['price'] > 0 and protein_content > 0:
        nutrition['protein_per_dollar'] = round(protein_content / nutrition['price'], 1)
    else:
        nutrition['protein_per_dollar'] = 0
    
    return nutrition

# Load SNAP/WIC data from JSON file
def load_snap_wic_data():
    """Load SNAP/WIC eligible items and pricing data"""
    try:
        # Get the directory of the current file and go up one level to find snap_wic_data.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        json_path = os.path.join(parent_dir, 'snap_wic_data.json')
        
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ snap_wic_data.json not found. Using minimal data.")
        return {"snap_eligible_items": {}, "budget_constraints": {}}
    except Exception as e:
        print(f"⚠️ Error loading SNAP/WIC data: {e}")
        return {"snap_eligible_items": {}, "budget_constraints": {}}

# Global variable to store SNAP/WIC data
SNAP_WIC_DATA = load_snap_wic_data()

def find_snap_wic_item(food_name: str):
    """Find food item in SNAP/WIC database"""
    food_name_lower = food_name.lower().strip()
    
    # Search through all categories in SNAP eligible items
    for category, items in SNAP_WIC_DATA.get('snap_eligible_items', {}).items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    item_name = item.get('name', '').lower()
                    if food_name_lower in item_name or item_name in food_name_lower:
                        return item
                    # Check for partial matches
                    food_words = food_name_lower.split()
                    item_words = item_name.split()
                    if any(word in item_name for word in food_words) or any(word in food_name_lower for word in item_words):
                        return item
    return None

def get_nutrition_analysis(food_items):
    """Enhanced nutrition analysis function using USDA API with SNAP/WIC data integration"""
    results = []
    total_cost = 0
    snap_eligible_count = 0
    wic_eligible_count = 0
    
    for item in food_items:
        item_name = item.lower().strip()
        
        # Try USDA API first
        food_data = get_food_nutrition_usda(item_name)
        
        # Try to find in SNAP/WIC database for additional information
        snap_wic_item = find_snap_wic_item(item_name)
        
        # If we have SNAP/WIC data, use it to enhance the food data
        if snap_wic_item:
            # Use SNAP/WIC pricing if available
            if 'average_price' in snap_wic_item:
                food_data['price'] = snap_wic_item['average_price']
            
            # Get nutrition priority from SNAP/WIC data
            priority_scores = SNAP_WIC_DATA.get('nutrition_scoring', {})
            nutrition_priority = snap_wic_item.get('nutrition_priority', 'medium')
            if nutrition_priority in priority_scores:
                # Boost nutrition score based on SNAP/WIC priority
                food_data['nutrition_score'] = max(food_data['nutrition_score'], priority_scores[nutrition_priority])
            
            # Update category from SNAP/WIC data
            food_data['category'] = snap_wic_item.get('category', food_data['category'])
            
            # Track SNAP/WIC eligibility
            if snap_wic_item.get('snap_eligible', False):
                snap_eligible_count += 1
            if snap_wic_item.get('wic_eligible', False):
                wic_eligible_count += 1
        
        # Calculate protein per dollar with updated price
        protein_content = food_data.get('protein', 0)
        if food_data['price'] > 0 and protein_content > 0:
            food_data['protein_per_dollar'] = round(protein_content / food_data['price'], 1)
        else:
            food_data['protein_per_dollar'] = 0
        
        # Format result with SNAP/WIC information
        result_item = {
            "name": item,
            "nutrition_score": food_data["nutrition_score"],
            "protein_per_dollar": food_data.get("protein_per_dollar", 0),
            "category": food_data["category"],
            "price": food_data["price"],
            "calories": food_data.get("calories", 0),
            "protein": food_data.get("protein", 0),
            "fiber": food_data.get("fiber", 0),
            "sugar": food_data.get("sugar", 0),
            "sodium": food_data.get("sodium", 0),
            "snap_eligible": snap_wic_item.get('snap_eligible', False) if snap_wic_item else False,
            "wic_eligible": snap_wic_item.get('wic_eligible', False) if snap_wic_item else False,
            "analysis": f"Nutrition score {food_data['nutrition_score']}/100 (USDA + SNAP/WIC data)" if food_data.get('protein', 0) > 0 else f"Estimated nutrition score {food_data['nutrition_score']}/100"
        }
        
        results.append(result_item)
        total_cost += food_data["price"]
    
    # Get budget constraints for analysis
    budget_constraints = SNAP_WIC_DATA.get('budget_constraints', {})
    weekly_budgets = budget_constraints.get('recommended_weekly_grocery_budget', {})
    
    # Generate SNAP/WIC-focused substitutions and recommendations
    substitutions = []
    budget_recommendations = []
    
    # Check for high-cost items that could be replaced with SNAP/WIC alternatives
    high_cost_items = [r for r in results if r['price'] > 5.0 and not r.get('snap_eligible', False)]
    for item in high_cost_items:
        substitutions.append(f"Consider SNAP-eligible alternative to {item['name']} (${item['price']:.2f}) for budget savings")
    
    # Health-based substitutions
    high_sugar_items = [r for r in results if r.get('sugar', 0) > 10]
    high_sodium_items = [r for r in results if r.get('sodium', 0) > 400]
    low_protein_items = [r for r in results if r.get('protein_per_dollar', 0) < 2.0 and r.get('protein', 0) > 5]
    
    for item in high_sugar_items:
        substitutions.append(f"High sugar alert: {item['name']} has {item.get('sugar', 0)}g sugar")
    
    for item in high_sodium_items:
        substitutions.append(f"High sodium warning: {item['name']} has {item.get('sodium', 0)}mg sodium")
    
    # SNAP/WIC budget analysis
    snap_family_budget = weekly_budgets.get('snap_family_of_4', 62.50)
    wic_family_budget = weekly_budgets.get('wic_family_of_3', 35.00)
    single_snap_budget = weekly_budgets.get('single_person_snap', 35.00)
    
    if total_cost > snap_family_budget:
        budget_recommendations.append(f"Total cost (${total_cost:.2f}) exceeds SNAP family weekly budget (${snap_family_budget:.2f})")
    
    if total_cost > wic_family_budget and wic_eligible_count > 0:
        budget_recommendations.append(f"Consider WIC-eligible items to stay within ${wic_family_budget:.2f} budget")
    
    # Recommend high-value SNAP/WIC items
    if snap_eligible_count < len(results) / 2:
        budget_recommendations.append("Consider adding more SNAP-eligible items for maximum benefit value")
    
    return {
        "total_items": len(results),
        "total_cost": round(total_cost, 2),
        "nutrition_analysis": results,
        "substitutions": substitutions,
        "budget_recommendations": budget_recommendations,
        "snap_wic_summary": {
            "snap_eligible_items": snap_eligible_count,
            "wic_eligible_items": wic_eligible_count,
            "total_items": len(results),
            "snap_coverage": round((snap_eligible_count / len(results)) * 100, 1) if results else 0,
            "wic_coverage": round((wic_eligible_count / len(results)) * 100, 1) if results else 0
        },
        "budget_comparison": {
            "current_cost": round(total_cost, 2),
            "snap_family_weekly_budget": weekly_budgets.get('snap_family_of_4', 62.50),
            "wic_family_weekly_budget": weekly_budgets.get('wic_family_of_3', 35.00),
            "single_snap_weekly_budget": weekly_budgets.get('single_person_snap', 35.00),
            "within_snap_family_budget": total_cost <= weekly_budgets.get('snap_family_of_4', 62.50),
            "within_wic_family_budget": total_cost <= weekly_budgets.get('wic_family_of_3', 35.00)
        },
        "average_nutrition_score": round(sum(r["nutrition_score"] for r in results) / len(results), 1),
        "data_source": "USDA FoodData Central API with SNAP/WIC Program Integration"
    }

# Create Nutrition Analysis Agent
nutrition_analyzer_agent = LlmAgent(
    model=MODEL,
    name="NutritionAnalyzer",
    description="Analyzes food items for nutritional density, health compatibility, and dietary restrictions.",
    instruction="""You are a nutrition expert agent for GrocerEase AI. Analyze food items and provide nutritional scores, 
    health condition compatibility, and dietary restriction compliance. Focus on protein content, fiber, 
    sugar levels, and sodium content. Provide protein-per-dollar calculations and suggest healthier substitutions.
    
    For each food item, evaluate:
    - Nutritional density (protein, fiber content)
    - Health condition compatibility (diabetes = low sugar, hypertension = low sodium)  
    - Protein per dollar value
    - Overall nutrition score (0-100)
    
    Return structured data with scores and recommendations.""",
    disallow_transfer_to_peers=True,
)

# Create Substitution Recommendation Agent
substitution_agent = LlmAgent(
    model=MODEL,
    name="SubstitutionAgent", 
    description="Recommends healthier and more cost-effective food substitutions based on nutritional analysis.",
    instruction="""You are a substitution specialist for GrocerEase AI. Based on nutritional analysis, recommend healthier 
    and more cost-effective alternatives. Consider health conditions like diabetes (low sugar) and 
    hypertension (low sodium). Prioritize high protein-per-dollar ratios and fiber content.
    
    Common substitutions:
    - White bread → Whole wheat bread (higher fiber)
    - Chicken breast → Lentils (more protein per dollar, fiber)
    - High sugar items → Low sugar alternatives for diabetics
    - High sodium items → Low sodium alternatives for hypertension
    
    Provide clear reasoning for each substitution.""",
    disallow_transfer_to_peers=True,
)

# Main Root Agent (This is what ADK web looks for as my_env.root_agent)
root_agent = LlmAgent(
    model=MODEL,
    name="GrocerEase_NutritionAgent",
    description="""GrocerEase AI Nutrition Agent with USDA API and SNAP/WIC program integration. 
    Optimizes shopping lists for nutrition, budget, and government benefit program eligibility.""",
    instruction="""You are the GrocerEase AI Nutrition Agent with comprehensive SNAP/WIC integration. I help optimize grocery shopping lists 
    for maximum nutritional value while ensuring SNAP/WIC eligibility and staying within program budgets.

    **🎯 SNAP/WIC PROGRAM INTEGRATION:**
    I now integrate official SNAP and WIC program data to provide budget-conscious, program-eligible recommendations 
    with real government benefit constraints and approved food items.

    **I specialize in:**
    🥗 **USDA-Accurate Analysis**: Real nutritional data from USDA FoodData Central for precise ratings (0-100)
    💰 **SNAP/WIC Budget Optimization**: Ensuring purchases stay within program weekly/monthly limits
    🏛️ **Program Eligibility**: Identifying SNAP-eligible and WIC-approved items
    🏥 **Health Compatibility**: Filtering for diabetes (low sugar), hypertension (low sodium), and other conditions
    🔄 **Smart Substitutions**: Program-friendly alternatives that maximize benefits
    📊 **Budget Analysis**: Comparing costs against SNAP family ($62.50/week) and WIC family ($35/week) budgets

    **SNAP/WIC Program Coverage:**
    - SNAP Family of 4: $62.50/week budget
    - WIC Family of 3: $35.00/week budget  
    - Single Person SNAP: $35.00/week budget
    - Real program-eligible items with accurate pricing
    - WIC-specific approved items and brands

    **When users share their shopping list, I provide:**
    1. **USDA-Verified Nutrition Scores** (0-100 for each item)
    2. **SNAP/WIC Eligibility Status** for every item
    3. **Program Budget Analysis** (within/over budget alerts)
    4. **Coverage Statistics** (% of SNAP/WIC eligible items)
    5. **Program-Specific Substitutions** (maximize benefit value)
    6. **Budget Recommendations** for different family sizes

    **Example Enhanced Response:**
    📊 **NUTRITION & PROGRAM ANALYSIS:**
    • Chicken Breast: Score 89/100, $8.99, SNAP✅ WIC❌ (USDA verified)
    • Whole Wheat Bread: Score 85/100, $2.79, SNAP✅ WIC✅ (Program approved)
    • Spinach: Score 91/100, $2.99, SNAP✅ WIC❌ (High nutrition value)
    
    💰 **BUDGET ANALYSIS:**
    • Total Cost: $14.77
    • SNAP Family Budget: $62.50/week ✅ Under budget
    • WIC Family Budget: $35.00/week ✅ Under budget
    
    🏛️ **PROGRAM COVERAGE:**
    • SNAP Eligible: 3/3 items (100%)
    • WIC Eligible: 1/3 items (33%)
    
    🔄 **PROGRAM RECOMMENDATIONS:**
    • Excellent SNAP coverage - maximizing benefit value
    • Consider adding more WIC-approved items for families with WIC benefits
    
    📈 **DATA SOURCE:** USDA FoodData Central + SNAP/WIC Program Database

    **Try me with:** "Analyze my shopping list for SNAP benefits: Chicken Breast, Whole Wheat Bread, Milk, Eggs" 
    
    I'll provide comprehensive nutrition analysis with SNAP/WIC program optimization! """,
    sub_agents=[nutrition_analyzer_agent, substitution_agent],
)
