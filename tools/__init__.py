# HackWithAI v2 — Dark Web Tools Package
from .darkweb_tools import OnionScraper, DarkWebSearch, LeakedCredsChecker, CryptoScanner, DarkWebMonitor
from .tor_manager import TorManager
from .darkweb_intelligence import (
    DarkWebMarketScanner,
    VendorReputationAnalyzer,
    PrivateForumScanner,
    PrivateCloudScanner,
    PrivateProductsDatabase,
    DarkWebReportGenerator,
    FilteredDarkWebSearch,
)

__all__ = [
    "TorManager",
    "OnionScraper", "DarkWebSearch", "LeakedCredsChecker", "CryptoScanner", "DarkWebMonitor",
    "DarkWebMarketScanner", "VendorReputationAnalyzer", "PrivateForumScanner",
    "PrivateCloudScanner", "PrivateProductsDatabase", "DarkWebReportGenerator",
    "FilteredDarkWebSearch",
]
