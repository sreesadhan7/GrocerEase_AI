# GrocerEase AI

A simple AI system that helps you shop for groceries with SNAP/WIC benefits.

## What it does

- Creates shopping lists within your budget
- Analyzes nutrition and health benefits
- Compares Walmart vs Target prices
- Works with SNAP, WIC, or both benefits

## How to use

1. **Install dependencies:**
   ```bash
   pip install -r Budgets_Agent/requirements.txt
   ```

2. **Set up your API key:**
   Create a `.env` file with:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **Run the system:**
   ```bash
   python grocerease_adk_demo.py
   ```

4. **Enter your grocery request:**
   ```
   I have $25 SNAP budget, I need protein-rich food
   ```

## Example requests

- "I have $20 SNAP credit"
- "WIC $15, I'm diabetic" 
- "SNAP $30 and WIC $10, need heart-healthy options"

## What you get

- **Shopping list** with prices
- **Store recommendations** (Walmart vs Target)
- **Nutrition analysis** for your health needs
- **Actionable advice** for better shopping

That's it! Simple grocery shopping with AI help.