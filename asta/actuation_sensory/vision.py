import mss
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger


class VisionSystem:
    """Handles OS-level screenshots and Visual Language Model (VLM) extraction."""

    def __init__(self, capture_dir: str = "~/.asta/vision_logs") -> None:
        self.capture_dir = Path(capture_dir).expanduser()
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        self.sct = mss.mss()

    def capture_screen(self, filename: str = "current_screen.png") -> Path:
        """Takes a screenshot of the primary monitor and saves it to disk."""
        filepath = self.capture_dir / filename

        # Grab the first monitor
        monitor = self.sct.monitors[1]

        # Grab the data
        sct_img = self.sct.grab(monitor)

        # Save to the picture file
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(filepath))

        logger.debug(f"Screen captured and saved to {filepath}")
        return filepath

    def parse_ui_elements(self, image_path: Path) -> List[Dict[str, Any]]:
        """
        Simulates parsing an image with a VLM (like LLaVA or Qwen-VL) to extract
        semantic bounding boxes.

        In a full implementation, this calls the local VLM. Here, we mock the
        extraction to demonstrate the architecture contract.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Cannot parse: {image_path} does not exist.")

        logger.info(f"VLM analyzing UI elements for {image_path.name}...")

        # Mocked VLM Response returning bounding boxes (x_min, y_min, x_max, y_max)
        mocked_elements = [
            {"id": "btn_login", "type": "button", "name": "Login", "bbox": [100, 200, 150, 220]},
            {"id": "inp_username", "type": "input", "name": "Username Field", "bbox": [100, 150, 300, 170]},
            {"id": "btn_submit", "type": "button", "name": "Submit", "bbox": [150, 400, 200, 430]}
        ]

        return mocked_elements

    def find_element_center(self, elements: List[Dict[str, Any]], target_id: str) -> Optional[tuple[int, int]]:
        """Calculates the center (x, y) coordinate of a target bounding box."""
        for el in elements:
            if el["id"] == target_id:
                x_min, y_min, x_max, y_max = el["bbox"]
                center_x = (x_min + x_max) // 2
                center_y = (y_min + y_max) // 2
                return (center_x, center_y)

        logger.warning(f"Element '{target_id}' not found in visual context.")
        return None
