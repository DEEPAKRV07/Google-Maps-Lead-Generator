"""
Google Maps Provider Plugin (providers/google_maps/plugin.py)
Implements BaseProvider interface for Google Maps lead generation.
"""

from providers.base_provider import BaseProvider
from providers.google_maps.selectors import NAME_SELECTORS, PHONE_SELECTORS, WEBSITE_SELECTORS, RATING_SELECTORS, REVIEWS_SELECTORS, HOURS_SELECTORS


class GoogleMapsProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="Google Maps", version="2.0.0")

    def search(self, category, location):
        """
        Formats Google Maps search URL for category and location.
        """
        query = f"{category} in {location}"
        return f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    def extract_details(self, place_item):
        """
        Standardizes lead dictionary representation.
        """
        return place_item
