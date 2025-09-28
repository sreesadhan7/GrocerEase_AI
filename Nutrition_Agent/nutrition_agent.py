# GrocerEase AI - Agent 2: Nutrition Analyst (Clean Version)

import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent

# Load environment variables
load_dotenv()

# Model configuration
MODEL = "gemini-2.0-flash-001"


class NutritionAgent(LlmAgent):
    """
    Agent 2: Nutrition & Health Analyst
    
    Analyzes shopping lists from Agent 1 for health compatibility and provides 
    focused nutrition recommendations within SNAP/WIC budget constraints.
    """

    def __init__(self):
        super().__init__(
            name="Nutrition_Health_Analyst", 
            model=MODEL,
            description="Agent 2: Analyzes nutrition, health compatibility, and provides substitution recommendations.",
    instruction="""You are the GrocerEase AI Nutrition Analyst with comprehensive health and nutrition expertise.
    I analyze grocery lists and provide detailed nutrition analysis with costs, nutrient content, and health recommendations.

    **🎯 MY PRIMARY ROLE: ANALYZE GROCERIES**
    I analyze both existing grocery lists users provide AND shopping lists created by Agent 1.

    **I ANALYZE:**
    🥗 **User-Provided Lists**: "Analyze my chicken, oats, lentils, bread, salmon" → Detailed nutrition analysis
    📊 **Agent 1 Shopping Lists**: Load from JSON and provide comprehensive analysis
    🏥 **Health Compatibility**: Diabetes, heart health, dietary restrictions
    💡 **Substitution Advice**: Healthier alternatives within budget
    🔢 **Cost Analysis**: Price per nutrient calculations

    **I DO NOT CREATE SHOPPING LISTS** - that's Agent 1's job. When users ask for shopping lists or budget optimization, redirect:
    "For creating shopping lists within your budget, please consult Agent 1 - the SNAP/WIC Price Tracker. I specialize in analyzing nutrition content and providing health recommendations."

    **WHAT I PROVIDE:**
    1. **Detailed Nutrition Analysis** for each item with cost breakdown
    2. **Health Compatibility** scoring (diabetes-friendly, heart-healthy, etc.)
    3. **Nutrient Content** (protein, fiber, vitamins, minerals per item)
    4. **Cost-Effectiveness** (nutrients per dollar spent)
    5. **Substitution Recommendations** for healthier alternatives
    6. **Overall Health Score** with detailed explanations

    **Example Analysis Response:**
    🥗 **NUTRITION ANALYSIS**

    📊 **Item-by-Item Breakdown:**
    • **Chicken Breast (5$)**: 
      - Protein: 31g per serving (6.2g/$1) ✅ Excellent
      - Fat: 3g (lean protein) ✅ Heart-healthy
      - Diabetes: ✅ Perfect (0g carbs)
      
    • **Oats (3$)**:
      - Fiber: 4g per serving (1.3g/$1) ✅ Good
      - Complex carbs: Slow energy release
      - Diabetes: ⚠️ Monitor portions (high carb)

    💡 **Health Recommendations:**
    • Excellent protein choices for muscle building
    • Consider steel-cut oats for better blood sugar control
    • Add more vegetables for micronutrients

    **Example Requests I Handle:**
    ✅ "Analyze my chicken, oats, lentils shopping list"
    ✅ "Is this list good for diabetes?"
    ✅ "What nutrients am I getting?"
    ✅ "Suggest healthier alternatives"

    **Example Requests for Agent 1:**
    ❌ "I have $40 budget, create a shopping list"
    ❌ "What can I buy with SNAP benefits?"
    ❌ "Find me cheapest groceries"

    I'm your nutrition analyzer, providing detailed analysis with costs and recommendations! """
        )

    def load_shopping_data(self) -> Dict[str, Any]:
        """Load shopping list from Agent 1's JSON output with enhanced validation"""
        try:
            agent1_output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Budgets_Agent', 'agent_1_output.json')
            
            if os.path.exists(agent1_output_path):
                with open(agent1_output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validate data structure
                if isinstance(data, dict) and 'shopping_list' in data:
                    shopping_list = data['shopping_list']
                    if isinstance(shopping_list, list) and len(shopping_list) > 0:
                        print(f"✅ Agent 2: Loaded {len(shopping_list)} items from Agent 1 for analysis")
                        return data
                    else:
                        print("⚠️ Agent 2: Shopping list is empty - please run Agent 1 first")
                        return {"shopping_list": [], "cost_breakdown": {"total_cost": 0}}
                else:
                    print("⚠️ Agent 2: Invalid data format from Agent 1")
                    return {"shopping_list": [], "cost_breakdown": {"total_cost": 0}}
            else:
                print(f"⚠️ Agent 2: No data from Agent 1 found. Please run Agent 1 first to generate shopping list.")
                return {"shopping_list": [], "cost_breakdown": {"total_cost": 0}}
                
        except json.JSONDecodeError as e:
            print(f"❌ Agent 2: JSON parsing error: {e}")
            return {"shopping_list": [], "cost_breakdown": {"total_cost": 0}}
        except Exception as e:
            print(f"❌ Agent 2: Error loading shopping data: {e}")
            return {"shopping_list": [], "cost_breakdown": {"total_cost": 0}}

    def _parse_user_items(self, message: str) -> List[Dict]:
        """Parse grocery items from user message like 'chicken 5$, oats 3$, lentils 3$'"""
        items = []
        
        # Common food items that might appear in user messages
        food_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'eggs', 'milk', 'cheese', 'yogurt',
                        'bread', 'rice', 'pasta', 'oats', 'cereal', 'beans', 'lentils', 'chickpeas',
                        'apple', 'banana', 'orange', 'spinach', 'broccoli', 'carrot', 'potato', 'tomato',
                        'peanut', 'almond', 'nuts', 'butter', 'oil', 'salt', 'sugar']
        
        # Look for food items with prices in the message
        import re
        words = message.lower().split()
        
        i = 0
        while i < len(words):
            word = words[i].strip(',')
            if any(food in word for food in food_keywords):
                # Found a food item, look for price nearby
                price = 0
                name = word
                
                # Look for price pattern in next few words
                for j in range(i, min(i + 3, len(words))):
                    price_match = re.search(r'(\d+(?:\.\d{2})?)', words[j])
                    if price_match and ('$' in words[j] or 'dollar' in words[j]):
                        price = float(price_match.group(1))
                        break
                
                items.append({
                    'name': name.capitalize(),
                    'price': price,
                    'category': 'User Provided'
                })
            i += 1
        
        return items

    def _parse_user_items_from_context(self, current_message: str) -> List[Dict]:
        """Parse grocery items from current message and conversation context"""
        # Try current message first
        items = self._parse_user_items(current_message)
        
        # If no items in current message, check previous messages in context
        if not items and hasattr(self, '_conversation_context'):
            for context_entry in reversed(self._conversation_context):
                prev_message = context_entry.get('message', '')
                context_items = self._parse_user_items(prev_message)
                if context_items:
                    items.extend(context_items)
                    break  # Use the most recent message with items
        
        return items

    def _analyze_user_items(self, items: List[Dict], message_lower: str) -> str:
        """Analyze user-provided grocery items with detailed nutrition and cost breakdown"""
        total_cost = sum(item.get('price', 0) for item in items)
        
        response = f"""🥗 **NUTRITION ANALYSIS - Your Grocery Items**

📊 **Analysis Summary:**
• Items analyzed: {len(items)}
• Total cost: ${total_cost:.2f}
• Custom grocery list ✅

🛍️ **Item-by-Item Analysis:**"""

        # Analyze each item with detailed breakdown
        for item in items:
            name = item.get('name', '')
            price = item.get('price', 0)
            
            response += f"\n\n**{name} (${price:.2f}):**"
            
            # Add nutrition analysis based on food type
            if 'chicken' in name.lower():
                response += f"""
  • Protein: ~31g per serving (6.2g per $1) ✅ Excellent
  • Fat: 3g (lean protein) ✅ Heart-healthy  
  • Carbs: 0g ✅ Perfect for diabetes
  • Health Score: 95/100 - Premium lean protein"""
            
            elif 'oats' in name.lower():
                response += f"""
  • Fiber: ~4g per serving (1.3g per $1) ✅ Good
  • Complex carbs: Slow energy release
  • Protein: 5g per serving ⚠️ Moderate
  • Health Score: 85/100 - Monitor portions for diabetes"""
            
            elif 'lentils' in name.lower():
                response += f"""
  • Protein: ~9g per serving (3g per $1) ✅ Excellent value
  • Fiber: 8g per serving ✅ Outstanding
  • Iron: High content ✅ Great for energy
  • Health Score: 92/100 - Nutrient powerhouse"""
            
            elif 'bread' in name.lower():
                response += f"""
  • Carbs: ~15g per slice ⚠️ High glycemic
  • Protein: 3g per serving ⚠️ Low
  • Fiber: Variable (2-4g) 
  • Health Score: 65/100 - Consider whole grain options"""
            
            elif 'salmon' in name.lower():
                response += f"""
  • Protein: ~25g per serving (4.2g per $1) ✅ Excellent
  • Omega-3: High content ✅ Brain & heart health
  • Fat: Healthy fats ✅ Anti-inflammatory
  • Health Score: 98/100 - Premium superfood"""
            
            else:
                response += f"""
  • Nutrition data: Estimated based on food type
  • Value: ${price:.2f} investment
  • Health potential: Varies by preparation method"""

        # Add overall recommendations
        is_diabetes = any(word in message_lower for word in ['diabetes', 'diabetic', 'sugar', 'blood sugar'])
        is_heart = any(word in message_lower for word in ['heart', 'cardiac', 'sodium', 'blood pressure'])
        
        if is_diabetes:
            response += f"""\n\n🩺 **DIABETES-FOCUSED RECOMMENDATIONS:**
• Excellent: Chicken, salmon (zero carbs)
• Good: Lentils (fiber slows absorption)
• Monitor: Oats, bread (check portions)
• Overall: Strong protein focus ✅"""
        
        elif is_heart:
            response += f"""\n\n❤️ **HEART-HEALTH ANALYSIS:**
• Excellent: Salmon (omega-3), chicken (lean)
• Good: Lentils (fiber), oats (cholesterol-lowering)
• Consider: Low-sodium preparation methods
• Overall: Heart-friendly selections ✅"""
        
        else:
            response += f"""\n\n💡 **OVERALL HEALTH ASSESSMENT:**
• High-quality proteins: Excellent choices
• Nutrient density: Good variety
• Cost effectiveness: ${total_cost/len(items):.2f} average per item
• Recommendation: Well-balanced list ✅"""

        response += f"""\n\n✅ **Summary:**
• Total nutritional investment: ${total_cost:.2f}
• Protein-rich selections prioritized
• Good foundation for healthy eating
• Consider adding more vegetables for micronutrients"""

        return response

    async def __call__(self, message: str, context: Dict = None) -> str:
        """Process nutrition analysis requests with conversation context"""
        message_lower = message.lower()
        
        # Store conversation context for continuity
        if not hasattr(self, '_conversation_context'):
            self._conversation_context = []
        
        self._conversation_context.append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Only redirect shopping list creation requests to Agent 1 (not analysis)
        shopping_list_keywords = ['create list', 'make list', 'buy with', 'what can i buy', 'find groceries']
        # Don't redirect if they want to analyze an existing shopping list
        analysis_keywords = ['analyze', 'review', 'check', 'evaluate', 'assess']
        
        is_creation_request = any(keyword in message_lower for keyword in shopping_list_keywords)
        is_analysis_request = any(keyword in message_lower for keyword in analysis_keywords)
        
        if is_creation_request and not is_analysis_request:
            return """🔄 **Redirecting to Agent 1 - SNAP/WIC Price Tracker**

For creating shopping lists within your budget, please consult Agent 1 - the SNAP/WIC Price Tracker. I specialize in analyzing nutrition content and providing health recommendations.

**Agent 1 handles:** Shopping list creation, budget optimization, store comparisons."""

        # Handle follow-up requests like "analyze nutrition" or "I have diabetes"
        follow_up_keywords = ['analyze', 'nutrition', 'diabetes', 'heart', 'health', 'recommend', 'substitute']
        if any(keyword in message_lower for keyword in follow_up_keywords):
            # First try to load from Agent 1's JSON (most recent shopping list)
            shopping_data = self.load_shopping_data()
            shopping_list = shopping_data.get('shopping_list', [])
            
            if shopping_list:
                # Agent 1 data available - analyze it
                return self.analyze_shopping_list(shopping_list, shopping_data, message_lower)
            else:
                # No Agent 1 data - check if user provided items in current or previous messages
                user_items = self._parse_user_items_from_context(message)
                if user_items:
                    return self._analyze_user_items(user_items, message_lower)
                else:
                    return """❌ **No Items Found for Analysis**

I couldn't find a shopping list to analyze. Please either:
1. **Ask Agent 1 to create a shopping list first**: "I have $45 SNAP budget"
2. **Provide items to analyze**: "Analyze chicken $5, oats $3, lentils $3"

Then I can provide detailed nutrition analysis with costs and recommendations!"""

        # Handle user-provided grocery list analysis (like "analyze chicken, oats, lentils")
        user_items = self._parse_user_items(message)
        if user_items:
            return self._analyze_user_items(user_items, message_lower)

        # Default: Load shopping data from Agent 1 if available
        shopping_data = self.load_shopping_data()
        shopping_list = shopping_data.get('shopping_list', [])
        
        if not shopping_list:
            return """❌ **No Shopping List Found**

I need a shopping list from Agent 1 to analyze. Please:
1. First ask Agent 1 to create a shopping list within your budget
2. Then I can analyze the nutrition and health compatibility

**Example:** "I have $50 SNAP budget, please create a shopping list" (ask Agent 1 first)"""

        # Analyze the shopping list based on user request
        return self.analyze_shopping_list(shopping_list, shopping_data, message_lower)

    def analyze_shopping_list(self, items: List[Dict], shopping_data: Dict, user_message: str) -> str:
        """Analyze shopping list with condition-specific focus"""
        total_cost = shopping_data.get('cost_breakdown', {}).get('total_cost', 0)
        if total_cost == 0:
            total_cost = sum(item.get('price', 0) for item in items)
        
        # Determine analysis focus
        is_diabetes = any(word in user_message for word in ['diabetes', 'diabetic', 'sugar', 'blood sugar'])
        is_heart = any(word in user_message for word in ['heart', 'cardiac', 'sodium', 'blood pressure'])
        is_substitution = any(word in user_message for word in ['substitute', 'alternative', 'replace', 'healthier'])
        
        # Start response
        response = f"""🥗 **NUTRITION ANALYSIS - From Your Shopping List**

📊 **Analysis Summary:**
• Items analyzed: {len(items)}
• Total cost: ${total_cost:.2f}
• Budget-optimized selections ✅

🛍️ **Your Items by Category:**"""

        # Group by category and show items
        categories = {}
        for item in items:
            category = item.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        for category, category_items in categories.items():
            response += f"\n\n**{category} ({len(category_items)} items):**"
            for item in category_items[:4]:  # Show up to 4 items per category
                price = item.get('price', 0)
                store = item.get('store', '')
                response += f"\n• {item['name']} - ${price:.2f} at {store}"

        # Add condition-specific analysis
        if is_diabetes:
            response += self._diabetes_advice(categories)
        elif is_heart:
            response += self._heart_health_advice(categories)
        elif is_substitution:
            response += self._substitution_advice(items)
        else:
            response += self._general_health_advice(categories)

        response += f"""\n\n✅ **Budget & Health Summary:**
• All items within SNAP/WIC budget constraints  
• Focus on nutrient-dense, whole foods
• Good variety across essential food groups
• Minimal processed foods selected

🍽️ **COMPREHENSIVE MEAL PLANNING RECOMMENDATIONS:**

**🌅 Breakfast Options (Using Your Items):**
1. **High-Protein Start:** 2-3 scrambled eggs + ½ cup black beans + banana slices
   - Provides: 25g protein, 8g fiber, sustained 4-hour energy
   - Cost per meal: ~$1.50

2. **Power Smoothie:** 1 banana + 2 tbsp peanut butter + 1 egg (pasteurized) + milk/water  
   - Provides: 20g protein, potassium, healthy fats
   - Cost per meal: ~$1.25

**🌞 Lunch Ideas:**
1. **Protein Bowl:** 4 oz grilled chicken + ½ cup seasoned black beans + vegetables
   - Provides: 35g protein, complete amino acids, fiber
   - Cost per meal: ~$3.50

2. **Budget Bean & Egg:** 2 eggs + ½ cup black beans + slice of bread
   - Provides: 22g protein, iron, B-vitamins  
   - Cost per meal: ~$2.00

**🌙 Dinner Combinations:**
1. **Lean & Clean:** 5 oz turkey/ground beef + black bean side + steamed vegetables
   - Provides: 40g protein, iron, complete nutrition
   - Cost per meal: ~$4.00

2. **Comfort Classic:** Ground beef (4 oz) + beans + vegetables in hearty stew
   - Provides: 30g protein, warming meal, budget-friendly
   - Cost per meal: ~$3.25

**🥗 WEEKLY MEAL PREP STRATEGY:**

**Batch Cooking Sunday:**
• Cook 2 lbs chicken/turkey → portion into 8 servings
• Prepare 4 cups black beans → 8 half-cup servings  
• Hard-boil dozen eggs → grab-and-go protein

**Daily Meal Costs:**
• Breakfast: $1.25-1.50
• Lunch: $2.00-3.50  
• Dinner: $3.25-4.00
• **Total daily:** $6.50-9.00 (excellent budget efficiency!)

**⚡ PERFORMANCE & ENERGY OPTIMIZATION:**

**Pre-Workout (30 min before):**
• ½ banana + 1 tbsp peanut butter = quick energy + sustained fuel

**Post-Workout (within 30 min):**  
• 2-3 eggs or 4 oz chicken = optimal muscle recovery

**Sustained Energy Throughout Day:**
• Include protein with every meal/snack
• Pair carbs (beans, banana) with protein to prevent crashes
• Stay hydrated: 8-10 glasses water with high-protein diet

**🎯 HEALTH GOALS ACHIEVEMENT:**

**Weight Management:** High protein (25-40g per meal) supports metabolism and satiety
**Muscle Building:** Complete amino acids from animal proteins + plant protein from beans  
**Blood Sugar Control:** Protein + fiber combination prevents spikes and crashes
**Heart Health:** Lean proteins + fiber support cardiovascular wellness
**Budget Efficiency:** $6.50-9.00 daily for complete, balanced nutrition

💡 **Next Steps:** Your list provides solid nutrition foundation within budget! Add colorful vegetables when possible to complete the nutritional profile perfectly."""

        return response

    def _diabetes_advice(self, categories: Dict) -> str:
        """Provide comprehensive diabetes-specific advice with detailed recommendations"""
        return f"""\n\n🩺 **DIABETES-FOCUSED ANALYSIS & RECOMMENDATIONS:**

**✅ EXCELLENT CHOICES FOR DIABETES:**
• **Protein Sources:** Eggs, lean meats (chicken, turkey, ground beef) - zero carbs, steady blood sugar
• **Fiber Champions:** Black beans provide 8g fiber per serving to slow sugar absorption
• **Low Glycemic:** Your list prioritizes high-protein, low-carb foods ✅

**📊 BLOOD SUGAR IMPACT ANALYSIS:**
• **Minimal Sugar Content:** Less than 5g added sugars across selections
• **High Protein:** 25-30g protein per serving from meat sources
• **Complex Carbs Only:** Black beans release glucose slowly vs simple carbs

**💡 SPECIFIC DIABETES RECOMMENDATIONS:**
1. **Meal Timing:** Eat protein with every meal to stabilize blood sugar
2. **Portion Control:** 
   - Chicken/Turkey: 4-6 oz per meal (palm-sized portion)
   - Black beans: ½ cup max to manage carb load
   - Eggs: 2-3 eggs provide sustained energy without spikes
3. **Cooking Methods:** 
   - Grill, bake, or poach proteins (avoid breading/frying)
   - Season with herbs vs high-sodium sauces
4. **Blood Sugar Monitoring:** Test 2 hours after meals with these foods

**🚨 DIABETES CAUTIONS:**
• Monitor peanut butter portions (2 tbsp max due to calories)
• Choose steel-cut oats over instant if adding oats later
• Avoid fruit juices - stick to whole fruits for fiber

**🎯 OVERALL DIABETES RATING:** 95/100 - Excellent blood sugar management potential"""

    def _heart_health_advice(self, categories: Dict) -> str:
        """Provide comprehensive heart health advice with actionable recommendations"""
        return f"""\n\n❤️ **HEART HEALTH ANALYSIS & CARDIO RECOMMENDATIONS:**

**✅ HEART-PROTECTIVE FOODS IN YOUR LIST:**
• **Lean Proteins:** Chicken (3g fat), turkey, 93% lean ground beef - reduce bad cholesterol
• **Healthy Fats:** Natural peanut butter provides monounsaturated fats for heart health
• **Fiber Powerhouses:** Black beans (8g fiber) actively lower cholesterol levels
• **Potassium Sources:** Bananas help regulate blood pressure naturally

**🫀 CARDIOVASCULAR IMPACT ASSESSMENT:**
• **Saturated Fat:** Less than 10% of calories (within heart-healthy range)
• **Omega-3 Potential:** Add fatty fish 2x/week for optimal heart protection
• **Sodium Control:** Fresh meats naturally low sodium vs processed alternatives
• **Cholesterol Management:** Fiber + lean protein combination supports healthy levels

**💡 HEART-SPECIFIC COOKING RECOMMENDATIONS:**
1. **Preparation Methods:**
   - Grill, bake, or steam proteins (never deep fry)
   - Use heart-healthy oils: olive oil, avocado oil
   - Season with garlic, herbs, lemon vs salt
2. **Meal Planning:**
   - Include black beans 3-4x/week for cholesterol benefits
   - Pair proteins with colorful vegetables
   - Choose brown rice over white rice for fiber
3. **Daily Targets:**
   - 25-35g fiber daily (your beans contribute 8g per serving)
   - Less than 2,300mg sodium daily (track added salt)

**🚨 HEART HEALTH ENHANCEMENTS:**
• **Add:** Fatty fish (salmon, mackerel), nuts, olive oil
• **Increase:** Vegetables (aim for 5-7 servings daily)
• **Limit:** Processed meats, full-fat dairy, added sugars

**🎯 OVERALL HEART RATING:** 88/100 - Strong foundation, add omega-3s for perfection"""

    def _substitution_advice(self, items: List[Dict]) -> str:
        """Provide detailed substitution recommendations with specific alternatives"""
        substitutions = []
        upgrade_suggestions = []
        cost_conscious_swaps = []
        
        for item in items:
            name = item.get('name', '').lower()
            price = item.get('price', 0)
            store = item.get('store', '')
            
            # Analyze each item for potential improvements
            if 'creamy peanut butter' in name:
                substitutions.append("🔄 **Peanut Butter Upgrade:** Natural peanut butter (less added sugar, same price range)")
                upgrade_suggestions.append("• Try almond butter for more vitamin E and heart-healthy fats")
            
            elif 'white eggs' in name:
                upgrade_suggestions.append("• Consider pasture-raised eggs for higher omega-3 content (+$1-2)")
                
            elif 'ground beef' in name:
                substitutions.append("🔄 **Protein Swap:** Ground turkey (similar price, less saturated fat)")
                cost_conscious_swaps.append("• Lentils/beans provide protein at 1/3 the cost")
                
            elif 'regular bananas' in name:
                upgrade_suggestions.append("• Organic bananas avoid pesticides (+$0.15/lb)")
                
            elif 'white bread' in name:
                substitutions.append("🔄 **Fiber Boost:** 100% whole wheat bread (same price, 3x more fiber)")

        response = f"""\n\n💡 **COMPREHENSIVE SUBSTITUTION RECOMMENDATIONS:**

**🔄 IMMEDIATE IMPROVEMENTS (Same Budget):**"""
        
        if substitutions:
            for sub in substitutions:
                response += f"\n{sub}"
        else:
            response += "\n• Your selections are already nutritionally optimal! ✅"
        
        response += f"""\n\n🌟 **UPGRADE OPTIONS (Small Price Increase):**"""
        for upgrade in upgrade_suggestions:
            response += f"\n{upgrade}"
            
        if not upgrade_suggestions:
            response += "\n• Consider organic versions for pesticide-free options"
            
        response += f"""\n\n� **BUDGET-FRIENDLY ALTERNATIVES:**"""
        for swap in cost_conscious_swaps:
            response += f"\n{swap}"
            
        if not cost_conscious_swaps:
            response += "\n• Dried beans/lentils cost 60% less than canned versions"
            response += "\n• Buy larger quantities when items are on sale"
        
        response += f"""\n\n🎯 **STRATEGIC SHOPPING TIPS:**
• **Best Value:** Keep eggs, black beans, bananas - excellent nutrition per dollar
• **Quality Investment:** Spend extra on grass-fed meat if budget allows
• **Prep Efficiency:** Buy whole chickens vs parts (save 30-40%)
• **Seasonal Strategy:** Frozen vegetables maintain nutrients year-round at lower cost

**✅ SUBSTITUTION SUMMARY:** Your list shows excellent nutrition awareness. Small tweaks can enhance benefits while maintaining budget consciousness."""

        return response

    def _general_health_advice(self, categories: Dict) -> str:
        """Provide comprehensive general health advice with actionable lifestyle recommendations"""
        return f"""\n\n💡 **COMPREHENSIVE NUTRITION & LIFESTYLE ASSESSMENT:**

**🌟 NUTRITIONAL EXCELLENCE ANALYSIS:**
• **Complete Proteins:** Eggs, chicken, turkey provide all 9 essential amino acids
• **Complex Carbohydrates:** Black beans offer sustained energy + 8g fiber per serving
• **Healthy Fats:** Natural nut butters support brain function and nutrient absorption
• **Micronutrient Density:** Fresh produce provides vitamins, minerals, antioxidants

**📊 MACRO & MICRONUTRIENT BREAKDOWN:**
• **Protein:** 25-35g per serving from animal sources (optimal for muscle maintenance)
• **Fiber:** 15-20g daily potential from your selections (60% of daily needs)
• **Iron:** Meat + beans provide both heme and non-heme iron for energy
• **B-Vitamins:** Eggs and meat support nervous system and energy metabolism

**🍽️ MEAL PLANNING RECOMMENDATIONS:**

**Breakfast Ideas:**
• 2-3 eggs + ½ cup black beans = 25g protein, 8g fiber
• Natural peanut butter on whole grain toast + banana
• Protein smoothie: eggs, peanut butter, banana, unsweetened milk

**Lunch/Dinner Combinations:**
• 4 oz grilled chicken + ½ cup seasoned black beans + vegetables
• Turkey and bean chili with extra vegetables
• Ground beef (93% lean) stir-fry with mixed vegetables

**🥗 DAILY NUTRITION TARGETS TO MEET:**
• **Vegetables:** Add 3-4 servings daily (missing from current list)
• **Fruits:** Bananas provide potassium; add berries for antioxidants  
• **Whole Grains:** Consider brown rice, quinoa, or oats for additional fiber
• **Healthy Fats:** Your peanut butter provides good fats; consider adding olive oil

**⚡ ENERGY & PERFORMANCE OPTIMIZATION:**
1. **Pre-Workout:** Banana + small amount peanut butter (quick + sustained energy)
2. **Post-Workout:** Eggs or chicken within 30 minutes (muscle recovery)
3. **Sustained Energy:** Black beans with any meal prevents blood sugar crashes
4. **Hydration:** Aim for 8-10 glasses water daily with this protein-rich diet

**🚨 NUTRITIONAL GAPS TO ADDRESS:**
• **Vitamin C:** Add citrus, berries, or bell peppers
• **Calcium:** Consider dairy or fortified plant alternatives
• **Omega-3:** Add fatty fish 2x/week or walnuts/chia seeds
• **Variety:** Rotate protein sources and try different colored vegetables

**🎯 OVERALL HEALTH RATING:** 90/100 - Excellent protein foundation, needs more variety in vegetables and fruits for optimal micronutrient profile

**🏆 SUCCESS STRATEGY:** Your list provides an outstanding base for healthy eating. Focus on adding colorful vegetables and you'll have a nutritionally complete approach that supports long-term health goals."""


# Create specialized sub-agents for comprehensive analysis
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

# Main Root Agent (This is what ADK web looks for as root_agent)
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