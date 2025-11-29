import os
from typing import Any, Dict

import asyncpg

try:
    import stripe
except ImportError:
    stripe = None

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class BillingWebhookHandler:
    """Обработчик вебхуков Stripe."""

    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db = db_pool
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        try:
            import stripe

            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            self.stripe = stripe
        except (ImportError, Exception):
            logger.warning("Stripe not available")
            self.stripe = None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Проверка подписи вебхука Stripe."""
        if not self.webhook_secret:
            return True  # Development mode

        try:
            if self.stripe:
                self.stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret)
                return True
        except Exception:
            return False

        return False

    async def handle_event(self, event: Dict) -> Dict:
        """Обработка события Stripe."""
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        logger.info("Processing Stripe event", extra={"event_type": event_type})

        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)

        if handler:
            await handler(data, event)
            return {"status": "handled"}

        logger.info("Unhandled event type", extra={"event_type": event_type})
        return {"status": "skipped"}

    async def _handle_subscription_created(self, subscription: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Обработка создания подписки."""
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status")

        async with self.db.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM tenants WHERE stripe_customer_id = $1", customer_id)

            if tenant:
                await conn.execute(
                    """
                    UPDATE tenants
                    SET stripe_subscription_id = $1,
                        status = CASE WHEN $2 = 'active' THEN 'active' ELSE status END
                    WHERE id = $3
                """,
                    subscription_id,
                    status,
                    tenant["id"],
                )

                await self._log_billing_event(tenant["id"], "subscription_created", event)

    async def _handle_subscription_updated(self, subscription: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Обработка обновления подписки."""
        subscription_id = subscription.get("id")
        status = subscription.get("status")

        async with self.db.acquire() as conn:
            tenant = await conn.fetchrow(
                "SELECT id FROM tenants WHERE stripe_subscription_id = $1",
                subscription_id,
            )

            if tenant:
                new_status = "active" if status == "active" else "suspended"

                await conn.execute(
                    "UPDATE tenants SET status = $1 WHERE id = $2",
                    new_status,
                    tenant["id"],
                )

                await self._log_billing_event(tenant["id"], "subscription_updated", event)

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Обработка удаления подписки."""
        subscription_id = subscription.get("id")

        async with self.db.acquire() as conn:
            tenant = await conn.fetchrow(
                "SELECT id FROM tenants WHERE stripe_subscription_id = $1",
                subscription_id,
            )

            if tenant:
                await conn.execute(
                    """
                    UPDATE tenants
                    SET status = 'cancelled',
                        subscription_ends_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """,
                    tenant["id"],
                )

                await self._log_billing_event(tenant["id"], "subscription_cancelled", event)

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Обработка успешного платежа."""
        customer_id = invoice.get("customer")
        amount = invoice.get("amount_paid")

        async with self.db.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM tenants WHERE stripe_customer_id = $1", customer_id)

            if tenant:
                await self._log_billing_event(tenant["id"], "payment_succeeded", event, amount_cents=amount)

    async def _handle_payment_failed(self, invoice: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Обработка неудачного платежа."""
        customer_id = invoice.get("customer")

        async with self.db.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM tenants WHERE stripe_customer_id = $1", customer_id)

            if tenant:
                await conn.execute(
                    "UPDATE tenants SET status = 'suspended' WHERE id = $1",
                    tenant["id"],
                )

                await self._log_billing_event(tenant["id"], "payment_failed", event)

    async def _log_billing_event(self, tenant_id: str, event_type: str, event: Dict[str, Any], amount_cents: int | None = None) -> None:
        """Логирование события биллинга."""
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO billing_events (
                    tenant_id,
                    event_type,
                    amount_cents,
                    stripe_event_id,
                    metadata,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                tenant_id,
                event_type,
                amount_cents,
                event.get("id"),
                event,
                event.get("created"),
            )
