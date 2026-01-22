"""
Human Behavior Simulator for X-Hive
Makes automation look like natural human interaction.

Features:
- Random delays between actions (2-8 seconds)
- Realistic typing speed (50-120 WPM)
- Mouse movement simulation
- Random scrolling
- Reading pauses
- Activity reduction on weekends/nights
"""

import asyncio
import random
import logging
from datetime import datetime
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class HumanBehavior:
    """
    Simulates human-like behavior to avoid bot detection.
    
    All delays are randomized to mimic natural human patterns.
    """
    
    # Typing speed range (WPM = words per minute)
    MIN_WPM = 50
    MAX_WPM = 120
    
    # Action delays (seconds)
    MIN_ACTION_DELAY = 2.0
    MAX_ACTION_DELAY = 8.0
    
    # Reading pause (seconds per 100 characters)
    MIN_READING_TIME_PER_100_CHARS = 3.0
    MAX_READING_TIME_PER_100_CHARS = 7.0
    
    # Mouse movement
    MOUSE_MOVE_STEPS = random.randint(5, 15)
    
    # Activity reduction multipliers
    WEEKEND_DELAY_MULTIPLIER = 1.5  # Slower on weekends
    NIGHT_DELAY_MULTIPLIER = 2.0    # Much slower at night (11pm-7am)
    
    @staticmethod
    def is_weekend() -> bool:
        """Check if today is weekend"""
        return datetime.now().weekday() >= 5  # Saturday=5, Sunday=6
    
    @staticmethod
    def is_night() -> bool:
        """Check if current time is night (11pm-7am)"""
        hour = datetime.now().hour
        return hour >= 23 or hour < 7
    
    @staticmethod
    def get_time_multiplier() -> float:
        """Get delay multiplier based on time of day/week"""
        multiplier = 1.0
        
        if HumanBehavior.is_weekend():
            multiplier *= HumanBehavior.WEEKEND_DELAY_MULTIPLIER
            logger.debug("🏖️ Weekend mode: slower activity")
        
        if HumanBehavior.is_night():
            multiplier *= HumanBehavior.NIGHT_DELAY_MULTIPLIER
            logger.debug("🌙 Night mode: much slower activity")
        
        return multiplier
    
    @staticmethod
    async def random_delay(
        min_seconds: Optional[float] = None,
        max_seconds: Optional[float] = None
    ) -> None:
        """
        Random delay with time-of-day consideration.
        
        Args:
            min_seconds: Minimum delay (default: 2s)
            max_seconds: Maximum delay (default: 8s)
        """
        min_s = min_seconds or HumanBehavior.MIN_ACTION_DELAY
        max_s = max_seconds or HumanBehavior.MAX_ACTION_DELAY
        
        base_delay = random.uniform(min_s, max_s)
        multiplier = HumanBehavior.get_time_multiplier()
        final_delay = base_delay * multiplier
        
        logger.debug(f"⏱️ Random delay: {final_delay:.2f}s (base: {base_delay:.2f}s, multiplier: {multiplier}x)")
        await asyncio.sleep(final_delay)
    
    @staticmethod
    async def typing_delay(text: str) -> None:
        """
        Simulate realistic typing delay based on text length.
        
        Args:
            text: Text being typed
        """
        # Calculate delay based on random WPM
        wpm = random.randint(HumanBehavior.MIN_WPM, HumanBehavior.MAX_WPM)
        chars_per_second = (wpm * 5) / 60  # Average 5 chars per word
        
        delay_per_char = 1.0 / chars_per_second
        total_delay = len(text) * delay_per_char
        
        # Add random variations (some characters take longer)
        variation = random.uniform(0.9, 1.3)
        final_delay = total_delay * variation
        
        logger.debug(f"⌨️ Typing delay: {final_delay:.2f}s for {len(text)} chars ({wpm} WPM)")
        await asyncio.sleep(final_delay)
    
    @staticmethod
    async def reading_delay(text: str) -> None:
        """
        Simulate reading delay based on text length.
        
        Args:
            text: Text being read
        """
        char_count = len(text)
        chunks = char_count / 100.0  # Per 100 characters
        
        time_per_chunk = random.uniform(
            HumanBehavior.MIN_READING_TIME_PER_100_CHARS,
            HumanBehavior.MAX_READING_TIME_PER_100_CHARS
        )
        
        total_delay = chunks * time_per_chunk
        multiplier = HumanBehavior.get_time_multiplier()
        final_delay = total_delay * multiplier
        
        logger.debug(f"📖 Reading delay: {final_delay:.2f}s for {char_count} chars")
        await asyncio.sleep(final_delay)
    
    @staticmethod
    async def move_mouse_randomly(page: Page) -> None:
        """
        Simulate random mouse movement.
        
        Args:
            page: Playwright page instance
        """
        try:
            # Get viewport size
            viewport = page.viewport_size
            if not viewport:
                logger.warning("No viewport size available for mouse movement")
                return
            
            width = viewport["width"]
            height = viewport["height"]
            
            # Random destination
            target_x = random.randint(100, width - 100)
            target_y = random.randint(100, height - 100)
            
            # Move in steps (more human-like)
            steps = random.randint(5, 15)
            
            for i in range(steps):
                intermediate_x = target_x * (i + 1) / steps
                intermediate_y = target_y * (i + 1) / steps
                
                await page.mouse.move(intermediate_x, intermediate_y)
                await asyncio.sleep(random.uniform(0.01, 0.05))
            
            logger.debug(f"🖱️ Mouse moved to ({target_x}, {target_y}) in {steps} steps")
        
        except Exception as e:
            logger.warning(f"Mouse movement failed: {e}")
    
    @staticmethod
    async def random_scroll(page: Page) -> None:
        """
        Simulate random scrolling behavior.
        
        Args:
            page: Playwright page instance
        """
        try:
            # Random scroll amount (positive = down, negative = up)
            scroll_amount = random.randint(-300, 800)
            
            # Scroll in steps
            steps = random.randint(3, 8)
            step_amount = scroll_amount / steps
            
            for _ in range(steps):
                await page.evaluate(f"window.scrollBy(0, {step_amount})")
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            logger.debug(f"📜 Scrolled {scroll_amount}px in {steps} steps")
        
        except Exception as e:
            logger.warning(f"Random scroll failed: {e}")
    
    @staticmethod
    async def simulate_thinking() -> None:
        """
        Simulate "thinking" pause before action.
        Used before clicking buttons or submitting forms.
        """
        thinking_time = random.uniform(1.0, 4.0)
        multiplier = HumanBehavior.get_time_multiplier()
        final_delay = thinking_time * multiplier
        
        logger.debug(f"🤔 Thinking pause: {final_delay:.2f}s")
        await asyncio.sleep(final_delay)
    
    @staticmethod
    async def simulate_page_load_wait() -> None:
        """
        Wait for page to "load" as a human would.
        Used after navigation.
        """
        load_wait = random.uniform(1.5, 3.5)
        logger.debug(f"⏳ Page load wait: {load_wait:.2f}s")
        await asyncio.sleep(load_wait)
    
    @staticmethod
    async def random_micro_pause() -> None:
        """
        Very short pause (human hesitation).
        Used between small actions like moving focus.
        """
        pause = random.uniform(0.3, 1.0)
        logger.debug(f"⏸️ Micro pause: {pause:.2f}s")
        await asyncio.sleep(pause)
    
    @staticmethod
    async def type_like_human(page: Page, selector: str, text: str) -> None:
        """
        Type text with human-like speed and pauses.
        
        Args:
            page: Playwright page instance
            selector: Element selector
            text: Text to type
        """
        element = page.locator(selector)
        await element.click()
        await HumanBehavior.random_micro_pause()
        
        # Type with realistic speed
        wpm = random.randint(HumanBehavior.MIN_WPM, HumanBehavior.MAX_WPM)
        chars_per_second = (wpm * 5) / 60
        delay_ms = int((1000 / chars_per_second) * random.uniform(0.8, 1.2))
        
        await element.type(text, delay=delay_ms)
        logger.debug(f"⌨️ Typed {len(text)} chars at ~{wpm} WPM")
    
    @staticmethod
    def should_perform_random_action() -> bool:
        """
        Randomly decide whether to perform additional human-like action.
        Returns True ~30% of the time.
        """
        return random.random() < 0.3
    
    @staticmethod
    async def perform_random_human_action(page: Page) -> None:
        """
        Perform a random human-like action (scroll, mouse move, etc.).
        
        Args:
            page: Playwright page instance
        """
        if not HumanBehavior.should_perform_random_action():
            return
        
        action = random.choice(["scroll", "mouse_move", "pause"])
        
        if action == "scroll":
            await HumanBehavior.random_scroll(page)
        elif action == "mouse_move":
            await HumanBehavior.move_mouse_randomly(page)
        elif action == "pause":
            await HumanBehavior.simulate_thinking()
        
        logger.debug(f"🎭 Random human action: {action}")
    
    @staticmethod
    async def anti_detection_delay() -> None:
        """
        Special delay for anti-detection.
        Longer than normal delays, used after critical operations.
        """
        delay = random.uniform(5.0, 12.0)
        multiplier = HumanBehavior.get_time_multiplier()
        final_delay = delay * multiplier
        
        logger.info(f"🛡️ Anti-detection delay: {final_delay:.2f}s")
        await asyncio.sleep(final_delay)
    
    @staticmethod
    def get_random_user_agent() -> str:
        """
        Get a random realistic User-Agent string.
        Returns modern Chrome on Windows/Mac.
        """
        agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]
        return random.choice(agents)
    
    @staticmethod
    def get_random_viewport() -> dict:
        """
        Get random realistic viewport size.
        Returns common desktop resolutions.
        """
        viewports = [
            {"width": 1920, "height": 1080},  # Full HD
            {"width": 1366, "height": 768},   # Common laptop
            {"width": 1536, "height": 864},   # Scaled 1080p
            {"width": 1440, "height": 900},   # MacBook Pro
            {"width": 1280, "height": 720},   # HD
        ]
        return random.choice(viewports)


# Convenience aliases
delay = HumanBehavior.random_delay
thinking = HumanBehavior.simulate_thinking
typing_delay = HumanBehavior.typing_delay
reading_delay = HumanBehavior.reading_delay
type_like_human = HumanBehavior.type_like_human
anti_detection_delay = HumanBehavior.anti_detection_delay
