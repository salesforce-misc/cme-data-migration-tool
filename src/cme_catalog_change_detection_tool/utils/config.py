from __future__ import annotations

"""App configuration utilities.

Parses input JSON for Salesforce credentials and runtime settings. Provides
helpers for building date window SOQL and a timestamped output folder name.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AppConfig:
    """
    Reads the config from input JSON and stores it
    """
    username: str
    password: str
    instance_url: Optional[str]
    number_of_days: int
    product_id: Optional[str]
    domain: str
    output_dir: str

    @staticmethod
    def from_file(path: str, override_product_id: Optional[str] = None) -> "AppConfig":
        """
        Load config from JSON file
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        username = raw.get("username")
        password = raw.get("password")
        if not username or not password:
            raise ValueError("username and password are required in input JSON")

        instance_url = raw.get("instance_url")

        number_of_days = int(raw.get("number_of_days")) if raw.get("number_of_days") is not None else 7
        product_id = override_product_id or raw.get("product_id")
        domain = raw.get("domain") or "login"
        output_dir = raw.get("output_dir") or "output"

        return AppConfig(
            username=username,
            password=password,
            instance_url=instance_url,
            number_of_days=number_of_days,
            product_id=product_id,
            domain=domain,
            output_dir=output_dir,
        )

    @property
    def timestamp_folder(self) -> str:
        """
        Creaet a UTC timestamp formatted folder name
        """
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


