"""
Adaptive Delays & Anti-Detection Fingerprint Engine (antidetect.py)
Provides user agent rotation, dynamic viewport randomization, human-like mouse movement,
smooth scroll velocity, and adaptive delay pacing based on response latency.
"""

import random
import time
import logger

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864}
]


def get_random_user_agent():
    return random.choice(USER_AGENTS)


def get_random_viewport():
    return random.choice(VIEWPORTS)


def simulate_human_scroll(page, min_scrolls=2, max_scrolls=4):
    """
    Simulates smooth human scrolling with random step increments and micro pauses.
    """
    try:
        scrolls = random.randint(min_scrolls, max_scrolls)
        for _ in range(scrolls):
            distance = random.randint(250, 600)
            page.mouse.wheel(0, distance)
            time.sleep(random.uniform(0.3, 0.8))
    except Exception as e:
        logger.warning("scraper", f"Human scroll simulation notice: {e}")


def simulate_human_mouse_movement(page):
    """
    Simulates human mouse cursor movement across coordinates.
    """
    try:
        vp = page.viewport_size or {"width": 1366, "height": 768}
        w, h = vp["width"], vp["height"]
        start_x, start_y = random.randint(100, w - 100), random.randint(100, h - 100)
        end_x, end_y = random.randint(100, w - 100), random.randint(100, h - 100)

        # Move mouse smoothly between start and end
        steps = random.randint(5, 10)
        for i in range(steps):
            curr_x = start_x + int((end_x - start_x) * (i / steps))
            curr_y = start_y + int((end_y - start_y) * (i / steps))
            page.mouse.move(curr_x, curr_y)
            time.sleep(random.uniform(0.02, 0.05))
    except Exception as e:
        logger.warning("scraper", f"Mouse movement simulation notice: {e}")


class AdaptivePacingEngine:
    """
    Monitors response latency and adjusts delay pacing dynamically.
    """
    def __init__(self, base_delay_min=1.0, base_delay_max=2.5):
        self.base_delay_min = base_delay_min
        self.base_delay_max = base_delay_max
        self.current_multiplier = 1.0
        self.latency_history = []

    def record_latency(self, latency_seconds):
        self.latency_history.append(latency_seconds)
        if len(self.latency_history) > 10:
            self.latency_history.pop(0)

        avg_latency = sum(self.latency_history) / max(len(self.latency_history), 1)

        # If latency is high, increase pacing multiplier
        if avg_latency > 4.0:
            self.current_multiplier = min(2.5, self.current_multiplier + 0.3)
            logger.warning("scraper", f"High latency detected ({round(avg_latency,2)}s). Increasing delay multiplier to {round(self.current_multiplier,2)}x")
        elif avg_latency < 2.0 and self.current_multiplier > 1.0:
            self.current_multiplier = max(1.0, self.current_multiplier - 0.1)

    def get_delay(self):
        min_d = self.base_delay_min * self.current_multiplier
        max_d = self.base_delay_max * self.current_multiplier
        return random.uniform(min_d, max_d)

    def trigger_captcha_backoff(self):
        """
        Triggers exponential backoff pause when captcha/bot cues are detected.
        """
        pause_sec = random.uniform(20.0, 45.0)
        logger.warning("scraper", f"[ANTI-DETECT] Captcha or slow response detected! Pausing scraper for {round(pause_sec,1)}s...")
        time.sleep(pause_sec)
