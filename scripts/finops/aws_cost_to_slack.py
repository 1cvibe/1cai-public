#!/usr/bin/env python3
"""Send AWS cost report to Slack webhook."""

from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any, Dict

import boto3
import requests

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def fetch_costs(days: int = 3) -> Dict[str, float]:
    client = boto3.client("ce", region_name=os.getenv("AWS_REGION", "us-east-1"))
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat(),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    return {
        item["TimePeriod"]["Start"]: float(item["Total"]["UnblendedCost"]["Amount"])
        for item in response["ResultsByTime"]
    }


def post_to_slack(costs: Dict[str, float]) -> None:
    if not WEBHOOK_URL:
        raise RuntimeError("SLACK_WEBHOOK_URL is not set")
    lines = [f"• {date}: ${amount:.2f}" for date, amount in sorted(costs.items())]
    payload = {
        "text": "AWS Cost Report (last 3 days)\n" + "\n".join(lines)
    }
    resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    resp.raise_for_status()


def main() -> None:
    costs = fetch_costs()
    post_to_slack(costs)


if __name__ == "__main__":
    main()
