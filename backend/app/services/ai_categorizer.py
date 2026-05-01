"""
AI-powered transaction categorization using GPT-4
"""
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ── Standard normalized categories ────────────────────────────────────────────
CATEGORIES = [
    "Groceries",
    "Dining & Restaurants",
    "Transportation & Gas",
    "Shopping & Retail",
    "Entertainment & Subscriptions",
    "Utilities & Bills",
    "Healthcare",
    "Travel",
    "Personal Care",
    "Home & Garden",
    "Education",
    "Other"
]

# ── Category mapping for fallback matching ────────────────────────────────────
CATEGORY_ALIASES = {
    "bills": "Utilities & Bills",
    "rent": "Utilities & Bills",
    "utilities": "Utilities & Bills",
    "phone": "Utilities & Bills",
    "internet": "Utilities & Bills",
    "gas": "Transportation & Gas",
    "uber": "Transportation & Gas",
    "lyft": "Transportation & Gas",
    "parking": "Transportation & Gas",
    "transit": "Transportation & Gas",
    "amazon": "Shopping & Retail",
    "target": "Shopping & Retail",
    "walmart": "Shopping & Retail",
    "shopping": "Shopping & Retail",
    "netflix": "Entertainment & Subscriptions",
    "spotify": "Entertainment & Subscriptions",
    "gym": "Entertainment & Subscriptions",
    "membership": "Entertainment & Subscriptions",
    "subscription": "Entertainment & Subscriptions",
    "movie": "Entertainment & Subscriptions",
    "game": "Entertainment & Subscriptions",
    "starbucks": "Dining & Restaurants",
    "restaurant": "Dining & Restaurants",
    "cafe": "Dining & Restaurants",
    "coffee": "Dining & Restaurants",
    "food": "Dining & Restaurants",
    "grocery": "Groceries",
    "whole foods": "Groceries",
    "trader joe": "Groceries",
    "health": "Healthcare",
    "medical": "Healthcare",
    "doctor": "Healthcare",
    "hospital": "Healthcare",
    "travel": "Travel",
    "hotel": "Travel",
    "flight": "Travel",
    "salon": "Personal Care",
    "spa": "Personal Care",
    "haircut": "Personal Care",
}


class AICategorizer:
    """Categorize transactions using GPT-4"""

    def __init__(self):
        """Initialize GPT-4 client if API key is available."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("⚠️  OpenAI API key not configured. AI categorization disabled.")

    def _fallback_categorize(self, merchant: str, description: str = "") -> str:
        """
        Fallback categorization using keyword matching.
        Used when AI is disabled or fails.
        """
        search_text = f"{merchant} {description}".lower()

        for keyword, category in CATEGORY_ALIASES.items():
            if keyword in search_text:
                return category

        return "Other"

    def categorize_transaction(
        self,
        merchant: str,
        description: str = "",
        amount: float = 0
    ) -> str:
        """
        Use GPT-4 to categorize a single transaction.

        Args:
            merchant: Merchant name (e.g., "STARBUCKS")
            description: Transaction description (optional)
            amount: Transaction amount (optional)

        Returns:
            Category name from CATEGORIES list
        """
        # ── Fallback if AI disabled ───────────────────────────────────────
        if not self.enabled:
            return self._fallback_categorize(merchant, description)

        prompt = f"""Categorize this transaction into EXACTLY ONE of these categories:
{', '.join(CATEGORIES)}

Transaction Details:
- Merchant: {merchant}
- Description: {description or 'N/A'}
- Amount: ${amount:.2f}

CATEGORIZATION RULES:
- "Utilities & Bills" → Rent, utilities, phone, internet, insurance
- "Transportation & Gas" → Gas stations, Uber, Lyft, parking, transit, taxis
- "Shopping & Retail" → Amazon, Target, Walmart, stores, online shopping
- "Entertainment & Subscriptions" → Netflix, Spotify, gym, movies, games, subscriptions
- "Dining & Restaurants" → Restaurants, cafes, coffee shops, bars, food delivery
- "Groceries" → Supermarkets, grocery stores, farmers markets
- "Healthcare" → Doctors, hospitals, pharmacies, medical supplies
- "Travel" → Hotels, flights, rental cars, travel agencies
- "Personal Care" → Salons, spas, haircuts, barbers
- "Home & Garden" → Hardware stores, furniture, gardening supplies
- "Education" → Schools, tutoring, courses, books
- "Other" → Anything that doesn't fit above

RESPOND WITH:
- ONLY the exact category name (no explanation)
- MUST be from the list above
- Example: "Transportation & Gas"

Category:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise financial transaction categorizer. "
                            "Respond with ONLY the exact category name from the provided list. "
                            "No explanation, no punctuation, just the category name."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=30
            )

            category = response.choices[0].message.content.strip()

            # ── Validate exact match ──────────────────────────────────────
            if category in CATEGORIES:
                return category

            # ── Try fuzzy match ───────────────────────────────────────────
            category_lower = category.lower()
            for valid_cat in CATEGORIES:
                if (valid_cat.lower() in category_lower or
                    category_lower in valid_cat.lower()):
                    return valid_cat

            # ── Fallback to keyword matching ──────────────────────────────
            logger.warning(
                f"AI returned invalid category '{category}' for {merchant}. "
                f"Falling back to keyword matching."
            )
            return self._fallback_categorize(merchant, description)

        except Exception as e:
            logger.error(f"AI categorization failed: {str(e)}. Using fallback.")
            return self._fallback_categorize(merchant, description)

    def categorize_batch(self, transactions: list) -> list:
        """
        Categorize multiple transactions efficiently.

        Args:
            transactions: List of transaction dicts with merchant, description, amount

        Returns:
            Same list with 'category' field updated
        """
        if not transactions:
            return transactions

        for trans in transactions:
            # Only categorize if no category exists or category is "Other"
            if not trans.get("category") or trans.get("category") == "Other":
                ai_category = self.categorize_transaction(
                    merchant=trans.get("merchant", "Unknown"),
                    description=trans.get("description", ""),
                    amount=trans.get("amount", 0)
                )
                if ai_category:
                    trans["category"] = ai_category

        return transactions
