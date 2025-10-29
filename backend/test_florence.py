#!/usr/bin/env python3
"""
Test script to verify Florence-2 model loading
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_florence_loading():
    """Test Florence-2 model loading"""
    try:
        logger.info("=" * 60)
        logger.info("🧪 Testing Florence-2 Model Loading")
        logger.info("=" * 60)
        
        # Import the service
        logger.info("\n1️⃣ Importing LocalVisionService...")
        from services.local_vision_service import local_vision_service
        logger.info("✅ Import successful")
        
        # Try to load the model
        logger.info("\n2️⃣ Loading Florence-2 models...")
        success = local_vision_service.load_florence_model()
        
        if success:
            logger.info("\n✅ ✅ ✅ Florence-2 models loaded successfully! ✅ ✅ ✅")
            
            # Check loaded components
            logger.info("\n📊 Model Status:")
            logger.info(f"  - Vision Session: {'✅ Loaded' if local_vision_service.vision_session else '❌ Not loaded'}")
            logger.info(f"  - Processor: {'✅ Loaded' if local_vision_service.processor else '❌ Not loaded'}")
            logger.info(f"  - Model Loaded Flag: {local_vision_service.model_loaded}")
            
            if local_vision_service.vision_session:
                logger.info("\n🔍 Vision Encoder Details:")
                inputs = local_vision_service.vision_session.get_inputs()
                outputs = local_vision_service.vision_session.get_outputs()
                logger.info(f"  Inputs ({len(inputs)}):")
                for inp in inputs:
                    logger.info(f"    - {inp.name}: {inp.shape} ({inp.type})")
                logger.info(f"  Outputs ({len(outputs)}):")
                for out in outputs:
                    logger.info(f"    - {out.name}: {out.shape} ({out.type})")
            
            return True
        else:
            logger.error("\n❌ ❌ ❌ Failed to load Florence-2 models ❌ ❌ ❌")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_florence_loading()
    sys.exit(0 if success else 1)
