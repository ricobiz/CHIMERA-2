import openai
from openai import OpenAI
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class DesignGeneratorService:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        self.design_prompt = """You are an expert UI/UX designer. Based on the user's request, create a detailed visual design description for the application.

**User Request:** {user_request}

**Your Task:**
1. Analyze the request and determine the core functionality
2. Propose a complete visual design including:
   - Color scheme and theme (light/dark, color palette)
   - Layout structure (header, main content, footer, sidebar if needed)
   - Component placement (where buttons, forms, lists go)
   - Typography (font styles, sizes for headers, body text)
   - Spacing and padding guidelines
   - Interactive elements styling (buttons, inputs, hover states)
   - Visual hierarchy and emphasis
   - Responsive behavior

**Response Format:**
Provide a detailed design specification in natural language that a developer can follow. Be specific about colors (use hex codes), spacing (use px/rem), and layout decisions.

Example: "Create a dark theme app (#0f0f10 background) with a top navigation bar (#1a1a1b, 64px height). Main content area should have 24px padding..."

Be creative but practical. Ensure the design matches the app's purpose."""

        self.mockup_prompt = """You are a UI/UX designer creating visual mockups. Generate a clean, modern UI mockup image based on this description:

{design_spec}

Create a high-quality mockup that shows:
- The main interface layout
- Color scheme applied
- Typography hierarchy
- Component placement
- Professional, polished appearance

Style: Modern, clean, professional UI design suitable for a web application."""

    async def generate_design(self, user_request: str, model: str = None) -> Dict:
        """Generate design specification using vision-capable model"""
        try:
            # Use Gemini 2.5 Flash Image (nano banana) for design generation
            selected_model = model or "google/gemini-2.5-flash-image"
            
            prompt = self.design_prompt.format(user_request=user_request)
            
            logger.info(f"Generating design with model: {selected_model}")
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            design_spec = response.choices[0].message.content
            
            logger.info("Design specification generated successfully")
            
            return {
                "design_spec": design_spec,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating design: {str(e)}")
            raise Exception(f"Failed to generate design: {str(e)}")
    
    async def generate_visual_mockup(self, design_spec: str, user_request: str, model: str = None) -> Dict:
        """Generate visual mockup IMAGE using Imagen-3 via OpenRouter images.generate endpoint"""
        try:
            # Imagen-3 model for image generation
            selected_model = model or "google/imagen-3.0-generate-002"
            
            logger.info(f"🎨 [IMAGE GEN] Using model: {selected_model}")
            
            # Промпт для UI мокапа
            image_prompt = f"""Create a professional UI mockup for: {user_request}

Design: {design_spec[:500]}

Style: Modern web interface, clean layout, professional colors, realistic mockup showing main screen with all key UI elements."""
            
            logger.info(f"🎨 [IMAGE GEN] Prompt: {image_prompt[:100]}...")
            
            # ПРАВИЛЬНЫЙ СПОСОБ: использовать images.generate() endpoint
            try:
                # OpenAI SDK поддерживает images.generate для OpenRouter
                response = self.client.images.generate(
                    model=selected_model,
                    prompt=image_prompt,
                    n=1,
                    response_format="b64_json"  # base64 JSON format
                )
                
                # Извлекаем base64 изображение
                if response.data and len(response.data) > 0:
                    image_data = response.data[0]
                    
                    # Проверяем формат ответа
                    if hasattr(image_data, 'b64_json') and image_data.b64_json:
                        b64_image = image_data.b64_json
                        mockup_url = f"data:image/png;base64,{b64_image}"
                        
                        logger.info(f"✅ [IMAGE GEN] Image generated successfully: {len(mockup_url)} chars")
                        
                        return {
                            "mockup_data": mockup_url,
                            "design_spec": design_spec,
                            "is_image": True,
                            "usage": {}
                        }
                    elif hasattr(image_data, 'url') and image_data.url:
                        # Если вернулся URL вместо base64
                        mockup_url = image_data.url
                        
                        logger.info(f"✅ [IMAGE GEN] Image URL generated: {mockup_url}")
                        
                        return {
                            "mockup_data": mockup_url,
                            "design_spec": design_spec,
                            "is_image": True,
                            "usage": {}
                        }
                    else:
                        logger.error(f"❌ [IMAGE GEN] No image data in response: {image_data}")
                        raise Exception("No image data in response")
                else:
                    logger.error(f"❌ [IMAGE GEN] Empty response.data")
                    raise Exception("Empty response from images.generate")
                    
            except Exception as sdk_error:
                logger.error(f"❌ [IMAGE GEN] SDK error: {str(sdk_error)}")
                logger.info("🔄 [IMAGE GEN] Trying fallback with httpx...")
                
                # Fallback: прямой HTTP запрос
                import httpx
                api_key = os.environ.get('OPENROUTER_API_KEY')
                
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.post(
                        "https://openrouter.ai/api/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://chimera-aios.com",
                            "X-Title": "Chimera AIOS"
                        },
                        json={
                            "model": selected_model,
                            "prompt": image_prompt,
                            "n": 1,
                            "response_format": "b64_json"
                        },
                        timeout=60.0
                    )
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"❌ [IMAGE GEN] HTTP error: {error_text}")
                        raise Exception(f"HTTP {response.status_code}: {error_text}")
                    
                    data = response.json()
                    
                    if 'data' in data and len(data['data']) > 0:
                        image_obj = data['data'][0]
                        
                        if 'b64_json' in image_obj:
                            b64_image = image_obj['b64_json']
                            mockup_url = f"data:image/png;base64,{b64_image}"
                            
                            logger.info(f"✅ [IMAGE GEN] Image generated via fallback")
                            
                            return {
                                "mockup_data": mockup_url,
                                "design_spec": design_spec,
                                "is_image": True,
                                "usage": {}
                            }
                        elif 'url' in image_obj:
                            mockup_url = image_obj['url']
                            
                            logger.info(f"✅ [IMAGE GEN] Image URL via fallback: {mockup_url}")
                            
                            return {
                                "mockup_data": mockup_url,
                                "design_spec": design_spec,
                                "is_image": True,
                                "usage": {}
                            }
                    
                    raise Exception(f"No image data in fallback response: {data}")
            
        except Exception as e:
            logger.error(f"❌ [IMAGE GEN] Complete failure: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Вернем текстовое описание как fallback
            return {
                "mockup_data": f"⚠️ Image generation failed: {str(e)}\n\nDesign description:\n\n{design_spec}",
                "design_spec": design_spec,
                "is_image": False,
                "error": str(e)
            }
    
    async def revise_design(self, current_design: str, revision_request: str, model: str = None) -> Dict:
        """Revise existing design based on user feedback"""
        try:
            selected_model = model or "google/gemini-2.5-flash-image"
            
            revision_prompt = f"""You are revising a UI/UX design based on user feedback.

**Current Design:**
{current_design}

**User's Revision Request:**
{revision_request}

**Your Task:**
Update the design specification to incorporate the user's requested changes while maintaining consistency and professionalism. Keep what works and only change what the user requested.

Provide the UPDATED design specification in the same detailed format as before."""

            logger.info(f"Revising design with model: {selected_model}")
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "user", "content": revision_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            revised_design = response.choices[0].message.content
            
            logger.info("Design revision completed successfully")
            
            return {
                "design_spec": revised_design,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error revising design: {str(e)}")
            raise Exception(f"Failed to revise design: {str(e)}")

design_generator_service = DesignGeneratorService()
