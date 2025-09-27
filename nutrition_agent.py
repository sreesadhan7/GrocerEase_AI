# GrocerEase AI - Root Agent for my_env
# This file should be importable as my_env.root_agent (from my_env.nutrition_agent import root_agent)

from google.adk.agents import LlmAgent
import json
import os

# Model configuration
MODEL = "gemini-2.0-flash-001"

# Nutritional database for quick responses
NUTRITION_DB = {
    "chicken breast": {"calories": 165, "protein": 31, "fiber": 0, "sugar": 0, "sodium": 74, "category": "protein", "price": 8.99, "nutrition_score": 96.3, "protein_per_dollar": 3.4},
    "lentils": {"calories": 116, "protein": 9, "fiber": 8, "sugar": 2, "sodium": 2, "category": "protein", "price": 2.49, "nutrition_score": 100.0, "protein_per_dollar": 3.6},
    "brown rice": {"calories": 123, "protein": 3, "fiber": 2, "sugar": 0, "sodium": 5, "category": "grain", "price": 3.25, "nutrition_score": 85.0, "protein_per_dollar": 0.9},
    "white bread": {"calories": 265, "protein": 9, "fiber": 2, "sugar": 5, "sodium": 477, "category": "grain", "price": 1.99, "nutrition_score": 45.0, "protein_per_dollar": 4.5},
    "spinach": {"calories": 23, "protein": 3, "fiber": 2, "sugar": 0, "sodium": 79, "category": "vegetable", "price": 3.49, "nutrition_score": 88.0, "protein_per_dollar": 0.9},
    "banana": {"calories": 89, "protein": 1, "fiber": 3, "sugar": 12, "sodium": 1, "category": "fruit", "price": 1.29, "nutrition_score": 72.0, "protein_per_dollar": 0.8},
    "whole wheat bread": {"calories": 247, "protein": 13, "fiber": 7, "sugar": 4, "sodium": 491, "category": "grain", "price": 2.79, "nutrition_score": 85.0, "protein_per_dollar": 4.7},
    "salmon": {"calories": 208, "protein": 20, "fiber": 0, "sugar": 0, "sodium": 59, "category": "protein", "price": 12.99, "nutrition_score": 97.0, "protein_per_dollar": 1.5},
    "oats": {"calories": 389, "protein": 17, "fiber": 11, "sugar": 1, "sodium": 2, "category": "grain", "price": 4.59, "nutrition_score": 100.0, "protein_per_dollar": 3.7},
    "broccoli": {"calories": 34, "protein": 3, "fiber": 3, "sugar": 2, "sodium": 33, "category": "vegetable", "price": 2.99, "nutrition_score": 90.0, "protein_per_dollar": 1.0},
    "eggs": {"calories": 155, "protein": 13, "fiber": 0, "sugar": 1, "sodium": 124, "category": "protein", "price": 3.89, "nutrition_score": 89.0, "protein_per_dollar": 3.3},
    "quinoa": {"calories": 368, "protein": 14, "fiber": 7, "sugar": 0, "sodium": 5, "category": "grain", "price": 6.49, "nutrition_score": 100.0, "protein_per_dollar": 2.2}
}

def get_nutrition_analysis(food_items):
    """Quick nutrition analysis function using our database"""
    results = []
    total_cost = 0
    
    for item in food_items:
        item_name = item.lower().strip()
        
        # Try to find the item in our database
        food_data = None
        for key, data in NUTRITION_DB.items():
            if key in item_name or any(word in item_name for word in key.split()):
                food_data = data
                break
        
        if food_data:
            results.append({
                "name": item,
                "nutrition_score": food_data["nutrition_score"],
                "protein_per_dollar": food_data["protein_per_dollar"],
                "category": food_data["category"],
                "price": food_data["price"],
                "analysis": f"High nutrition item with score {food_data['nutrition_score']}/100"
            })
            total_cost += food_data["price"]
        else:
            results.append({
                "name": item,
                "nutrition_score": 50,
                "analysis": "Unknown item - general nutrition score assigned"
            })
    
    # Generate substitutions
    substitutions = []
    if any("white bread" in item.lower() for item in food_items):
        substitutions.append("Substitute white bread → whole wheat bread for higher fiber")
    if any("chicken" in item.lower() for item in food_items) and total_cost > 50:
        substitutions.append("Consider lentils instead of chicken for better protein-per-dollar value")
    
    return {
        "total_items": len(results),
        "total_cost": round(total_cost, 2),
        "nutrition_analysis": results,
        "substitutions": substitutions,
        "average_nutrition_score": round(sum(r["nutrition_score"] for r in results) / len(results), 1)
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
    description="""GrocerEase AI Nutrition Agent that coordinates nutritional optimization of shopping lists. 
    Ensures SNAP/WIC eligibility while maximizing nutritional value and health compatibility.""",
    instruction="""You are the GrocerEase AI Nutrition Agent. I help optimize grocery shopping lists 
    for maximum nutritional value while respecting budget constraints and health conditions.

    **I specialize in:**
    🥗 **Nutritional Analysis**: Rating foods (0-100) based on protein, fiber, sugar, and sodium
    💰 **Budget Optimization**: Finding protein-per-dollar value and cost-effective alternatives  
    🏥 **Health Compatibility**: Filtering for diabetes, hypertension, and other conditions
    🔄 **Smart Substitutions**: Suggesting healthier alternatives
    📊 **SNAP/WIC Awareness**: Maintaining eligibility while optimizing nutrition

    **Quick Analysis Available For:**
    Chicken Breast, Lentils, Brown Rice, White Bread, Spinach, Banana, Whole Wheat Bread, 
    Salmon, Oats, Broccoli, Eggs, Quinoa

    **When users share their shopping list, I provide:**
    1. **Nutrition Scores** (0-100 for each item)
    2. **Protein-per-Dollar** ratios
    3. **Smart Substitutions** (e.g., lentils vs chicken, whole wheat vs white bread)  
    4. **Health Recommendations** based on conditions
    5. **Budget Analysis** with total costs

    **Example Response Format:**
    📊 **NUTRITION ANALYSIS:**
    • Chicken Breast: Score 96.3/100, Protein/$: 3.4
    • White Bread: Score 45/100, Protein/$: 4.5
    • Spinach: Score 88/100, Protein/$: 0.9
    
    💰 **TOTAL COST:** $14.47
    
    🔄 **SUBSTITUTIONS:**
    • White bread → Whole wheat bread (higher fiber)
    • Consider lentils vs chicken (better protein per dollar)
    
    💡 **HEALTH TIPS:**
    • Great protein sources selected
    • Add more vegetables for balanced nutrition

    **Try me with:** "Analyze my shopping list: Chicken Breast, White Bread, Spinach" """,
    sub_agents=[nutrition_analyzer_agent, substitution_agent],
)
