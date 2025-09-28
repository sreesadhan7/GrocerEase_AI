"""
Comprehensive nutritional data for grocery items
Contains detailed nutrient information per serving for Agent 2 analysis
"""

from typing import Dict, Any

# Detailed nutritional data per serving for common grocery items
NUTRITION_DATA = {
    "bananas": {
        "name": "Fresh Bananas",
        "serving_size": "1 medium (118g)",
        "calories": 105,
        "macronutrients": {
            "protein": 1.3,  # grams
            "carbohydrates": 27.0,
            "fiber": 3.1,
            "sugars": 14.4,
            "fat": 0.4
        },
        "vitamins": {
            "vitamin_c": 10.3,  # mg (11% DV)
            "vitamin_b6": 0.4,  # mg (22% DV)
            "folate": 24.0,     # mcg (6% DV)
            "vitamin_a": 76.0   # IU (2% DV)
        },
        "minerals": {
            "potassium": 422,   # mg (9% DV)
            "magnesium": 32,    # mg (8% DV)
            "manganese": 0.3,   # mg (13% DV)
            "copper": 0.1       # mg (4% DV)
        },
        "health_benefits": [
            "Heart health (potassium)",
            "Digestive health (fiber)",
            "Energy metabolism (vitamin B6)",
            "Muscle function (potassium, magnesium)"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "low_sodium": True,
            "cholesterol_free": True
        }
    },
    
    "oats": {
        "name": "Rolled Oats",
        "serving_size": "1/2 cup dry (40g)",
        "calories": 150,
        "macronutrients": {
            "protein": 5.0,
            "carbohydrates": 27.0,
            "fiber": 4.0,
            "sugars": 1.0,
            "fat": 3.0
        },
        "vitamins": {
            "thiamine": 0.2,  # mg
            "folate": 14,  # mcg
            "vitamin_e": 0.4,  # mg
            "niacin": 1.0  # mg
        },
        "minerals": {
            "manganese": 1.9,  # mg
            "phosphorus": 180,  # mg
            "magnesium": 63,  # mg
            "iron": 2.1  # mg
        },
        "health_benefits": [
            "High soluble fiber",
            "Cholesterol lowering",
            "Blood sugar control",
            "Heart healthy whole grain"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "high_fiber": True,
            "low_carb": False,
            "keto_friendly": False
        }
    },
    
    "eggs": {
        "name": "Large Eggs",
        "serving_size": "1 large egg (50g)",
        "calories": 70,
        "macronutrients": {
            "protein": 6.3,
            "carbohydrates": 0.4,
            "fiber": 0,
            "sugars": 0.2,
            "fat": 4.8
        },
        "vitamins": {
            "vitamin_d": 44.0,    # IU (11% DV)
            "vitamin_b12": 0.6,   # mcg (25% DV)
            "riboflavin": 0.3,    # mg (15% DV)
            "folate": 22.0,       # mcg (6% DV)
            "vitamin_a": 270      # IU (5% DV)
        },
        "minerals": {
            "selenium": 15.4,     # mcg (22% DV)
            "phosphorus": 86,     # mg (9% DV)
            "choline": 147,       # mg
            "iron": 0.9           # mg (5% DV)
        },
        "health_benefits": [
            "Complete protein source",
            "Brain development (choline)",
            "Eye health (lutein, zeaxanthin)",
            "Bone health (vitamin D)"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "high_protein": True,
            "low_carb": True
        }
    },
    
    "chicken": {
        "name": "Chicken Breast",
        "serving_size": "3 oz (85g) cooked",
        "calories": 140,
        "macronutrients": {
            "protein": 26.0,
            "carbohydrates": 0,
            "fiber": 0,
            "sugars": 0,
            "fat": 3.0
        },
        "vitamins": {
            "niacin": 8.9,        # mg (44% DV)
            "vitamin_b6": 0.5,    # mg (29% DV)
            "vitamin_b12": 0.3,   # mcg (13% DV)
            "pantothenic_acid": 0.8  # mg (8% DV)
        },
        "minerals": {
            "phosphorus": 196,    # mg (20% DV)
            "selenium": 20.6,     # mcg (29% DV)
            "potassium": 220,     # mg (5% DV)
            "zinc": 0.9           # mg (6% DV)
        },
        "health_benefits": [
            "Lean protein source",
            "Muscle building and repair",
            "Weight management",
            "Immune system support"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "high_protein": True,
            "low_carb": True,
            "keto_friendly": True
        }
    },
    
    "black_beans": {
        "name": "Black Beans",
        "serving_size": "1/2 cup (86g) cooked",
        "calories": 114,
        "macronutrients": {
            "protein": 7.6,
            "carbohydrates": 20.4,
            "fiber": 7.5,
            "sugars": 0.3,
            "fat": 0.5
        },
        "vitamins": {
            "folate": 128,        # mcg (32% DV)
            "thiamine": 0.2,      # mg (17% DV)
            "vitamin_k": 2.8,     # mcg (4% DV)
            "vitamin_b6": 0.1     # mg (4% DV)
        },
        "minerals": {
            "iron": 1.8,          # mg (10% DV)
            "magnesium": 60,      # mg (15% DV)
            "potassium": 305,     # mg (7% DV)
            "zinc": 0.9,          # mg (6% DV)
            "manganese": 0.4      # mg (19% DV)
        },
        "health_benefits": [
            "Heart health (fiber, potassium)",
            "Blood sugar control (fiber, protein)",
            "Digestive health (fiber)",
            "Anemia prevention (iron, folate)"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "high_fiber": True,
            "plant_protein": True,
            "cholesterol_free": True
        }
    },
    
    "ground_beef": {
        "name": "Ground Beef (93% lean)",
        "serving_size": "3 oz (85g) cooked",
        "calories": 164,
        "macronutrients": {
            "protein": 22.0,
            "carbohydrates": 0,
            "fiber": 0,
            "sugars": 0,
            "fat": 7.5
        },
        "vitamins": {
            "vitamin_b12": 2.4,   # mcg (100% DV)
            "niacin": 4.9,        # mg (25% DV)
            "vitamin_b6": 0.3,    # mg (18% DV)
            "riboflavin": 0.2     # mg (12% DV)
        },
        "minerals": {
            "zinc": 4.5,          # mg (30% DV)
            "iron": 2.2,          # mg (12% DV)
            "phosphorus": 177,    # mg (18% DV)
            "selenium": 16.2      # mcg (23% DV)
        },
        "health_benefits": [
            "Complete protein source",
            "Iron absorption (heme iron)",
            "Immune system support (zinc)",
            "Energy metabolism (B vitamins)"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "high_protein": True,
            "low_carb": True,
            "keto_friendly": True,
            "iron_rich": True
        }
    },
    
    "peanut_butter": {
        "name": "Natural Peanut Butter",
        "serving_size": "2 tbsp (32g)",
        "calories": 190,
        "macronutrients": {
            "protein": 8.0,
            "carbohydrates": 6.0,
            "fiber": 3.0,
            "sugars": 2.0,
            "fat": 16.0
        },
        "vitamins": {
            "niacin": 4.2,        # mg (21% DV)
            "vitamin_e": 2.9,     # mg (15% DV)
            "folate": 18.0,       # mcg (4% DV)
            "vitamin_b6": 0.2     # mg (9% DV)
        },
        "minerals": {
            "magnesium": 54,      # mg (14% DV)
            "phosphorus": 107,    # mg (11% DV)
            "potassium": 208,     # mg (4% DV)
            "zinc": 0.9           # mg (6% DV)
        },
        "health_benefits": [
            "Heart health (monounsaturated fats)",
            "Satiety (protein, fat, fiber)",
            "Energy sustained release",
            "Antioxidant protection (vitamin E)"
        ],
        "dietary_considerations": {
            "diabetes_friendly": True,
            "heart_healthy": True,
            "high_protein": True,
            "high_calorie": True
        }
    }
}

