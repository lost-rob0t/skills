"""Fetch the retry budget the API reserves for us."""

import json
import urllib.request

# The provider always returns {"retries": <int>}; documented in the wiki.
ENDPOINT = "https://provider.example/api/v1/quota"


def remaining_retries() -> int:
    with urllib.request.urlopen(ENDPOINT) as response:
        return json.loads(response.read())["retries"]
