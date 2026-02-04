"""
Temporal Client - Connection to Temporal Cloud.

Handles authentication and provides a connected client for workflows and activities.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def get_temporal_client(project_path: Optional[Path] = None):
    """
    Create and return a connected Temporal client.

    Args:
        project_path: Path to the 1KH project (for loading .env)

    Returns:
        Connected Temporal Client

    Raises:
        ValueError: If required credentials are missing
        ConnectionError: If cannot connect to Temporal Cloud
    """
    # Import here to allow graceful failure if not installed
    from temporalio.client import Client

    # Load credentials from project's .env
    if project_path:
        env_file = project_path / ".1kh" / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    # Get credentials
    api_key = os.environ.get("TEMPORAL_CLOUD_API_KEY")
    namespace = os.environ.get("TEMPORAL_NAMESPACE")
    address = os.environ.get("TEMPORAL_ADDRESS")

    if not api_key:
        raise ValueError(
            "TEMPORAL_CLOUD_API_KEY not found. "
            "Add it to your project's .1kh/.env file."
        )

    if not namespace:
        raise ValueError(
            "TEMPORAL_NAMESPACE not found. "
            "Add it to your project's .1kh/.env file."
        )

    # Derive address from namespace if not specified
    if not address:
        # Temporal Cloud format: namespace.accountId.tmprl.cloud:7233
        # The namespace already contains the full identifier
        if ".tmprl.cloud" in namespace:
            address = f"{namespace}:7233"
        else:
            # Assume it's just the namespace name, need full address
            raise ValueError(
                "TEMPORAL_ADDRESS not found and couldn't derive from namespace. "
                "Add TEMPORAL_ADDRESS to your project's .1kh/.env file.\n"
                "Format: your-namespace.accountId.tmprl.cloud:7233"
            )

    return api_key, namespace, address


async def create_client(project_path: Optional[Path] = None):
    """
    Create an async Temporal client connected to Temporal Cloud.

    This is the main entry point for connecting to Temporal.
    """
    from temporalio.client import Client

    api_key, namespace, address = get_temporal_client(project_path)

    # Debug output
    print(f"  Namespace: {namespace}")
    print(f"  Address: {address}")
    print(f"  API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")

    # Connect with API key authentication
    # Temporal Cloud requires TLS and API key in metadata
    client = await Client.connect(
        address,
        namespace=namespace,
        api_key=api_key,
        tls=True,  # Temporal Cloud always uses TLS
    )

    return client
