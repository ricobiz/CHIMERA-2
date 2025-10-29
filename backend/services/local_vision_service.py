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
FLORENCE_VISION_ENCODER = os.path.join(FLORENCE_MODEL_DIR, "onnx/vision_encoder_q4.onnx")
FLORENCE_ENCODER = os.path.join(FLORENCE_MODEL_DIR, "onnx/encoder_model_q4.onnx")

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

    def detect_with_florence(self, 
                           screenshot_base64: str,
                           viewport_w: int,
                           viewport_h: int) -> List[Dict]:
        """
        Use Florence-2 to detect UI elements in screenshot
        Returns: List of detected elements with bboxes
        """
        try:
            if not self.model_loaded:
                logger.info("🔄 [VISION] Model not loaded, loading Florence-2...")
                if not self.load_florence_model():
                    logger.warning("⚠️ [VISION] Failed to load Florence-2, falling back to DOM")
                    return []
            
            logger.info("🔍 [VISION] Starting Florence-2 detection...")
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"📷 Image size: {image.size}")
            
            # For UI detection, we use "<OD>" (Object Detection) task
            prompt = "<OD>"
            
            # Preprocess image
            logger.info("🔄 Preprocessing image...")
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="np"
            )
            logger.info(f"✅ Preprocessed: {inputs.keys()}")
            
            # Run vision encoder
            logger.info("🚀 Running vision encoder...")
            pixel_values = inputs["pixel_values"].astype(np.float32)
            vision_outputs = self.vision_session.run(
                None,
                {"pixel_values": pixel_values}
            )
            logger.info(f"✅ Vision encoder output: {len(vision_outputs)} tensors")
            
            # Extract detected objects (simplified - real implementation needs decoder)
            # For now, return empty list as we need full pipeline
            # This is placeholder for object detection results
            detections = []
            
            logger.info(f"🎯 [VISION] Florence-2 detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"❌ [VISION] Florence-2 detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def detect(self,
               screenshot_base64: str,
               viewport_w: int,
               viewport_h: int,
               dom_clickables: Optional[List[Dict]] = None,
               model_path: Optional[str] = None,
               rows: Optional[int] = None,
               cols: Optional[int] = None) -> List[Dict]:
        """
        Returns list of {cell, bbox:{x,y,w,h}, label, type, confidence}
        
        Strategy:
        1. Try Florence-2 for visual detection (future)
        2. Fall back to DOM clickables (current reliable method)
        3. Merge results if both available
        """
        try:
            logger.info(f"🔍 [VISION] detect() called with {len(dom_clickables or [])} DOM clickables, viewport {viewport_w}x{viewport_h}")
            
            # Align grid to caller's config
            if rows and cols:
                self.set_grid(rows, cols)
                logger.info(f"🔍 [VISION] Grid set to {rows}x{cols}")

            results: List[Dict] = []

            # Strategy: For now, prioritize DOM clickables (reliable)
            # Florence-2 is loaded but not yet fully integrated for object detection
            # We'll add Florence-2 detection gradually
            
            # Try Florence-2 detection (experimental)
            if screenshot_base64 and False:  # Disabled for now until full pipeline
                florence_results = self.detect_with_florence(
                    screenshot_base64,
                    viewport_w,
                    viewport_h
                )
                if florence_results:
                    logger.info(f"✅ [VISION] Florence-2 detected {len(florence_results)} objects")
                    results.extend(florence_results)

            # Primary path: use dom_clickables (reliable)
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
                            'confidence': float(el.get('confidence', 0.75)),
                            'source': 'dom'  # Mark source
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
