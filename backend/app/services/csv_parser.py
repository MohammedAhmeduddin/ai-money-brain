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

    # ── Column patterns ───────────────────────────────────────────────────────
    COLUMN_PATTERNS = {
        "date": [
            "date", "posted date", "transaction date", "trans date",
            "post date", "posting date", "trans. date", "effective date",
            "value date", "booking date", "cleared date"
        ],
        "amount": [
            # Single-column amount formats (NOT debit/credit split)
            "amount", "transaction amount", "charge amount",
            "payment amount", "value", "sum", "charged amount"
        ],
        "debit": [
            # Split debit column (Capital One, some BofA)
            "debit", "withdrawal", "debit amount"
        ],
        "credit": [
            # Split credit column (Capital One, some BofA)
            "credit", "deposit", "credit amount"
        ],
        "merchant": [
            # ⚠️ "reference" removed — BofA puts ref numbers before payee
            "description", "merchant", "payee", "memo", "details",
            "transaction description", "name", "notes",
            "particulars", "narration", "vendor", "supplier"
        ],
        "category": [
            "category", "type", "transaction type", "class",
            "classification", "group", "spending category"
        ],
    }

    MERCHANT_CLEANING_PATTERNS = [
        (r'^SQ \*', ''),
        (r'^TST\*', ''),
        (r'^DD \*', ''),
        (r'^CBI\*', ''),
        (r'^STRIPE\*', ''),
        (r'^PAYPAL \*', ''),
        (r'^UBER \*', ''),
        (r'^SP \*', ''),
        (r'^POS ', ''),
        (r'\s+#\d+', ''),
        (r'\s+\d{3}-\d{3}-\d{4}', ''),
        (r'\s+[A-Z]{2}\s*$', ''),
    ]

    RECURRING_KEYWORDS = [
        'subscription', 'monthly', 'netflix', 'spotify', 'hulu', 'disney',
        'apple music', 'youtube premium', 'amazon prime', 'prime video',
        'gym', 'fitness', 'planet fitness', 'anytime fitness',
        'insurance', 'geico', 'progressive', 'state farm',
        'phone', 'verizon', 'at&t', 't-mobile', 'sprint', 'visible',
        'internet', 'comcast', 'xfinity', 'spectrum',
        'utilities', 'electric', 'gas', 'water',
        'openai', 'github', 'adobe', 'microsoft', 'google one',
        'icloud', 'dropbox', 'patreon',
        'dashpass', 'doordash', 'uber pass'
    ]

    PAYMENT_KEYWORDS = [
        'online payment', 'autopay', 'direct debit',
        'credit adjustment', 'cashback', 'reward', 'interest paid',
        'payment thank you', 'thank you', 'payment received',
        'balance transfer',
    ]

    INCOME_KEYWORDS = [
        'payroll', 'direct deposit', 'salary', 'employer direct',
        'wages', 'income', 'paycheck'
    ]

    # ── Column detection ──────────────────────────────────────────────────────

    def detect_column(self, header: str, column_type: str) -> bool:
        """Check if a column header matches a known pattern for column_type."""
        header_lower = header.lower().strip()
        patterns = self.COLUMN_PATTERNS.get(column_type, [])
        return any(
            pattern == header_lower or pattern in header_lower
            for pattern in patterns
        )

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect column mappings from ANY bank format.
        Handles both single 'Amount' column AND split 'Debit'/'Credit' columns.
        """
        column_map = {}

        for col in df.columns:
            col_str = str(col).strip()
            # Check all types including debit/credit separately
            for col_type in ["date", "amount", "debit", "credit",
                              "merchant", "category"]:
                if col_type not in column_map:
                    if self.detect_column(col_str, col_type):
                        column_map[col_type] = col_str
                        break

        return column_map

    # ── Amount resolution ─────────────────────────────────────────────────────

    def clean_merchant_name(self, merchant: str) -> str:
        """Clean merchant name from various bank formats."""
        if not merchant or pd.isna(merchant):
            return "Unknown"

        merchant_str = str(merchant).strip()

        for pattern, replacement in self.MERCHANT_CLEANING_PATTERNS:
            merchant_str = re.sub(pattern, replacement, merchant_str, flags=re.IGNORECASE)

        merchant_str = ' '.join(merchant_str.split())
        return merchant_str if merchant_str else "Unknown"



    def parse_amount(self, value) -> float:
        """
        Universal amount parser.
        Handles: negative signs, parentheses, currency symbols, commas.
        Returns signed float (negative = expense for Chase/Amex/WF format).
        """
        if pd.isna(value):
            return 0.0

        amount_str = str(value).strip()

        if not amount_str or amount_str in ('', '-', 'nan', 'None'):
            return 0.0

        amount_str = re.sub(r'[$,£€¥₹₽¢]', '', amount_str)

        if '(' in amount_str and ')' in amount_str:
            amount_str = '-' + amount_str.replace('(', '').replace(')', '')

        amount_str = re.sub(r'[^\d.-]', '', amount_str)

        try:
            return float(amount_str)
        except (ValueError, TypeError):
            return 0.0

    def resolve_amount(self, row, column_map: Dict[str, str]) -> Optional[float]:
        """
        Resolve transaction amount handling two formats:

        Format A — Single amount column (Chase, Amex, Wells Fargo):
          Amount = -45.00  → expense
          Amount = +2500   → income (skip)

        Format B — Split Debit/Credit columns (Capital One):
          Debit = 45.00, Credit = (empty) → expense
          Debit = (empty), Credit = 2500  → income (skip)

        Returns:
          positive float  → expense (keep)
          None            → income/skip
        """
        # ── Format A: single amount column ───────────────────────────────
        if "amount" in column_map:
            amt = self.parse_amount(row[column_map["amount"]])
            if amt < 0:
                return abs(amt)   # expense
            elif amt > 0:
                return None       # income — skip
            return None

        # ── Format B: split debit / credit ───────────────────────────────
        if "debit" in column_map or "credit" in column_map:
            debit  = 0.0
            credit = 0.0

            if "debit" in column_map:
                raw = row[column_map["debit"]]
                if pd.notna(raw) and str(raw).strip() not in ('', '-', 'nan'):
                    debit = abs(self.parse_amount(raw))

            if "credit" in column_map:
                raw = row[column_map["credit"]]
                if pd.notna(raw) and str(raw).strip() not in ('', '-', 'nan'):
                    credit = abs(self.parse_amount(raw))

            if debit > 0:
                return debit    # expense — keep
            elif credit > 0:
                return None     # income — skip
            return None

        return None

    # ── Helper detectors ──────────────────────────────────────────────────────

    def parse_date(self, value) -> Optional[datetime]:
        """Universal date parser — tries multiple formats."""
        if pd.isna(value):
            return None

        date_str = str(value).strip()
        date_formats = [
            "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y",
            "%Y-%m-%d", "%Y/%m/%d",
            "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y",
            "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        try:
            return pd.to_datetime(date_str)
        except Exception:
            return None

    def detect_recurring(self, merchant: str, amount: float) -> bool:
        """Detect if transaction is likely recurring/subscription."""
        merchant_lower = merchant.lower()
        if any(kw in merchant_lower for kw in self.RECURRING_KEYWORDS):
            return True
        if amount in [9.99, 19.99, 29.99, 39.99, 49.99, 99.99]:
            return True
        if amount in [5.00, 10.00, 15.00, 20.00, 25.00, 30.00, 50.00, 100.00]:
            return True
        return False

    def is_payment_or_credit(self, merchant: str) -> bool:
        """Detect payments/credits that should be excluded."""
        merchant_lower = merchant.lower()
        return any(kw in merchant_lower for kw in self.PAYMENT_KEYWORDS)

    def is_income(self, merchant: str) -> bool:
        """Detect income/payroll transactions."""
        merchant_lower = merchant.lower()
        return any(kw in merchant_lower for kw in self.INCOME_KEYWORDS)

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, csv_content: str) -> List[Dict]:
        """
        Main entry point — parse raw CSV string into standardized transactions.
        """
        try:
            try:
                df = pd.read_csv(StringIO(csv_content))
            except Exception:
                df = pd.read_csv(StringIO(csv_content), sep=';')

            # Strip whitespace from column names
            df.columns = [str(c).strip() for c in df.columns]

            if df.empty:
                raise CSVValidationError("CSV file is empty")

            column_map = self.detect_columns(df)

            if "date" not in column_map:
                raise CSVValidationError(
                    f"Could not find date column. Available: {list(df.columns)}"
                )

            has_amount = "amount" in column_map
            has_debit  = "debit"  in column_map
            has_credit = "credit" in column_map

            if not has_amount and not has_debit and not has_credit:
                raise CSVValidationError(
                    f"Could not find amount column. Available: {list(df.columns)}"
                )

            merchant_column = column_map.get("merchant")
            transactions    = []
            skipped         = 0

            for _, row in df.iterrows():

                # ── Date ─────────────────────────────────────────────────
                txn_date = self.parse_date(row[column_map["date"]])
                if not txn_date:
                    continue

                # ── Merchant ─────────────────────────────────────────────
                merchant = "Unknown"
                if merchant_column and merchant_column in row.index:
                    merchant = self.clean_merchant_name(row[merchant_column])

                # ── Skip income & payments ────────────────────────────────
                if self.is_income(merchant) or self.is_payment_or_credit(merchant):
                    skipped += 1
                    continue

                # ── Amount ───────────────────────────────────────────────
                amount = self.resolve_amount(row, column_map)

                if amount is None or amount < 0.01:
                    skipped += 1
                    continue

                # ── Category ─────────────────────────────────────────────
                category = None
                if "category" in column_map:
                    cat_val = row[column_map["category"]]
                    if pd.notna(cat_val) and str(cat_val).strip():
                        category = str(cat_val).strip()

                # ── Recurring ────────────────────────────────────────────
                is_recurring = self.detect_recurring(merchant, amount)

                transactions.append({
                    "date":         txn_date.date(),
                    "merchant":     merchant,
                    "description":  merchant,
                    "amount":       amount,
                    "category":     category,
                    "payment_type": "credit_card",
                    "is_recurring": is_recurring,
                })

            if not transactions:
                raise CSVValidationError(
                    f"No valid expense transactions found. "
                    f"Skipped {skipped} income/payment entries."
                )

            return transactions

        except pd.errors.ParserError as e:
            raise CSVValidationError(f"Failed to parse CSV: {str(e)}")
        except Exception as e:
            if isinstance(e, CSVValidationError):
                raise
            raise CSVValidationError(f"Error processing CSV: {str(e)}")

    def validate_csv_size(self, file_size: int, max_size_mb: int = 10) -> bool:
        """Validate CSV file size."""
        return file_size <= max_size_mb * 1024 * 1024
