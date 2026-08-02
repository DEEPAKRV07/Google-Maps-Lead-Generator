"""
Abstract Base Provider Interface (providers/base_provider.py)
Defines the standard plugin contract for all lead data providers.
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    def __init__(self, name, version="1.0.0"):
        self.name = name
        self.version = version
        self.supported = True

    @abstractmethod
    def search(self, category, location):
        """
        Executes a search for a category in a given location.
        Returns a list of raw place URLs or items.
        """
        pass

    @abstractmethod
    def extract_details(self, place_item):
        """
        Extracts detailed lead information from a place item.
        Returns a standard dictionary representation of the lead.
        """
        pass
