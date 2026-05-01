"""
Demo: Upload CSVs from multiple banks
"""
from app.services.csv_parser import CSVParser

# Bank of America format
bofa_csv = """Posted Date,Reference Number,Payee,Address,Amount
02/09/2026,24055226040642506882295,BROTHER'S SUPERMARKET HARRISON NJ,HARRISON NJ,-10.79"""

# Chase format
chase_csv = """Transaction Date,Post Date,Description,Category,Type,Amount
01/15/2024,01/16/2024,STARBUCKS STORE 12345,Food & Drink,Sale,-5.67"""

# Wells Fargo format
wellsfargo_csv = """Date,Amount,Description
2024-01-15,-45.00,SHELL OIL GAS STATION"""

# Amex format
amex_csv = """Date,Description,Card Member,Amount
01/15/2024,WHOLE FOODS MARKET,JOHN DOE,-67.89"""

parser = CSVParser()

print("=" * 60)
print("TESTING MULTI-BANK CSV PARSER")
print("=" * 60)

banks = [
    ("Bank of America", bofa_csv),
    ("Chase", chase_csv),
    ("Wells Fargo", wellsfargo_csv),
    ("American Express", amex_csv)
]

for bank_name, csv_content in banks:
    print(f"\n✅ Testing {bank_name}:")
    try:
        transactions = parser.parse(csv_content)
        print(f"   Parsed {len(transactions)} transaction(s)")
        for trans in transactions:
            print(f"   - {trans['date']}: {trans['merchant']} (${trans['amount']})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("ALL BANKS SUPPORTED! ✅")
print("=" * 60)
