"""
AI-powered transaction categorization using GPT-4
"""
from openai import OpenAI
from app.core.config import settings
import os

# Standard categories
CATEGORIES = [
    "Groceries",
    "Dining & Restaurants",
    "Transportation & Gas",
    "Shopping & Retail",
    "Entertainment",
    "Subscriptions",
    "Utilities & Bills",
    "Healthcare",
    "Travel",
    "Personal Care",
    "Home & Garden",
    "Education",
    "Other"
]


class AICategorizer:
    """Categorize transactions using GPT-4"""

    def __init__(self):
        # Only initialize if API key is configured
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("⚠️  OpenAI API key not configured. AI categorization disabled.")

    def categorize_transaction(self, merchant: str, description: str = "", amount: float = 0) -> str:
        """
        Use GPT-4 to categorize a single transaction

        Args:
            merchant: Merchant name (e.g., "STARBUCKS")
            description: Transaction description (optional)
            amount: Transaction amount (optional)

        Returns:
            Category name from CATEGORIES list, or None if AI disabled
        """
        if not self.enabled:
            return None

        prompt = f"""Categorize this transaction into ONE of these categories:
{', '.join(CATEGORIES)}

Transaction:
- Merchant: {merchant}
- Description: {description or 'N/A'}
- Amount: ${amount}

Reply with ONLY the category name, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial transaction categorizer. Reply with only the category name from the provided list."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=20
            )

            category = response.choices[0].message.content.strip()

            # Validate category is in our list
            if category in CATEGORIES:
                return category

            # Try fuzzy match
            for valid_cat in CATEGORIES:
                if category.lower() in valid_cat.lower() or valid_cat.lower() in category.lower():
                    return valid_cat

            return "Other"

        except Exception as e:
            print(f"❌ Error categorizing transaction: {e}")
            return None

    def categorize_batch(self, transactions: list) -> list:
        """
        Categorize multiple transactions

        Args:
            transactions: List of transaction dicts with merchant, description, amount

        Returns:
            Same list with 'category' field updated if AI categorization succeeds
        """
        if not self.enabled:
            return transactions

        for trans in transactions:
            # Only categorize if no category exists
            if not trans.get("category"):
                ai_category = self.categorize_transaction(
                    merchant=trans.get("merchant", "Unknown"),
                    description=trans.get("description", ""),
                    amount=trans.get("amount", 0)
                )
                if ai_category:
                    trans["category"] = ai_category

        return transactions
