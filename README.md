# GrocerEase AI - Nutrition Agent

A sophisticated AI nutrition agent built with Google's Agent Development Kit (ADK) that optimizes grocery shopping lists for maximum nutritional value, budget efficiency, and health compatibility.

## 🎯 Overview

The GrocerEase AI Nutrition Agent helps users make smarter grocery shopping decisions by:
- **Analyzing nutritional density** of food items (0-100 scoring system)
- **Optimizing budget efficiency** with protein-per-dollar calculations
- **Providing health-compatible recommendations** for conditions like diabetes and hypertension
- **Suggesting smart substitutions** for better nutrition and value
- **Maintaining SNAP/WIC eligibility** while maximizing nutrition

## 🏗️ Architecture

### Multi-Agent System
```
GrocerEase_NutritionAgent (Root Agent)
├── NutritionAnalyzer (Sub-agent)
│   └── Analyzes nutritional density and health compatibility
└── SubstitutionAgent (Sub-agent)
    └── Recommends healthier and cost-effective alternatives
```

### Agent Chain Ready
- **Standalone Mode**: Direct user interaction
- **Chain Mode**: Processes output from first agent (shopping list generator)
- **JSON Schema Support**: Structured inter-agent communication

## 📁 Project Structure

```
D:\GrocerEase AI\
├── my_env/                          # Virtual environment & main agent
│   ├── nutrition_agent.py          # Main agent file (root_agent)
│   ├── __init__.py                  # Package initialization
│   ├── Scripts/                     # Python executables
│   └── Lib/site-packages/          # Dependencies (ADK, etc.)
├── schemas/                         # Inter-agent communication (future)
│   └── first_agent_output.py       # Schema definitions
├── .env                            # Environment variables (API keys)
├── .vscode/                        # VS Code configuration
│   └── settings.json               # Python interpreter settings
├── requirements.txt                # Dependencies
├── nutrition_agent.py              # Original file (reference)
└── README.md                       # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google AI Studio API Key
- Google Agent Development Kit (ADK)

### Installation

1. **Clone or download the project**
```bash
cd "D:\GrocerEase AI"
```

2. **Set up environment variables**
Create `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Verify the virtual environment**
```bash
# Check Python interpreter
my_env\Scripts\python.exe --version

# Test imports
my_env\Scripts\python.exe -c "import google.adk.agents; print('ADK installed successfully')"
```

### Running the Agent

1. **Start the ADK Web Server**
```bash
# From the project root directory
adk web --app my_env
```

2. **Access the Web Interface**
Open your browser to: `http://127.0.0.1:8000`

3. **Test the Agent**
Try these example prompts:
```
"Analyze my shopping list: chicken breast, white bread, spinach"
"I have diabetes, help optimize: banana, white rice, salmon"  
"Budget $30: eggs, quinoa, broccoli, oats"
```

## 🥗 Nutrition Database

The agent includes a comprehensive nutrition database with 12+ food items:

| Food Item | Nutrition Score | Protein/$ | Category | Key Benefits |
|-----------|----------------|-----------|----------|--------------|
| Oats | 100.0 | 3.7 | Grain | High fiber, complete nutrition |
| Lentils | 100.0 | 3.6 | Protein | Plant protein, fiber rich |
| Salmon | 97.0 | 1.5 | Protein | Omega-3, premium protein |
| Chicken Breast | 96.3 | 3.4 | Protein | Lean protein, versatile |
| Broccoli | 90.0 | 1.0 | Vegetable | Vitamins, minerals, fiber |

## 🎯 Agent Capabilities

### Nutritional Analysis
- **Nutrition Score**: 0-100 rating system
- **Macronutrient Breakdown**: Protein, fiber, sugar, sodium
- **Health Compatibility**: Diabetes, hypertension considerations
- **Category Classification**: Protein, grain, vegetable, fruit

### Budget Optimization  
- **Protein-per-Dollar**: Value calculations
- **Cost Analysis**: Total shopping list costs
- **Smart Substitutions**: Better value alternatives
- **SNAP/WIC Awareness**: Eligible food recommendations

### Health Recommendations
- **Diabetic-Friendly**: Low sugar alternatives
- **Hypertension**: Low sodium options
- **High Fiber**: Digestive health focus
- **Balanced Nutrition**: Complete meal planning

