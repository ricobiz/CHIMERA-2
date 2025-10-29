#!/usr/bin/env python3
"""
Test Florence-2 with a simple test image
"""
import sys
import logging
import base64
from PIL import Image, ImageDraw
import io

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_image():
    """Create a simple test image with buttons"""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "button"
    draw.rectangle([100, 100, 300, 150], fill='blue', outline='black', width=2)
    draw.text((150, 115), "Button", fill='white')
    
    # Draw another "button"
    draw.rectangle([400, 200, 600, 250], fill='green', outline='black', width=2)
    draw.text((450, 215), "Submit", fill='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_florence_detection():
    """Test Florence-2 detection on test image"""
    try:
        logger.info("=" * 60)
        logger.info("🧪 Testing Florence-2 Detection")
        logger.info("=" * 60)
        
        # Import the service
        logger.info("\n1️⃣ Importing LocalVisionService...")
        from services.local_vision_service import local_vision_service
        logger.info("✅ Import successful")
        
        # Create test image
        logger.info("\n2️⃣ Creating test image...")
        test_image_base64 = create_test_image()
        logger.info(f"✅ Test image created ({len(test_image_base64)} bytes base64)")
        
        # Test detection
        logger.info("\n3️⃣ Testing detection...")
        results = local_vision_service.detect(
            screenshot_base64=test_image_base64,
            viewport_w=800,
            viewport_h=600,
            dom_clickables=None,  # No DOM, pure vision
            rows=24,
            cols=16
        )
        
        logger.info(f"\n✅ Detection completed!")
        logger.info(f"📊 Results: {len(results)} elements detected")
        
        for idx, result in enumerate(results):
            logger.info(f"  {idx+1}. {result}")
        
        return True
            
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_florence_detection()
    sys.exit(0 if success else 1)
