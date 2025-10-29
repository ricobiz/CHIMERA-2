import os
import base64
from typing import List, Dict, Optional

# Optional ONNX runtime (if available)
try:
    import onnxruntime as ort  # type: ignore
except Exception:  # pragma: no cover
    ort = None

from .grid_service import GridConfig

MODEL_PATH = "/app/backend/models/ui-detector.onnx"

# Simple lazy downloader for a tiny onnx model (placeholder URL)
MODEL_URL = os.environ.get(
    "UI_DETECTOR_MODEL_URL",
    "https://huggingface.co/onnx/models/resolve/main/tiny_detectors/ui-detector.onnx"
)

def ensure_model():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        try:
            import httpx
            r = httpx.get(MODEL_URL, timeout=20.0)
            if r.status_code == 200 and r.content:
                with open(MODEL_PATH, 'wb') as f:
                    f.write(r.content)
        except Exception:
            # If download fails, we'll continue with DOM fallback only
            pass

ensure_model()

class LocalVisionService:
    """
    Local visual detector (Eyes):
      - Primary path: ONNX model (if present)
      - Fallback path: DOM-derived clickable elements passed in
    It maps detections to grid cells.
    """
    def __init__(self):
        self.grid = GridConfig(rows=12, cols=8)
        self.session = None

    def maybe_load_model(self, model_path: Optional[str]) -> None:
        if model_path and ort and self.session is None and os.path.exists(model_path):
            try:
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])  # noqa: E501
            except Exception:
                self.session = None

    def set_grid(self, rows: int, cols: int) -> None:
        self.grid = GridConfig(rows=rows, cols=cols)

    def detect(self,
               screenshot_base64: str,
               viewport_w: int,
               viewport_h: int,
               dom_clickables: Optional[List[Dict]] = None,
               model_path: Optional[str] = MODEL_PATH,
               rows: Optional[int] = None,
               cols: Optional[int] = None) -> List[Dict]:
        """
        Returns list of {cell, bbox:{x,y,w,h}, label, type, confidence}
        """
        logger.info(f"🔍 [VISION] detect() called with {len(dom_clickables or [])} DOM clickables, viewport {viewport_w}x{viewport_h}")
        
        # Align grid to caller's config
        if rows and cols:
            self.set_grid(rows, cols)
        # Try model if available (placeholder – not producing detections yet)
        if model_path:
            self.maybe_load_model(model_path)
        # If session exists, you can add real model inference here later

        results: List[Dict] = []

        # Fallback: use dom_clickables if provided
        if dom_clickables:
            logger.info(f"🔍 [VISION] Processing {len(dom_clickables)} DOM clickables...")
            for el in dom_clickables:
                bbox = el.get('bbox', {})
                label = el.get('label') or el.get('text') or el.get('name') or ''
                etype = el.get('type') or 'button'
                cell = self.grid.bbox_to_cell(bbox, viewport_w, viewport_h)
                results.append({
                    'cell': cell,
                    'bbox': bbox,
                    'label': label[:64],
                    'type': etype,
                    'confidence': float(el.get('confidence', 0.75))
                })
            logger.info(f"🔍 [VISION] Returning {len(results)} results")
        else:
            logger.warning("🔍 [VISION] No DOM clickables provided!")

        return results

local_vision_service = LocalVisionService()