## 🔗 Agent Chaining

### Integration with First Agent
The nutrition agent can seamlessly process output from a shopping list generator:

```json
{
  "shopping_list": [
    {"item": "chicken breast", "quantity": "2 lbs", "estimated_price": 8.99},
    {"item": "white bread", "quantity": "1 loaf", "estimated_price": 1.99}
  ],
  "user_profile": {
    "budget": 50,
    "health_conditions": ["diabetes"],
    "household_size": 2
  }
}
```

### Response Format
```
📊 NUTRITION ANALYSIS:
• Chicken Breast: Score 96.3/100, Protein/$: 3.4
• White Bread: Score 45/100, Protein/$: 4.5

💰 TOTAL COST: $10.98 (within $50 budget)

🔄 SUBSTITUTIONS:
• White bread → Whole wheat bread (higher fiber, better for health)

🏥 HEALTH COMPATIBILITY:
• Diabetes: Consider reducing white bread (high sugar content)
```

## 🧪 Testing

### Manual Testing
```bash
# Test import functionality
python -c "from my_env.nutrition_agent import root_agent; print('Agent loaded successfully')"

# Test nutrition analysis
python -c "from my_env.nutrition_agent import get_nutrition_analysis; print(get_nutrition_analysis(['chicken breast', 'spinach']))"
```

### Web Interface Testing
1. Start the ADK server
2. Use the chat interface
3. Try various food combinations
4. Test health condition scenarios

## 🛠️ Development

### Adding New Foods
Extend the `NUTRITION_DB` in `nutrition_agent.py`:

```python
"new_food": {
    "calories": 100,
    "protein": 10,
    "fiber": 5,
    "sugar": 2,
    "sodium": 50,
    "category": "protein",
    "price": 4.99,
    "nutrition_score": 85.0,
    "protein_per_dollar": 2.0
}
```

### Customizing Health Conditions
Modify the health compatibility logic in the agent instructions or create specialized sub-agents.

### Extending Agent Chain
Add new agents to the `sub_agents` list and update the coordination logic.

## 📊 Performance

### Response Time
- **Database Lookup**: < 100ms for known foods
- **LLM Analysis**: 1-3 seconds for complex queries
- **Full Analysis**: 2-5 seconds for complete shopping lists

### Accuracy
- **Nutrition Database**: 12+ foods with verified nutritional data
- **Price Estimates**: Based on average grocery store prices
- **Health Recommendations**: Following standard dietary guidelines

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
```bash
# Fix: Ensure correct Python interpreter
# In VS Code: Ctrl+Shift+P → "Python: Select Interpreter"
# Choose: d:\GrocerEase AI\my_env\Scripts\python.exe
```

2. **ADK Server Won't Start**
```bash
# Check virtual environment
adk web --app my_env --verbose

# Verify agent structure
python -c "from my_env.nutrition_agent import root_agent"
```

3. **API Key Issues**
```bash
# Verify .env file exists and contains:
# GEMINI_API_KEY=your_actual_api_key
```

### Debug Mode
```bash
# Run with verbose logging
adk web --app my_env --verbose --debug
```

## 🤝 Contributing

### Code Structure
- **Follow ADK patterns**: Use LlmAgent class properly
- **Maintain database format**: Keep nutrition data consistent  
- **Update documentation**: Reflect changes in README
- **Test thoroughly**: Verify both standalone and chain modes

### Future Enhancements
- [ ] Expand nutrition database (100+ foods)
- [ ] Add meal planning capabilities
- [ ] Integrate with grocery store APIs for real-time pricing
- [ ] Support for multiple dietary patterns (keto, vegan, etc.)
- [ ] Advanced health condition modeling
- [ ] Recipe suggestions based on shopping lists

## 📝 License

This project is part of the GrocerEase AI system. Please ensure compliance with Google ADK licensing terms.

## 🙋‍♀️ Support

For issues and questions:
1. Check the troubleshooting section
2. Verify your ADK installation
3. Ensure proper virtual environment setup
4. Test with simple food items first

---

**GrocerEase AI Nutrition Agent** - Making healthy eating accessible and affordable! 🥗💚