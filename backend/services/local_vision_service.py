import os
import base64
import logging
import io
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Optional ONNX runtime (if available)
try:
    import onnxruntime as ort  # type: ignore
    from PIL import Image
    from transformers import AutoProcessor
except Exception as e:
    logger.warning(f"⚠️ ONNX/PIL/Transformers not available: {e}")
    ort = None
    Image = None
    AutoProcessor = None

from .grid_service import GridConfig

# Florence-2 model path
FLORENCE_MODEL_DIR = "/app/backend/onnx_models/florence-2-base"
FLORENCE_VISION_ENCODER = os.path.join(FLORENCE_MODEL_DIR, "onnx/vision_encoder_q4f16.onnx")
FLORENCE_ENCODER = os.path.join(FLORENCE_MODEL_DIR, "onnx/encoder_model_q4f16.onnx")

logger.info(f"🔧 [VISION] Florence-2 paths configured:")
logger.info(f"  Vision Encoder: {FLORENCE_VISION_ENCODER}")
logger.info(f"  Encoder: {FLORENCE_ENCODER}")

class LocalVisionService:
    """
    Local visual detector (Eyes) using Florence-2:
      - Primary path: Florence-2 ONNX model for visual understanding
      - Fallback path: DOM-derived clickable elements passed in
    It maps detections to grid cells.
    """
    def __init__(self):
        self.grid = GridConfig(rows=12, cols=8)
        self.vision_session = None
        self.encoder_session = None
        self.processor = None
        self.model_loaded = False
        logger.info("🧠 [VISION] LocalVisionService initialized")

    def load_florence_model(self) -> bool:
        """Load Florence-2 ONNX models"""
        if self.model_loaded:
            return True
            
        if not ort or not Image or not AutoProcessor:
            logger.warning("⚠️ [VISION] Missing dependencies (onnxruntime/PIL/transformers)")
            return False
            
        try:
            logger.info("📥 [VISION] Loading Florence-2 models...")
            
            # Check if files exist
            if not os.path.exists(FLORENCE_VISION_ENCODER):
                logger.error(f"❌ [VISION] Vision encoder not found: {FLORENCE_VISION_ENCODER}")
                return False
            
            # Load vision encoder
            logger.info(f"Loading vision encoder: {FLORENCE_VISION_ENCODER}")
            self.vision_session = ort.InferenceSession(
                FLORENCE_VISION_ENCODER,
                providers=["CPUExecutionProvider"]
            )
            logger.info(f"✅ Vision encoder loaded: {len(self.vision_session.get_inputs())} inputs")
            
            # Load processor for image preprocessing
            logger.info(f"Loading processor from: {FLORENCE_MODEL_DIR}")
            self.processor = AutoProcessor.from_pretrained(
                FLORENCE_MODEL_DIR,
                trust_remote_code=True
            )
            logger.info("✅ Processor loaded")
            
            self.model_loaded = True
            logger.info("✅ [VISION] Florence-2 models loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ [VISION] Failed to load Florence-2 models: {e}")
            import traceback
            traceback.print_exc()
            self.model_loaded = False
            return False

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
        try:
            logger.info(f"🔍 [VISION] detect() called with {len(dom_clickables or [])} DOM clickables, viewport {viewport_w}x{viewport_h}")
            
            # Align grid to caller's config
            if rows and cols:
                self.set_grid(rows, cols)
                logger.info(f"🔍 [VISION] Grid set to {rows}x{cols}")
            # Try model if available (placeholder – not producing detections yet)
            if model_path:
                self.maybe_load_model(model_path)
            # If session exists, you can add real model inference here later

            results: List[Dict] = []

            # Fallback: use dom_clickables if provided
            if dom_clickables:
                logger.info(f"🔍 [VISION] Processing {len(dom_clickables)} DOM clickables...")
                for idx, el in enumerate(dom_clickables):
                    try:
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
                    except Exception as e:
                        logger.error(f"🔍 [VISION] Error processing element {idx}: {e}")
                        continue
                logger.info(f"🔍 [VISION] Returning {len(results)} results")
            else:
                logger.warning("🔍 [VISION] No DOM clickables provided!")

            return results
        except Exception as e:
            logger.error(f"🔍 [VISION] detect() FAILED: {e}")
            import traceback
            traceback.print_exc()
            return []

local_vision_service = LocalVisionService()
