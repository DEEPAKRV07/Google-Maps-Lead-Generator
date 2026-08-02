"""
Optional Proxy Manager & Rotation Pool (proxy_manager.py)
Disabled by default (PROXY_ENABLED = False).
Supports residential/datacenter proxies, health checks, cooldowns, and auto-rotation.
"""

import os
import random
import time
import logger
import config

PROXIES_FILE = "proxies.txt"


class ProxyManager:
    """
    Manages a pool of HTTP/HTTPS/SOCKS5 proxies with rotation and health tracking.
    """
    def __init__(self, proxy_file=PROXIES_FILE, enabled=False):
        self.enabled = getattr(config, "PROXY_ENABLED", enabled)
        self.proxies = []
        self.bad_proxies = set()
        self.cooldown_map = {}
        self.load_proxies(proxy_file)

    def load_proxies(self, proxy_file):
        if not self.enabled:
            return

        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        p = line.strip()
                        if p and not p.startswith("#"):
                            if not p.startswith("http://") and not p.startswith("https://") and not p.startswith("socks5://"):
                                p = "http://" + p
                            self.proxies.append(p)
                if self.proxies:
                    logger.info("scraper", f"[PROXY] Loaded {len(self.proxies)} proxies from {proxy_file}")
            except Exception as e:
                logger.warning("scraper", f"[PROXY] Could not read proxies file: {e}")

    def get_proxy(self):
        """
        Returns a healthy proxy string, or None if proxies are disabled/unavailable.
        """
        if not self.enabled or not self.proxies:
            return None

        # Clean cooldowns older than 10 minutes
        now = time.time()
        expired = [p for p, ts in self.cooldown_map.items() if now - ts > 600]
        for p in expired:
            del self.cooldown_map[p]
            self.bad_proxies.discard(p)

        available = [p for p in self.proxies if p not in self.bad_proxies]
        if not available:
            logger.warning("scraper", "[PROXY] All proxies are currently in cooldown. Reusing pool...")
            available = self.proxies

        return random.choice(available)

    def mark_bad(self, proxy_str):
        if proxy_str:
            self.bad_proxies.add(proxy_str)
            self.cooldown_map[proxy_str] = time.time()
            logger.warning("scraper", f"[PROXY] Marked proxy as bad/cooldown: {proxy_str}")


def get_requests_proxy_dict(proxy_url):
    if not proxy_url:
        return None
    return {
        "http": proxy_url,
        "https": proxy_url
    }
