"""
Test AI categorization
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_categorizer import AICategorizer

def test_ai_categorization():
    """Test AI categorization with sample transactions"""
    categorizer = AICategorizer()

    if not categorizer.enabled:
        print("⚠️  AI Categorization is disabled (no OpenAI API key)")
        print("   Set OPENAI_API_KEY in backend/.env to test")
        return

    # Test transactions
    test_transactions = [
        {"merchant": "STARBUCKS", "description": "Coffee", "amount": 5.67},
        {"merchant": "SHELL OIL", "description": "Gas", "amount": 45.00},
        {"merchant": "NETFLIX.COM", "description": "Subscription", "amount": 15.99},
        {"merchant": "WHOLE FOODS", "description": "Groceries", "amount": 89.42},
        {"merchant": "UBER", "description": "Ride", "amount": 18.50},
        {"merchant": "CVS PHARMACY", "description": "Medicine", "amount": 24.99},
    ]

    print("\n" + "=" * 60)
    print("Testing AI Categorization with GPT-4")
    print("=" * 60)

    for trans in test_transactions:
        category = categorizer.categorize_transaction(
            trans["merchant"],
            trans["description"],
            trans["amount"]
        )

        status = "✅" if category else "❌"
        print(f"{status} {trans['merchant']:25} → {category or 'Failed'}")

    print("=" * 60)

if __name__ == "__main__":
    test_ai_categorization()