def get_nutrition_info(food_name: str) -> Dict[str, Any]:
    """Get detailed nutrition information for a food item"""
    food_key = food_name.lower().replace(" ", "_")
    
    # Try to match common food items
    for key, data in NUTRITION_DATA.items():
        if key in food_key or food_key in key:
            return data
    
    return None

def calculate_nutrient_density(nutrition_data: Dict, price: float) -> Dict[str, float]:
    """Calculate nutrient density per dollar"""
    if not nutrition_data or price <= 0:
        return {}
    
    density = {}
    
    # Protein per dollar
    protein = nutrition_data.get('macronutrients', {}).get('protein', 0)
    density['protein_per_dollar'] = protein / price
    
    # Fiber per dollar
    fiber = nutrition_data.get('macronutrients', {}).get('fiber', 0)
    density['fiber_per_dollar'] = fiber / price
    
    # Iron per dollar
    iron = nutrition_data.get('minerals', {}).get('iron', 0)
    density['iron_per_dollar'] = iron / price
    
    # Vitamin C per dollar
    vitamin_c = nutrition_data.get('vitamins', {}).get('vitamin_c', 0)
    density['vitamin_c_per_dollar'] = vitamin_c / price
    
    # Potassium per dollar
    potassium = nutrition_data.get('minerals', {}).get('potassium', 0)
    density['potassium_per_dollar'] = potassium / price
    
    return density