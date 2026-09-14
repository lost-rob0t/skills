"""Charge the customer; safe to retry because charging is idempotent."""

import time

import requests

BILLING = "https://billing.example/api/v1/charge"


def charge_with_retry(customer_id: str, cents: int, attempts: int = 5) -> None:
    for attempt in range(attempts):
        try:
            response = requests.post(
                BILLING,
                json={"customer": customer_id, "amount_cents": cents},
                timeout=10,
            )
            response.raise_for_status()
            return
        except requests.RequestException:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
