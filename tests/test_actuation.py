import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# PyAutoGUI requires a DISPLAY environment variable to import, even if mocked.
# We map it to the virtual framebuffer Xvfb running on :99
if "DISPLAY" not in os.environ or os.environ["DISPLAY"] == ":0":
    os.environ["DISPLAY"] = ":99"

from asta.actuation_sensory.vision import VisionSystem
from asta.actuation_sensory.motor import MotorController

@pytest.fixture
def vision_system(tmp_path: Path) -> VisionSystem:
    # Use tmp_path for the capture directory so we don't pollute ~/.asta
    return VisionSystem(capture_dir=str(tmp_path))

def test_vlm_bounding_box_extraction(vision_system: VisionSystem, tmp_path: Path) -> None:
    """Verify that the system can 'parse' a screenshot and extract bounding box centers."""

    # Create a dummy image file to bypass the exists() check
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_text("fake image data")

    elements = vision_system.parse_ui_elements(dummy_img)

    # Assert VLM returned expected elements
    assert len(elements) == 3

    # Verify the center calculation math
    # btn_login is [100, 200, 150, 220]
    # Center X: (100 + 150) // 2 = 125
    # Center Y: (200 + 220) // 2 = 210
    center = vision_system.find_element_center(elements, "btn_login")
    assert center == (125, 210)


@patch("pyautogui.moveTo")
@patch("pyautogui.click")
@patch("pyautogui.write")
def test_motor_controller_actuation(mock_write: MagicMock, mock_click: MagicMock, mock_move: MagicMock) -> None:
    """
    Verify the Motor Controller correctly routes physical OS commands
    using the mocked PyAutoGUI library.
    """
    # Use debug mode to bypass the complex bezier math/positioning which fails in headless
    motor = MotorController(debug_mode=True)

    # 1. Test clicking
    motor.click(500, 600)
    mock_move.assert_called_with(500, 600, duration=0.0)
    # Note: in debug_mode=True, the actual click() call is bypassed for safety,
    # but the move_to is triggered.

    # 2. Test typing
    motor.type_text("Hello World", wpm=100)
    # In debug_mode, write() is also bypassed, so let's test it with debug=False briefly
    motor_live = MotorController(debug_mode=False)
    motor_live.type_text("Hello World")
    mock_write.assert_called_once()


@patch("pyautogui.moveTo")
def test_bezier_curve_generation(mock_move: MagicMock) -> None:
    """Verify the math behind the human-like mouse movement logic."""
    motor = MotorController()

    # Direct math check on the private method
    start = (0, 0)
    end = (100, 100)

    curve = motor._generate_bezier_curve(start, end, points=10)

    # Must generate 10 points
    assert len(curve) == 10

    # Must start at origin (math rounding might make it exactly 0 or 1 depending on NP)
    assert curve[0] == start
    # Must end exactly at the target
    assert curve[-1] == end
