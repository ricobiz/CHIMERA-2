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
        """Generate visual mockup IMAGE using Gemini 2.5 Flash Image (Nano Banana) via chat completions endpoint"""
        try:
            # Use Gemini 2.5 Flash Image (Nano Banana) for image generation
            selected_model = model or "google/gemini-2.5-flash-image"
            
            logger.info(f"🎨 [IMAGE GEN] Using model: {selected_model}")
            
            # Промпт для UI мокапа или любого изображения
            image_prompt = f"""Create a professional high-quality image for: {user_request}

Design: {design_spec[:500]}

Style: Modern, clean, professional, high-quality, realistic."""
            
            logger.info(f"🎨 [IMAGE GEN] Prompt: {image_prompt[:100]}...")
            
            # ПРАВИЛЬНЫЙ СПОСОБ для Gemini 2.5 Flash Image: chat completions с modalities
            try:
                response = self.client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {
                            "role": "user",
                            "content": image_prompt
                        }
                    ],
                    extra_body={
                        "modalities": ["image", "text"]  # Ключевой параметр для генерации изображения
                    }
                )
                
                # Извлекаем изображение из ответа - OpenRouter возвращает в images field
                logger.info(f"🔍 [IMAGE GEN] Response structure: {dir(response)}")
                
                # Проверяем наличие images в ответе (через extra поле)
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
                
                if 'images' in response_dict and response_dict['images']:
                    # Images field содержит массив base64 data URLs
                    images = response_dict['images']
                    mockup_url = images[0] if isinstance(images, list) else images
                    
                    logger.info(f"✅ [IMAGE GEN] Image generated successfully: {len(str(mockup_url))} chars")
                    
                    return {
                        "mockup_data": mockup_url,
                        "design_spec": design_spec,
                        "is_image": True,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                            "total_tokens": response.usage.total_tokens if response.usage else 0
                        }
                    }
                elif response.choices and len(response.choices) > 0:
                    # Fallback: check message content
                    choice = response.choices[0]
                    message_content = choice.message.content
                    
                    logger.warning(f"⚠️ [IMAGE GEN] No images field, got text response: {message_content[:100]}")
                    
                    # Если это base64 изображение в content
                    if message_content and (message_content.startswith('data:image') or 
                                          message_content.startswith('/9j/') or 
                                          message_content.startswith('iVBOR')):
                        if not message_content.startswith('data:image'):
                            mockup_url = f"data:image/png;base64,{message_content}"
                        else:
                            mockup_url = message_content
                        
                        return {
                            "mockup_data": mockup_url,
                            "design_spec": design_spec,
                            "is_image": True,
                            "usage": {
                                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                                "total_tokens": response.usage.total_tokens if response.usage else 0
                            }
                        }
                    else:
                        # Это текстовый ответ, не изображение
                        raise Exception(f"Model returned text instead of image: {message_content[:200]}")
                else:
                    logger.error(f"❌ [IMAGE GEN] No images or choices in response")
                    raise Exception("No images or choices in response")
                    
            except Exception as sdk_error:
                logger.error(f"❌ [IMAGE GEN] SDK error: {str(sdk_error)}")
                logger.info("🔄 [IMAGE GEN] Trying direct httpx fallback...")
                
                # Fallback: прямой HTTP запрос к OpenRouter
                import httpx
                api_key = os.environ.get('OPENROUTER_API_KEY')
                
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://chimera-aios.com",
                            "X-Title": "Chimera AIOS"
                        },
                        json={
                            "model": selected_model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": image_prompt
                                }
                            ],
                            "response_modality": "IMAGE"
                        },
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            message_content = choice.get('message', {}).get('content', '')
                            
                            if message_content:
                                # Обработка base64
                                if message_content.startswith('data:image'):
                                    mockup_url = message_content
                                elif message_content.startswith('/9j/') or message_content.startswith('iVBOR'):
                                    mockup_url = f"data:image/png;base64,{message_content}"
                                else:
                                    mockup_url = message_content
                                
                                logger.info(f"✅ [IMAGE GEN] HTTP fallback successful: {len(mockup_url)} chars")
                                
                                return {
                                    "mockup_data": mockup_url,
                                    "design_spec": design_spec,
                                    "is_image": True,
                                    "usage": data.get('usage', {})
                                }
                    else:
                        error_text = response.text
                        logger.error(f"❌ [IMAGE GEN] HTTP error: {error_text}")
                        raise Exception(f"HTTP {response.status_code}: {error_text}")
            
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
