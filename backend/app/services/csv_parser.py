"""
Universal CSV Parser - Handles ANY bank CSV format
Supports: Bank of America, Chase, Wells Fargo, Capital One, Amex, and more
"""
import pandas as pd
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime
import re


class CSVValidationError(Exception):
    """Custom exception for CSV validation errors"""
    pass


class CSVParser:
    """
    Universal CSV parser that intelligently detects and handles ANY bank format
    """

    # Comprehensive column patterns for ALL banks
    COLUMN_PATTERNS = {
        "date": [
            # Common variations
            "date", "posted date", "transaction date", "trans date",
            "post date", "posting date", "trans. date", "effective date",
            "value date", "booking date", "cleared date"
        ],
        "amount": [
            # Amount columns
            "amount", "debit", "credit", "transaction amount",
            "charge amount", "payment amount", "withdrawal", "deposit",
            "value", "sum", "total", "balance", "charged amount"
        ],
        "merchant": [
            # Merchant/description columns
            "description", "merchant", "payee", "memo", "details",
            "transaction description", "name", "notes", "reference",
            "particulars", "narration", "vendor", "supplier"
        ],
        "category": [
            # Category columns
            "category", "type", "transaction type", "class",
            "classification", "group", "spending category"
        ],
        "reference": [
            # Transaction ID/Reference
            "reference number", "reference", "ref number", "transaction id",
            "trans id", "confirmation number", "ref", "id", "transaction number"
        ]
    }

    # Merchant name cleaning patterns (universal)
    MERCHANT_CLEANING_PATTERNS = [
        # Payment processors
        (r'^SQ \*', ''),           # Square
        (r'^TST\*', ''),           # Toast POS
        (r'^DD \*', ''),           # DoorDash
        (r'^CBI\*', ''),           # CBI
        (r'^STRIPE\*', ''),        # Stripe
        (r'^PAYPAL \*', ''),       # PayPal
        (r'^UBER \*', ''),         # Uber
        (r'^SP \*', ''),           # Stripe
        (r'^POS ', ''),            # Point of Sale

        # Remove location codes
        (r'\s+#\d+', ''),          # Store numbers
        (r'\s+\d{3}-\d{3}-\d{4}', ''),  # Phone numbers

        # Clean up state codes at end
        (r'\s+[A-Z]{2}\s*$', ''),  # State codes
    ]

    # Keywords for detecting recurring/subscription transactions
    RECURRING_KEYWORDS = [
        'subscription', 'monthly', 'netflix', 'spotify', 'hulu', 'disney',
        'apple music', 'youtube premium', 'amazon prime', 'prime video',
        'gym', 'fitness', 'planet fitness', 'anytime fitness',
        'insurance', 'geico', 'progressive', 'state farm',
        'phone', 'verizon', 'at&t', 't-mobile', 'sprint', 'visible',
        'internet', 'comcast', 'xfinity', 'spectrum',
        'utilities', 'electric', 'gas', 'water',
        'openai', 'github', 'adobe', 'microsoft', 'google one',
        'icloud', 'dropbox', 'patreon', 'onlyfans',
        'dashpass', 'doordash', 'uber pass'
    ]

    def detect_column(self, header: str, column_type: str) -> bool:
        """
        Intelligently detect if a column header matches a column type
        Uses fuzzy matching for flexibility
        """
        header_lower = header.lower().strip()
        patterns = self.COLUMN_PATTERNS[column_type]

        # Exact match or contains match
        return any(
            pattern == header_lower or pattern in header_lower
            for pattern in patterns
        )

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect column mappings from ANY bank format
        Returns mapping of standard names to actual column names
        """
        column_map = {}

        for col in df.columns:
            col_str = str(col).strip()

            # Try to match each column type (priority order matters)
            for col_type in ["date", "amount", "merchant", "category", "reference"]:
                if col_type not in column_map:  # Only map once
                    if self.detect_column(col_str, col_type):
                        column_map[col_type] = col_str
                        break

        return column_map

    def clean_merchant_name(self, merchant: str) -> str:
        """
        Clean merchant name from various bank formats
        Removes payment processor prefixes, phone numbers, locations
        """
        if not merchant or pd.isna(merchant):
            return "Unknown"

        merchant_str = str(merchant).strip()

        # Apply all cleaning patterns
        for pattern, replacement in self.MERCHANT_CLEANING_PATTERNS:
            merchant_str = re.sub(pattern, replacement, merchant_str, flags=re.IGNORECASE)

        # Clean up extra spaces and capitalize properly
        merchant_str = ' '.join(merchant_str.split())

        return merchant_str if merchant_str else "Unknown"

    def parse_amount(self, value) -> float:
        """
        Universal amount parser
        Handles: negative signs, parentheses, currency symbols, commas
        """
        if pd.isna(value):
            return 0.0

        # Convert to string and clean
        amount_str = str(value).strip()

        # Remove currency symbols
        amount_str = re.sub(r'[$,£€¥₹₽¢]', '', amount_str)

        # Handle accounting format: (123.45) = -123.45
        if '(' in amount_str and ')' in amount_str:
            amount_str = '-' + amount_str.replace('(', '').replace(')', '')

        # Remove any remaining non-numeric except decimal and minus
        amount_str = re.sub(r'[^\d.-]', '', amount_str)

        try:
            return float(amount_str)
        except ValueError:
            return 0.0

    def parse_date(self, value) -> Optional[datetime]:
        """
        Universal date parser - tries multiple formats
        Handles: US, EU, ISO, and custom formats
        """
        if pd.isna(value):
            return None

        date_formats = [
            # US formats
            "%m/%d/%Y",      # 03/20/2026 (Bank of America, Chase)
            "%m/%d/%y",      # 03/20/26
            "%m-%d-%Y",      # 03-20-2026
            "%m-%d-%y",      # 03-20-26

            # ISO formats
            "%Y-%m-%d",      # 2026-03-20 (International standard)
            "%Y/%m/%d",      # 2026/03/20

            # EU formats
            "%d/%m/%Y",      # 20/03/2026
            "%d/%m/%y",      # 20/03/26
            "%d-%m-%Y",      # 20-03-2026
            "%d-%m-%y",      # 20-03-26

            # Named months
            "%b %d, %Y",     # Mar 20, 2026
            "%B %d, %Y",     # March 20, 2026
            "%d %b %Y",      # 20 Mar 2026
            "%d %B %Y",      # 20 March 2026
        ]

        date_str = str(value).strip()

        # Try each format
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Fallback to pandas date parser (very flexible)
        try:
            return pd.to_datetime(date_str)
        except:
            return None

    def detect_recurring(self, merchant: str, amount: float) -> bool:
        """
        Detect if transaction is likely recurring/subscription
        Uses merchant name and amount patterns
        """
        merchant_lower = merchant.lower()

        # Check keywords
        if any(keyword in merchant_lower for keyword in self.RECURRING_KEYWORDS):
            return True

        # Subscription-like amounts (rounded numbers)
        # e.g., 9.99, 19.99, 29.99, 10.00, 20.00
        if amount in [9.99, 19.99, 29.99, 39.99, 49.99, 99.99]:
            return True

        if amount in [5.00, 10.00, 15.00, 20.00, 25.00, 30.00, 50.00, 100.00]:
            return True

        return False

    def is_payment_or_credit(self, merchant: str, amount: float) -> bool:
        """
        Detect if transaction is a payment/credit (should be excluded)
        """
        merchant_lower = merchant.lower()

        payment_keywords = [
            'payment', 'online payment', 'autopay', 'direct debit',
            'transfer', 'deposit', 'payroll', 'salary', 'refund',
            'credit adjustment', 'cashback', 'reward', 'interest paid'
        ]

        return any(keyword in merchant_lower for keyword in payment_keywords)

    def parse(self, csv_content: str) -> List[Dict]:
        """
        Universal CSV parser - handles ANY bank format

        Args:
            csv_content: CSV file content as string

        Returns:
            List of standardized transaction dictionaries

        Raises:
            CSVValidationError: If CSV is invalid or missing required columns
        """
        try:
            # Read CSV (handle different delimiters)
            try:
                df = pd.read_csv(StringIO(csv_content))
            except:
                # Try semicolon delimiter (some EU banks)
                df = pd.read_csv(StringIO(csv_content), sep=';')

            if df.empty:
                raise CSVValidationError("CSV file is empty")

            # Auto-detect columns
            column_map = self.detect_columns(df)

            # Validate required columns
            if "date" not in column_map:
                raise CSVValidationError(
                    f"Could not find date column. Available columns: {list(df.columns)}"
                )

            if "amount" not in column_map:
                raise CSVValidationError(
                    f"Could not find amount column. Available columns: {list(df.columns)}"
                )

            # Get merchant column (optional but recommended)
            merchant_column = column_map.get("merchant")

            # Parse transactions
            transactions = []
            skipped_payments = 0

            for _, row in df.iterrows():
                # Parse date
                transaction_date = self.parse_date(row[column_map["date"]])
                if not transaction_date:
                    continue  # Skip rows with invalid dates

                # Parse amount
                amount = self.parse_amount(row[column_map["amount"]])

                # Get merchant/description
                merchant = "Unknown"
                if merchant_column and merchant_column in row.index:
                    merchant_raw = row[merchant_column]
                    merchant = self.clean_merchant_name(merchant_raw)

                # Skip payments/credits based on keywords or positive amounts
                # (Bank of America: positive = payment, negative = expense)
                # (Some banks: positive = expense, negative = payment)
                # We use merchant keywords to be safe
                if self.is_payment_or_credit(merchant, amount):
                    skipped_payments += 1
                    continue

                # Convert amount to positive (expenses stored as positive)
                amount = abs(amount)

                # Skip zero or very small amounts
                if amount < 0.01:
                    continue

                # Get category (if provided by bank)
                category = None
                if "category" in column_map:
                    category_val = row[column_map["category"]]
                    if pd.notna(category_val):
                        category = str(category_val).strip()

                # Detect recurring transactions
                is_recurring = self.detect_recurring(merchant, amount)

                # Create standardized transaction
                transaction = {
                    "date": transaction_date.date(),
                    "merchant": merchant,
                    "description": merchant,  # Can be enhanced with full description
                    "amount": amount,
                    "category": category,  # Usually None, AI will categorize
                    "payment_type": "credit_card",  # Default assumption
                    "is_recurring": is_recurring
                }

                transactions.append(transaction)

            if not transactions:
                raise CSVValidationError(
                    f"No valid expense transactions found. "
                    f"Skipped {skipped_payments} payment/credit entries. "
                    f"Please ensure the CSV contains transaction data."
                )

            return transactions

        except pd.errors.ParserError as e:
            raise CSVValidationError(f"Failed to parse CSV: {str(e)}")
        except Exception as e:
            if isinstance(e, CSVValidationError):
                raise
            raise CSVValidationError(f"Error processing CSV: {str(e)}")

    def validate_csv_size(self, file_size: int, max_size_mb: int = 10) -> bool:
        """Validate CSV file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
