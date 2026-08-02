"""
Plugin Provider Registry & Manager (providers/provider_manager.py)
Manages dynamic loading of lead generation provider plugins.
"""

import logger
from providers.google_maps.plugin import GoogleMapsProvider

PROVIDERS = {
    "google_maps": GoogleMapsProvider()
}


def get_provider(name="google_maps"):
    return PROVIDERS.get(name.lower(), PROVIDERS["google_maps"])


def list_providers():
    return [
        {"name": p.name, "version": p.version, "supported": p.supported}
        for p in PROVIDERS.values()
    ]
