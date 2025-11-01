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
        Use Florence-2 to detect UI elements in screenshot.
        Returns: List of detected elements with bboxes and labels.
        
        IMPORTANT: This is EXPERIMENTAL and currently used as FALLBACK only.
        Primary detection still relies on DOM for reliability.
        """
        try:
            if not self.model_loaded:
                logger.info("🔄 [VISION] Florence-2 not loaded, attempting to load...")
                if not self.load_florence_model():
                    logger.warning("⚠️ [VISION] Failed to load Florence-2")
                    return []
            
            logger.info("🔍 [VISION] Starting Florence-2 visual detection...")
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"📷 Image size: {image.size}")
            
            # For UI detection, we use "<OD>" (Object Detection) prompt
            # Florence-2 supports various tasks:
            # - <OD>: General object detection
            # - <DENSE_REGION_CAPTION>: Detailed descriptions
            # - <CAPTION>: Image caption
            # - <OCR>: Text extraction
            prompt = "<OD>"
            
            # Preprocess image
            logger.info("🔄 Preprocessing image...")
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="np"
            )
            
            # Run vision encoder
            logger.info("🚀 Running Florence-2 vision encoder...")
            pixel_values = inputs["pixel_values"].astype(np.float32)
            vision_outputs = self.vision_session.run(
                None,
                {"pixel_values": pixel_values}
            )
            logger.info(f"✅ Vision encoder completed: {len(vision_outputs)} output tensors")
            
            # TODO: Full Florence-2 pipeline requires:
            # 1. Vision encoder (DONE)
            # 2. Decoder for bbox extraction (NOT YET IMPLEMENTED)
            # 3. Post-processing to convert to grid cells
            
            # For now, return empty as we don't have full pipeline
            # This will make system fall back to DOM elements (reliable)
            detections = []
            
            logger.info(f"🎯 [VISION] Florence-2 detected {len(detections)} objects (full pipeline pending)")
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
               rows: Optional[int] = None,
               cols: Optional[int] = None) -> List[Dict]:
        """
        Main vision detection function for 3-TIER ARCHITECTURE.
        
        ARCHITECTURE ROLE:
        - Called by: browser_automation_service._augment_with_vision()
        - Used by: Spinal Cord (supervisor_service) for decision-making
        - Output: vision[] array for grid-based automation
        
        STRATEGY (Cost-effective & Reliable):
        1. PRIMARY: DOM elements (fast, reliable, free)
        2. ENHANCEMENT: Florence-2 visual detection (experimental, when needed)
        3. MERGE: Combine results, prioritize DOM, add visual-only finds
        
        Returns: List of {cell, bbox, label, type, confidence, source}
        """
        try:
            logger.info(f"🔍 [VISION] detect() called: viewport={viewport_w}x{viewport_h}, DOM={len(dom_clickables or [])}")
            
            # Set grid configuration
            if rows and cols:
                self.set_grid(rows, cols)
                logger.info(f"🔍 [VISION] Grid configured: {rows}x{cols}")

            results: List[Dict] = []

            # ==============================================================
            # PHASE 1: DOM-BASED DETECTION (PRIMARY, ALWAYS ON)
            # ==============================================================
            if dom_clickables:
                logger.info(f"🔍 [VISION] Processing {len(dom_clickables)} DOM clickables...")
                for idx, el in enumerate(dom_clickables):
                    try:
                        bbox = el.get('bbox', {})
                        label = el.get('label') or el.get('text') or el.get('name') or el.get('type', '').upper()
                        etype = el.get('type') or 'button'
                        cell = self.grid.bbox_to_cell(bbox, viewport_w, viewport_h)
                        
                        results.append({
                            'cell': cell,
                            'bbox': bbox,
                            'label': label[:64],  # Cap label length
                            'type': etype,
                            'confidence': float(el.get('confidence', 0.90)),  # DOM is highly reliable
                            'source': 'dom'  # Mark source for debugging
                        })
                    except Exception as e:
                        logger.error(f"🔍 [VISION] Error processing DOM element {idx}: {e}")
                        continue
                
                logger.info(f"✅ [VISION] DOM detection: {len(results)} elements")
            else:
                logger.warning("⚠️ [VISION] No DOM clickables provided - will rely on visual only")
            
            # ==============================================================
            # PHASE 2: FLORENCE-2 VISUAL DETECTION (OPTIONAL, ENHANCEMENT)
            # ==============================================================
            # Enable this when:
            # - DOM elements have unclear labels (INPUT fields without placeholder)
            # - Need to find elements not in DOM (canvas, SVG, dynamically rendered)
            # - Verification mode (check if button actually visible)
            
            USE_FLORENCE_ENHANCEMENT = True  # Feature flag (enabled for visual element detection)
            
            if USE_FLORENCE_ENHANCEMENT and screenshot_base64:
                logger.info("🔍 [VISION] Running Florence-2 visual enhancement...")
                florence_results = self.detect_with_florence(
                    screenshot_base64,
                    viewport_w,
                    viewport_h
                )
                
                if florence_results:
                    logger.info(f"✅ [VISION] Florence-2 found {len(florence_results)} additional elements")
                    
                    # Merge: Add Florence-2 detections that DON'T overlap with DOM
                    existing_cells = {r['cell'] for r in results}
                    for f_result in florence_results:
                        if f_result['cell'] not in existing_cells:
                            f_result['source'] = 'florence2'
                            results.append(f_result)
                            logger.info(f"  + Added visual element: {f_result['label']} at {f_result['cell']}")
            
            # ==============================================================
            # PHASE 3: QUALITY CHECK & RETURN
            # ==============================================================
            # Remove duplicates by cell (keep highest confidence)
            seen_cells = {}
            unique_results = []
            for r in results:
                cell = r.get('cell')
                if not cell:
                    continue
                if cell not in seen_cells or r.get('confidence', 0) > seen_cells[cell].get('confidence', 0):
                    seen_cells[cell] = r
            
            unique_results = list(seen_cells.values())
            
            logger.info(f"✅ [VISION] Final output: {len(unique_results)} unique elements")
            return unique_results
            
        except Exception as e:
            logger.error(f"❌ [VISION] detect() FAILED: {e}")
            import traceback
            traceback.print_exc()
            return []

local_vision_service = LocalVisionService()
