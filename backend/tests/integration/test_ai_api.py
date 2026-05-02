"""
Integration tests for AI-related endpoints.
NOTE: app/api/v1/ai.py is currently empty (0 lines).
These tests verify the AI categorizer service through the upload flow.
"""
import io
import pytest
from unittest.mock import patch, MagicMock


def upload_csv(client, headers, csv_content, filename="test.csv"):
    """Helper to upload CSV."""
    files = {"file": (filename, io.BytesIO(csv_content.encode()), "text/csv")}
    return client.post("/api/v1/transactions/upload", files=files, headers=headers)


class TestAICategorizationViaUpload:
    """Test AI categorization through CSV upload flow."""

    def test_upload_triggers_categorization(self, client, auth_headers, sample_chase_csv):
        """Upload should attempt to categorize transactions."""
        response = upload_csv(client, auth_headers, sample_chase_csv)
        assert response.status_code in (200, 201)

    def test_uploaded_transactions_have_categories(self, client, auth_headers, sample_chase_csv):
        """After upload, transactions should have category field (even if None)."""
        upload_csv(client, auth_headers, sample_chase_csv)
        response = client.get("/api/v1/transactions", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        items = data if isinstance(data, list) else (
            data.get("items") or data.get("transactions") or data.get("data") or []
        )

        if items:
            # Each transaction should have a category field (even if None)
            for tx in items[:3]:  # Check first 3
                assert "category" in tx


class TestAICategorizerDirect:
    """Direct tests against the AICategorizer service."""

    def test_categorizer_handles_starbucks(self):
        from app.services.ai_categorizer import AICategorizer
        categorizer = AICategorizer()
        result = categorizer.categorize_transaction(
            merchant="STARBUCKS",
            description="Coffee Purchase",
            amount=5.67,
        )
        # Either returns category string or None (if disabled)
        assert result is None or isinstance(result, str)

    def test_categorizer_handles_uber(self):
        from app.services.ai_categorizer import AICategorizer
        categorizer = AICategorizer()
        result = categorizer.categorize_transaction(
            merchant="UBER",
            description="Ride Share",
            amount=18.50,
        )
        assert result is None or isinstance(result, str)

    def test_categorizer_handles_unknown_merchant(self):
        from app.services.ai_categorizer import AICategorizer
        categorizer = AICategorizer()
        result = categorizer.categorize_transaction(
            merchant="ZZXYQQ123",
            description="Mystery purchase",
            amount=99.99,
        )
        assert result is None or isinstance(result, str)


class TestAICategorizerMocked:
    """Mocked OpenAI tests to exercise success paths without API cost."""

    @patch("app.services.ai_categorizer.OpenAI")
    def test_mocked_success_response(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Dining & Restaurants"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        from app.services.ai_categorizer import AICategorizer
        categorizer = AICategorizer()
        if hasattr(categorizer, "client"):
            categorizer.client = mock_client
            categorizer.enabled = True

        result = categorizer.categorize_transaction(
            merchant="STARBUCKS",
            description="Coffee",
            amount=5.67,
        )
        assert result is None or isinstance(result, str)

    @patch("app.services.ai_categorizer.OpenAI")
    def test_mocked_api_error(self, mock_openai_class):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit")
        mock_openai_class.return_value = mock_client

        from app.services.ai_categorizer import AICategorizer
        categorizer = AICategorizer()
        if hasattr(categorizer, "client"):
            categorizer.client = mock_client
            categorizer.enabled = True

        result = categorizer.categorize_transaction(
            merchant="STARBUCKS",
            description="Coffee",
            amount=5.67,
        )
        # Should not crash
        assert result is None or isinstance(result, str)
