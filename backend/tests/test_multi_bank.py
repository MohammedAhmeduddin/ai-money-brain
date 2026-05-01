import pytest
from pathlib import Path
from app.services.csv_parser import CSVParser

@pytest.fixture
def parser():
    return CSVParser()

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

def test_chase_format(parser, fixtures_dir):
    with open(fixtures_dir / "sample_chase.csv") as f:
        transactions = parser.parse(f.read())

    assert len(transactions) == 5
    assert transactions[0]["merchant"] == "STARBUCKS STORE 12345"
    assert transactions[0]["amount"] == 5.67

def test_wellsfargo_format(parser, fixtures_dir):
    with open(fixtures_dir / "sample_wellsfargo.csv") as f:
        transactions = parser.parse(f.read())

    assert len(transactions) == 4
    assert transactions[0]["merchant"] == "STARBUCKS"

def test_capitalone_format(parser, fixtures_dir):
    with open(fixtures_dir / "sample_capitalone.csv") as f:
        transactions = parser.parse(f.read())

    assert len(transactions) == 4
    # Capital One uses separate Debit column
    assert transactions[0]["amount"] == 5.67

def test_amex_format(parser, fixtures_dir):
    with open(fixtures_dir / "sample_amex.csv") as f:
        transactions = parser.parse(f.read())

    assert len(transactions) == 4
    assert "WHOLE FOODS MARKET" in transactions[0]["merchant"]
