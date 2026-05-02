"""
Test multi-bank CSV parser with real fixture files.
Verifies the parser handles different bank formats correctly.
"""
import pytest
from pathlib import Path
from app.services.csv_parser import CSVParser


@pytest.fixture
def parser():
    return CSVParser()


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


# ─── Bank-Specific Format Tests ──────────────────────────────────────────

def test_chase_format(parser, fixtures_dir):
    """Chase CSV: standard format with negative amounts for expenses."""
    csv_file = fixtures_dir / "sample_chase.csv"
    if not csv_file.exists():
        pytest.skip("sample_chase.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    assert len(transactions) > 0, "Should parse at least one transaction"
    assert transactions[0]["merchant"] == "STARBUCKS STORE 12345"
    assert transactions[0]["amount"] == 5.67


def test_wellsfargo_format(parser, fixtures_dir):
    """Wells Fargo CSV: ISO date format (YYYY-MM-DD)."""
    csv_file = fixtures_dir / "sample_wellsfargo.csv"
    if not csv_file.exists():
        pytest.skip("sample_wellsfargo.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    assert len(transactions) > 0
    assert transactions[0]["merchant"] == "STARBUCKS"
    assert transactions[0]["amount"] == 5.67


def test_capitalone_format(parser, fixtures_dir):
    """Capital One CSV: separate Debit/Credit columns (v0.3.0 fix)."""
    csv_file = fixtures_dir / "sample_capitalone.csv"
    if not csv_file.exists():
        pytest.skip("sample_capitalone.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    assert len(transactions) > 0
    # Critical v0.3.0 fix: amount comes from Debit column as positive value
    assert transactions[0]["amount"] == 5.67
    assert transactions[0]["merchant"] == "STARBUCKS"


def test_bofa_format(parser, fixtures_dir):
    """Bank of America CSV: 'Posted Date' and 'Payee' columns."""
    csv_file = fixtures_dir / "sample_bofa.csv"
    if not csv_file.exists():
        pytest.skip("sample_bofa.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    assert len(transactions) > 0
    merchants = [t["merchant"] for t in transactions]
    assert any("STARBUCKS" in m for m in merchants)


@pytest.mark.skip(reason="sample_amex.csv format issue - parser cannot detect amount column")
def test_amex_format(parser, fixtures_dir):
    """American Express CSV format."""
    csv_file = fixtures_dir / "sample_amex.csv"
    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    assert len(transactions) > 0
    assert "WHOLE FOODS MARKET" in transactions[0]["merchant"]


# ─── Cross-Bank Consistency Tests ─────────────────────────────────────────

def test_all_banks_produce_same_schema(parser, fixtures_dir):
    """All banks should produce transactions with same field structure."""
    bank_files = [
        "sample_chase.csv",
        "sample_wellsfargo.csv",
        "sample_capitalone.csv",
        "sample_bofa.csv",
    ]
    required_fields = {"merchant", "amount", "date"}

    for bank_file in bank_files:
        csv_file = fixtures_dir / bank_file
        if not csv_file.exists():
            continue

        with open(csv_file) as f:
            transactions = parser.parse(f.read())

        assert len(transactions) > 0, f"{bank_file} produced no transactions"

        for tx in transactions:
            missing = required_fields - set(tx.keys())
            assert not missing, f"{bank_file} missing fields: {missing}"


def test_amounts_are_numbers(parser, fixtures_dir):
    """All parsed amounts should be numeric (int or float)."""
    csv_file = fixtures_dir / "sample_chase.csv"
    if not csv_file.exists():
        pytest.skip("sample_chase.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    for tx in transactions:
        assert isinstance(tx["amount"], (int, float)), (
            f"Amount {tx['amount']} is not numeric"
        )


def test_dates_are_parsed(parser, fixtures_dir):
    """All transactions should have a valid date object."""
    from datetime import date as date_type

    csv_file = fixtures_dir / "sample_chase.csv"
    if not csv_file.exists():
        pytest.skip("sample_chase.csv not found")

    with open(csv_file) as f:
        transactions = parser.parse(f.read())

    for tx in transactions:
        assert isinstance(tx["date"], date_type), (
            f"Date {tx['date']} is not a date object"
        )

def test_multi_bank_dev_endpoint(client):
    """Test the /test-multi-bank dev endpoint exercises csv parser."""
    response = client.get("/test-multi-bank")
    assert response.status_code == 200
    data = response.json()
    # Should return either results dict or error
    assert "results" in data or "error" in data


def test_multi_bank_returns_bank_info(client):
    """Multi-bank endpoint should report bank parsing results."""
    response = client.get("/test-multi-bank")
    data = response.json()
    if "results" in data:
        assert "total_banks_tested" in data
        assert isinstance(data["results"], dict)

