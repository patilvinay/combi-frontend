#!/usr/bin/env python3
"""
Example Python client for the IoT Client REST API.
This script demonstrates how to interact with the API programmatically.
"""

import requests
import json
import time
import argparse
import sys

class IoTClientAPI:
    """Client for interacting with the IoT Client REST API."""

    def __init__(self, base_url="http://localhost:5000", api_key=None):
        """Initialize the API client with the base URL and API key."""
        self.base_url = base_url
        self.api_key = api_key

    def _get_headers(self, additional_headers=None):
        """Get headers for API requests, including the API key if provided."""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def list_devices(self):
        """List all registered devices."""
        response = requests.get(
            f"{self.base_url}/api/devices",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def register_device(self, device_id):
        """Register a new device."""
        response = requests.post(
            f"{self.base_url}/api/register-device",
            json={"deviceId": device_id},
            headers=self._get_headers({"Content-Type": "application/json"})
        )
        response.raise_for_status()
        return response.json()

    def unregister_device(self, device_id):
        """Unregister a device."""
        response = requests.delete(
            f"{self.base_url}/api/unregister-device/{device_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_telemetry(self, device_id=None):
        """Get telemetry data for a device."""
        url = f"{self.base_url}/api/telemetry"
        if device_id:
            url += f"?deviceId={device_id}"

        response = requests.get(
            url,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

def main():
    """Main function to demonstrate the API client."""
    parser = argparse.ArgumentParser(description="IoT Client API Example")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for the API")
    parser.add_argument("--device", default="test-device", help="Device ID to use for testing")
    parser.add_argument("--api-key", default=None, help="API key for authentication")
    args = parser.parse_args()

    client = IoTClientAPI(base_url=args.url, api_key=args.api_key)
    device_id = args.device

    try:
        # List all devices
        print("Listing all devices...")
        devices = client.list_devices()
        print(json.dumps(devices, indent=2))
        print()

        # Register a device
        print(f"Registering device {device_id}...")
        result = client.register_device(device_id)
        print(json.dumps(result, indent=2))
        print()

        # Get telemetry for the device
        print(f"Getting telemetry for device {device_id}...")
        telemetry = client.get_telemetry(device_id)
        print(json.dumps(telemetry, indent=2))
        print()

        # Wait a bit for telemetry to be updated
        print("Waiting for telemetry updates...")
        time.sleep(5)

        # Get updated telemetry
        print(f"Getting updated telemetry for device {device_id}...")
        telemetry = client.get_telemetry(device_id)
        print(json.dumps(telemetry, indent=2))
        print()

        # Unregister the device
        print(f"Unregistering device {device_id}...")
        result = client.unregister_device(device_id)
        print(json.dumps(result, indent=2))
        print()

        # List all devices again
        print("Listing all devices after unregistering...")
        devices = client.list_devices()
        print(json.dumps(devices, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
