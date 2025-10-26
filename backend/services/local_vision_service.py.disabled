"""
Local Vision Service for Browser Automation
Uses Hugging Face models for element detection on screenshots
NO API calls - fully local and FREE
"""
import logging
import base64
import io
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq, AutoModel, AutoTokenizer
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class LocalVisionService:
    """
    Local vision model service using Hugging Face models
    Models supported:
    - Florence-2 (Microsoft) - Best for UI element detection
    - BLIP-2 (Salesforce) - Good for image captioning and VQA
    - OWL-ViT (Google) - Zero-shot object detection
    """
    
    def __init__(self, model_name: str = "microsoft/Florence-2-base"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.loaded = False
        
        logger.info(f"Initializing Local Vision Service with {model_name}")
        logger.info(f"Device: {self.device}")
    
    async def load_model(self):
        """Load model from Hugging Face (downloads on first run, then cached)"""
        if self.loaded:
            return
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            if "florence" in self.model_name.lower():
                # Florence-2 is best for UI/document understanding
                self.processor = AutoProcessor.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True
                )
                self.model = AutoModelForVision2Seq.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
                
            elif "blip" in self.model_name.lower():
                # BLIP-2 for visual question answering
                from transformers import Blip2Processor, Blip2ForConditionalGeneration
                self.processor = Blip2Processor.from_pretrained(self.model_name)
                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
            
            else:
                # Generic vision model
                self.processor = AutoProcessor.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            
            self.loaded = True
            logger.info(f"✓ Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def _decode_screenshot(self, screenshot: str) -> Image.Image:
        """Convert base64 screenshot to PIL Image"""
        try:
            # Remove data URL prefix if present
            if screenshot.startswith("data:image"):
                screenshot = screenshot.split(",")[1]
            
            # Decode base64
            image_bytes = base64.b64decode(screenshot)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Error decoding screenshot: {str(e)}")
            raise
    
    async def find_element(
        self, 
        screenshot: str, 
        description: str,
        return_multiple: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find UI element on screenshot using natural language description
        
        Args:
            screenshot: Base64 encoded PNG image
            description: Natural language description (e.g., "login button", "email input field")
            return_multiple: If True, return all matching elements
        
        Returns:
            List of elements with bounding boxes and confidence scores
        """
        await self.load_model()
        
        try:
            image = self._decode_screenshot(screenshot)
            
            if "florence" in self.model_name.lower():
                return await self._find_with_florence(image, description, return_multiple)
            elif "blip" in self.model_name.lower():
                return await self._find_with_blip(image, description)
            else:
                return await self._find_generic(image, description)
                
        except Exception as e:
            logger.error(f"Error finding element: {str(e)}")
            return []
    
    async def _find_with_florence(
        self, 
        image: Image.Image, 
        description: str,
        return_multiple: bool
    ) -> List[Dict[str, Any]]:
        """Use Florence-2 for object detection with natural language"""
        try:
            # Florence-2 supports grounding tasks
            prompt = f"<OD>{description}</OD>"
            
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    num_beams=3
                )
            
            # Decode results
            decoded = self.processor.batch_decode(outputs, skip_special_tokens=False)[0]
            
            # Parse bounding boxes from Florence-2 output
            elements = self._parse_florence_output(decoded, image.size)
            
            logger.info(f"Florence-2 found {len(elements)} elements for '{description}'")
            
            return elements[:5] if return_multiple else elements[:1]
            
        except Exception as e:
            logger.error(f"Florence-2 error: {str(e)}")
            return []
    
    def _parse_florence_output(self, output: str, image_size: Tuple[int, int]) -> List[Dict]:
        """Parse Florence-2 output to extract bounding boxes"""
        # Florence-2 returns format: <loc_x1><loc_y1><loc_x2><loc_y2>text</loc>
        import re
        
        elements = []
        width, height = image_size
        
        # Extract location tokens
        pattern = r'<loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)>([^<]*)'
        matches = re.findall(pattern, output)
        
        for match in matches:
            x1, y1, x2, y2, text = match
            
            # Florence uses normalized coordinates (0-1000)
            x1 = int(x1) * width / 1000
            y1 = int(y1) * height / 1000
            x2 = int(x2) * width / 1000
            y2 = int(y2) * height / 1000
            
            elements.append({
                'box': {
                    'x': int(x1),
                    'y': int(y1),
                    'width': int(x2 - x1),
                    'height': int(y2 - y1)
                },
                'text': text.strip(),
                'confidence': 0.9,  # Florence is very accurate
                'type': 'ui_element'
            })
        
        return elements
    
    async def _find_with_blip(self, image: Image.Image, description: str) -> List[Dict]:
        """Use BLIP-2 for visual question answering"""
        try:
            # Ask question about element location
            question = f"Where is the {description} located on this screen?"
            
            inputs = self.processor(
                images=image,
                text=question,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=100)
            
            answer = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            logger.info(f"BLIP-2 answer for '{description}': {answer}")
            
            # BLIP-2 gives text description, not bounding boxes
            # Would need additional model for bbox extraction
            return [{
                'box': {'x': 0, 'y': 0, 'width': 100, 'height': 50},
                'text': answer,
                'confidence': 0.7,
                'type': 'text_description'
            }]
            
        except Exception as e:
            logger.error(f"BLIP-2 error: {str(e)}")
            return []
    
    async def _find_generic(self, image: Image.Image, description: str) -> List[Dict]:
        """Generic fallback method"""
        logger.warning("Using generic fallback - limited accuracy")
        return []
    
    async def detect_all_interactive_elements(self, screenshot: str) -> List[Dict[str, Any]]:
        """
        Detect all interactive UI elements (buttons, inputs, links)
        Returns comprehensive list with types and locations
        """
        await self.load_model()
        
        try:
            image = self._decode_screenshot(screenshot)
            
            # Detect multiple element types
            element_types = [
                "button",
                "input field",
                "link", 
                "checkbox",
                "radio button",
                "dropdown menu"
            ]
            
            all_elements = []
            
            for elem_type in element_types:
                elements = await self.find_element(
                    screenshot,
                    elem_type,
                    return_multiple=True
                )
                for elem in elements:
                    elem['element_type'] = elem_type
                    all_elements.append(elem)
            
            logger.info(f"Detected {len(all_elements)} interactive elements total")
            
            return all_elements
            
        except Exception as e:
            logger.error(f"Error detecting elements: {str(e)}")
            return []
    
    async def extract_text_from_region(
        self, 
        screenshot: str,
        box: Dict[str, int]
    ) -> str:
        """
        Extract text from specific region using OCR
        """
        await self.load_model()
        
        try:
            image = self._decode_screenshot(screenshot)
            
            # Crop to region
            region = image.crop((
                box['x'],
                box['y'],
                box['x'] + box['width'],
                box['y'] + box['height']
            ))
            
            if "florence" in self.model_name.lower():
                # Florence-2 has built-in OCR
                prompt = "<OCR>"
                inputs = self.processor(
                    text=prompt,
                    images=region,
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model.generate(**inputs, max_new_tokens=512)
                
                text = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
                return text.strip()
            
            else:
                # Fallback: use image captioning
                inputs = self.processor(images=region, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self.model.generate(**inputs)
                text = self.processor.decode(outputs[0], skip_special_tokens=True)
                return text
                
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
    
    async def compare_screenshots(
        self,
        before: str,
        after: str
    ) -> Dict[str, Any]:
        """
        Compare two screenshots to detect changes
        Useful for validation after actions
        """
        try:
            image_before = self._decode_screenshot(before)
            image_after = self._decode_screenshot(after)
            
            # Convert to numpy arrays
            arr_before = np.array(image_before)
            arr_after = np.array(image_after)
            
            # Calculate pixel difference
            diff = np.abs(arr_before.astype(float) - arr_after.astype(float))
            total_diff = np.sum(diff)
            max_diff = arr_before.size * 255 * 3  # Max possible difference
            
            change_percentage = (total_diff / max_diff) * 100
            
            # Detect regions with significant changes
            diff_gray = np.mean(diff, axis=2)
            threshold = 30
            changed_mask = diff_gray > threshold
            
            # Find bounding boxes of changed regions
            from scipy import ndimage
            labeled, num_features = ndimage.label(changed_mask)
            
            changed_regions = []
            for i in range(1, num_features + 1):
                coords = np.argwhere(labeled == i)
                if len(coords) > 100:  # Minimum size filter
                    y_min, x_min = coords.min(axis=0)
                    y_max, x_max = coords.max(axis=0)
                    
                    changed_regions.append({
                        'box': {
                            'x': int(x_min),
                            'y': int(y_min),
                            'width': int(x_max - x_min),
                            'height': int(y_max - y_min)
                        },
                        'change_type': 'visual_change'
                    })
            
            return {
                'has_changes': change_percentage > 1.0,  # 1% threshold
                'change_percentage': float(change_percentage),
                'changed_regions': changed_regions
            }
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {str(e)}")
            return {
                'has_changes': False,
                'change_percentage': 0,
                'changed_regions': []
            }
    
    def cleanup(self):
        """Free up GPU memory"""
        if self.model:
            del self.model
            del self.processor
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.loaded = False
            logger.info("Vision model cleaned up")


# Global instance
vision_service = LocalVisionService(model_name="microsoft/Florence-2-base")
