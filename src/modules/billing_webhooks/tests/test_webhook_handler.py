import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.billing_webhooks.services.webhook_handler import BillingWebhookHandler

@pytest.mark.asyncio
async def test_webhook_handler_initialization():
    """Тест инициализации обработчика вебхуков."""
    mock_pool = AsyncMock()
    handler = BillingWebhookHandler(mock_pool)
    assert handler.db == mock_pool
    # Stripe might be None if not installed/configured, but object should exist
    assert hasattr(handler, 'verify_signature')
    assert hasattr(handler, 'handle_event')

@pytest.mark.asyncio
async def test_verify_signature_dev_mode():
    """Тест проверки подписи в режиме разработки (без секрета)."""
    mock_pool = AsyncMock()
    handler = BillingWebhookHandler(mock_pool)
    handler.webhook_secret = "" # Force empty secret
    assert handler.verify_signature(b"payload", "sig") is True
