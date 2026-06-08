import pyautogui
import numpy as np
import time
from loguru import logger
import math
from typing import Tuple, List

# PyAutoGUI safety setting: moving mouse to corner aborts program
pyautogui.FAILSAFE = True


class MotorController:
    """Handles physical OS-level keyboard and mouse actuation."""

    def __init__(self, debug_mode: bool = False) -> None:
        self.debug_mode = debug_mode

    def _generate_bezier_curve(self, start: Tuple[int, int], end: Tuple[int, int], points: int = 15) -> List[Tuple[int, int]]:
        """
        Generates a random human-like bezier curve path between two points
        to bypass simple anti-bot mechanisms.
        """
        x1, y1 = start
        x2, y2 = end

        # Calculate distance
        dist = math.hypot(x2 - x1, y2 - y1)

        # Determine control point offsets based on distance
        deviation = min(int(dist * 0.3), 50)

        # If the points are extremely close together, avoid np.random.randint throwing ValueError(low>=high)
        if deviation <= 0:
            rand_offset_x1, rand_offset_y1 = 0, 0
            rand_offset_x2, rand_offset_y2 = 0, 0
        else:
            rand_offset_x1 = np.random.randint(-deviation, deviation)
            rand_offset_y1 = np.random.randint(-deviation, deviation)
            rand_offset_x2 = np.random.randint(-deviation, deviation)
            rand_offset_y2 = np.random.randint(-deviation, deviation)

        # Control point 1 (slightly randomized)
        cp1_x = x1 + (x2 - x1) * 0.3 + rand_offset_x1
        cp1_y = y1 + (y2 - y1) * 0.3 + rand_offset_y1

        # Control point 2 (slightly randomized)
        cp2_x = x1 + (x2 - x1) * 0.7 + rand_offset_x2
        cp2_y = y1 + (y2 - y1) * 0.7 + rand_offset_y2

        curve_points = []
        for t in np.linspace(0, 1, points):
            # Cubic Bezier Formula
            bx = int((1-t)**3 * x1 + 3*(1-t)**2 * t * cp1_x + 3*(1-t) * t**2 * cp2_x + t**3 * x2)
            by = int((1-t)**3 * y1 + 3*(1-t)**2 * t * cp1_y + 3*(1-t) * t**2 * cp2_y + t**3 * y2)
            curve_points.append((bx, by))

        return curve_points

    def move_to(self, target_x: int, target_y: int, human_like: bool = True) -> None:
        """Move the mouse to a specific screen coordinate."""
        try:
            current_x, current_y = pyautogui.position()
        except Exception:
            # If running in headless test env, pyautogui.position() might fail
            current_x, current_y = (0, 0)

        logger.debug(f"Moving mouse from ({current_x}, {current_y}) to ({target_x}, {target_y})")

        if human_like and not self.debug_mode:
            path = self._generate_bezier_curve((current_x, current_y), (target_x, target_y))
            for point in path:
                # Move fast but smoothly along the curve
                pyautogui.moveTo(point[0], point[1], duration=0.01)

            # Final precision snap
            pyautogui.moveTo(target_x, target_y, duration=0.1)
        else:
            # Linear, instant movement (best for headless/debug)
            pyautogui.moveTo(target_x, target_y, duration=0.0 if self.debug_mode else 0.5)

    def click(self, target_x: int, target_y: int) -> None:
        """Moves to the target and executes a physical hardware-level click."""
        self.move_to(target_x, target_y)
        logger.debug(f"Clicking at ({target_x}, {target_y})")
        if not self.debug_mode:
            pyautogui.click()
            time.sleep(np.random.uniform(0.1, 0.3)) # Human pause after click

    def type_text(self, text: str, wpm: int = 80) -> None:
        """Types text organically using host OS keyboard commands."""
        # Calculate delay per keystroke based on target Words Per Minute (WPM)
        # Average word is 5 characters
        cpm = wpm * 5
        delay = 60.0 / cpm if cpm > 0 else 0.1

        logger.debug(f"Typing text: '{text}' at ~{wpm} WPM")
        if not self.debug_mode:
            pyautogui.write(text, interval=delay)
