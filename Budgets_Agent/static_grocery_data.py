"""Static grocery data for Walmart and Target with SNAP/WIC eligibility."""

from typing import List, Dict, Any
from datetime import datetime

# Static grocery data - 7 items each with wide cost range
WALMART_GROCERY_DATA = [
    {
        "product_id": "walmart_001",
        "name": "Fresh Bananas, per lb",
        "brand": "Fresh",
        "size": "per lb",
        "regular_price": 0.58,
        "promo_price": None,
        "category": "Fresh Produce",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_002",
        "name": "Great Value Canned Black Beans, 15 oz",
        "brand": "Great Value",
        "size": "15 oz",
        "regular_price": 1.08,
        "promo_price": 0.88,
        "category": "Pantry",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_003",
        "name": "Great Value Large White Eggs, 12 Count",
        "brand": "Great Value",
        "size": "12 Count",
        "regular_price": 2.32,
        "promo_price": 1.98,
        "category": "Dairy",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_004",
        "name": "Great Value Whey Protein Powder, Vanilla, 1 lb",
        "brand": "Great Value",
        "size": "1 lb",
        "regular_price": 3.00,
        "promo_price": None,
        "category": "Health & Wellness",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_005",
        "name": "Great Value Peanut Butter, Creamy, 40 oz",
        "brand": "Great Value",
        "size": "40 oz",
        "regular_price": 3.98,
        "promo_price": 3.48,
        "category": "Pantry",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_006",
        "name": "Fresh Ground Beef, 93% Lean, per lb",
        "brand": "Fresh",
        "size": "per lb",
        "regular_price": 5.98,
        "promo_price": None,
        "category": "Meat",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Walmart"
    },
    {
        "product_id": "walmart_007",
        "name": "Great Value Boneless Skinless Chicken Breasts, 3 lb",
        "brand": "Great Value",
        "size": "3 lb",
        "regular_price": 8.97,
        "promo_price": 7.48,
        "category": "Meat",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Walmart"
    }
]

TARGET_GROCERY_DATA = [
    {
        "product_id": "target_001",
        "name": "Fresh Organic Bananas, per lb",
        "brand": "Fresh",
        "size": "per lb",
        "regular_price": 0.79,
        "promo_price": 0.69,
        "category": "Fresh Produce",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Target"
    },
    {
        "product_id": "target_002",
        "name": "Good & Gather Organic Black Beans, 15 oz",
        "brand": "Good & Gather",
        "size": "15 oz",
        "regular_price": 1.29,
        "promo_price": None,
        "category": "Pantry",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Target"
    },
    {
        "product_id": "target_003",
        "name": "Good & Gather Cage Free Large Eggs, 12 Count",
        "brand": "Good & Gather",
        "size": "12 Count",
        "regular_price": 2.79,
        "promo_price": None,
        "category": "Dairy",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Target"
    },
    {
        "product_id": "target_004",
        "name": "Good & Gather Whey Protein Powder, Chocolate, 1 lb",
        "brand": "Good & Gather",
        "size": "1 lb",
        "regular_price": 3.49,
        "promo_price": 2.99,
        "category": "Health & Wellness",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Target"
    },
    {
        "product_id": "target_005",
        "name": "Good & Gather Natural Peanut Butter, 36 oz",
        "brand": "Good & Gather",
        "size": "36 oz",
        "regular_price": 4.49,
        "promo_price": None,
        "category": "Pantry",
        "snap_eligible": True,
        "wic_eligible": True,
        "store": "Target"
    },
    {
        "product_id": "target_006",
        "name": "Good & Gather Ground Turkey, 93% Lean, per lb",
        "brand": "Good & Gather",
        "size": "per lb",
        "regular_price": 6.49,
        "promo_price": 5.99,
        "category": "Meat",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Target"
    },
    {
        "product_id": "target_007",
        "name": "Good & Gather Boneless Skinless Chicken Breast, 2.5 lb",
        "brand": "Good & Gather",
        "size": "2.5 lb",
        "regular_price": 9.99,
        "promo_price": 8.49,
        "category": "Meat",
        "snap_eligible": True,
        "wic_eligible": False,
        "store": "Target"
    }
]

def get_walmart_groceries(snap_eligible_only: bool = False, wic_eligible_only: bool = False) -> List[Dict[str, Any]]:
    """Get Walmart grocery data with optional SNAP/WIC filtering."""
    data = WALMART_GROCERY_DATA.copy()
    
    if snap_eligible_only:
        data = [item for item in data if item["snap_eligible"]]
    
    if wic_eligible_only:
        data = [item for item in data if item["wic_eligible"]]
    
    return data

def get_target_groceries(snap_eligible_only: bool = False, wic_eligible_only: bool = False) -> List[Dict[str, Any]]:
    """Get Target grocery data with optional SNAP/WIC filtering."""
    data = TARGET_GROCERY_DATA.copy()
    
    if snap_eligible_only:
        data = [item for item in data if item["snap_eligible"]]
    
    if wic_eligible_only:
        data = [item for item in data if item["wic_eligible"]]
    
    return data

def get_all_static_groceries(snap_eligible_only: bool = False, wic_eligible_only: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """Get all static grocery data from Walmart and Target."""
    return {
        "walmart": get_walmart_groceries(snap_eligible_only, wic_eligible_only),
        "target": get_target_groceries(snap_eligible_only, wic_eligible_only)
    }

if __name__ == "__main__":
    all_data = get_all_static_groceries()
    snap_data = get_all_static_groceries(snap_eligible_only=True)
    wic_data = get_all_static_groceries(wic_eligible_only=True)
    
    print(f"Walmart: {len(all_data['walmart'])} total, {len(snap_data['walmart'])} SNAP, {len(wic_data['walmart'])} WIC")
    print(f"Target: {len(all_data['target'])} total, {len(snap_data['target'])} SNAP, {len(wic_data['target'])} WIC")