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
        
        self.design_prompt = """You are an expert UI/UX designer. Based on the user's request, create a HIGHLY DETAILED visual design specification for the application.

**User Request:** {user_request}

**Your Task:**
1. Analyze the request and determine the core functionality
2. Propose a COMPLETE and SPECIFIC visual design including:
   
   **Color Scheme:**
   - Primary color (exact hex code)
   - Secondary color (exact hex code)  
   - Background colors (exact hex codes for main bg, secondary bg)
   - Text colors (exact hex codes for headings, body, muted)
   - Accent/highlight colors (exact hex codes)
   - Border/divider colors (exact hex codes)
   
   **Layout Structure:**
   - Exact page structure (header height in px, content padding, footer)
   - Grid/flex layout specifications
   - Container widths (max-width values)
   - Spacing system (4px, 8px, 16px, 24px, 32px guidelines)
   
   **Typography:**
   - Font family recommendations
   - Heading sizes (h1: Xpx, h2: Xpx, etc.)
   - Body text size and line-height
   - Font weights for different elements
   
   **Components Styling:**
   - Button styles (primary, secondary) with exact colors, padding, border-radius
   - Input field styling (border, focus state, padding, height)
   - Card/container styling (background, shadow, border-radius, padding)
   - Lists, tables, or data display components
   
   **Interactive States:**
   - Hover effects (color changes, transforms)
   - Active/focus states
   - Disabled states
   - Loading states
   
   **Visual Elements:**
   - Border radius values (buttons, cards, inputs)
   - Shadow specifications (box-shadow values)
   - Icon placement and sizing
   - Image styling if applicable

**Response Format:**
Provide a DETAILED design specification that reads like a design system document. Use EXACT values:
- Colors: hex codes (#RRGGBB)
- Spacing: px or rem values
- Sizes: px or rem values
- Tailwind classes where applicable

Example: 
"PRIMARY COLOR: #8b5cf6 (purple-500)
BACKGROUND: #0f0f10 (almost black)
CARDS: bg-gray-900 (#111827), rounded-lg (8px), p-6 (24px padding), shadow-xl
BUTTONS: Primary button uses bg-purple-600 hover:bg-purple-700, rounded-md (6px), px-6 py-3 (24px x 12px), text-white font-semibold
INPUTS: bg-gray-800 border border-gray-700 focus:border-purple-500 rounded-md h-10 (40px) px-4"

Be EXTREMELY specific. The developer will implement EXACTLY what you specify."""

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
            selected_model = model or "google/gemini-2.5-flash-image-preview"
            
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
                
                # Извлекаем изображение из ответа - OpenRouter возвращает в images field ВНУТРИ message
                logger.info(f"🔍 [IMAGE GEN] Response type: {type(response)}")
                
                # Проверяем наличие images в ответе (через extra поле)
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
                logger.info(f"🔍 [IMAGE GEN] Response dict keys: {response_dict.keys()}")
                
                # OpenRouter возвращает images ВНУТРИ message, а не в корне response
                if response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    message = choice.message
                    mockup_url = None
                    
                    # Проверяем, есть ли images в message (новый формат OpenRouter)
                    # Try direct attribute access first, then model_dump
                    if hasattr(message, 'images') and message.images:
                        images = message.images
                        logger.info(f"✅ [IMAGE GEN] Found images via direct access: {len(images)}")
                        
                        # Извлекаем первый image_url
                        first_image = images[0]
                        if isinstance(first_image, dict) and 'image_url' in first_image:
                            mockup_url = first_image['image_url'].get('url') if isinstance(first_image['image_url'], dict) else first_image['image_url']
                        else:
                            mockup_url = first_image
                    else:
                        # Fallback to model_dump approach
                        message_dict = message.model_dump() if hasattr(message, 'model_dump') else message.__dict__
                        logger.info(f"🔍 [IMAGE GEN] Message dict keys: {message_dict.keys()}")
                        
                        if 'images' in message_dict and message_dict['images']:
                            # Images field содержит массив объектов с image_url
                            images = message_dict['images']
                            logger.info(f"✅ [IMAGE GEN] Found images in message dict: {len(images)}")
                            
                            # Извлекаем первый image_url
                            first_image = images[0]
                            if isinstance(first_image, dict) and 'image_url' in first_image:
                                mockup_url = first_image['image_url'].get('url') if isinstance(first_image['image_url'], dict) else first_image['image_url']
                            else:
                                mockup_url = first_image
                    
                    # If we found an image, return it
                    if mockup_url:
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
                    logger.error("❌ [IMAGE GEN] No images or choices in response")
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
                            "modalities": ["image", "text"]
                        },
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Проверяем наличие images в ответе (приоритет)
                        if 'images' in data and data['images']:
                            images = data['images']
                            mockup_url = images[0] if isinstance(images, list) else images
                            
                            logger.info(f"✅ [IMAGE GEN] HTTP fallback successful (images field): {len(str(mockup_url))} chars")
                            
                            return {
                                "mockup_data": mockup_url,
                                "design_spec": design_spec,
                                "is_image": True,
                                "usage": data.get('usage', {})
                            }
                        elif 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            message_content = choice.get('message', {}).get('content', '')
                            
                            logger.warning(f"⚠️ [IMAGE GEN] HTTP fallback: No images field, got text response: {message_content[:100] if message_content else 'None'}")
                            
                            if message_content and (message_content.startswith('data:image') or 
                                                  message_content.startswith('/9j/') or 
                                                  message_content.startswith('iVBOR')):
                                # Обработка base64
                                if message_content.startswith('data:image'):
                                    mockup_url = message_content
                                else:
                                    mockup_url = f"data:image/png;base64,{message_content}"
                                
                                logger.info(f"✅ [IMAGE GEN] HTTP fallback successful (content field): {len(mockup_url)} chars")
                                
                                return {
                                    "mockup_data": mockup_url,
                                    "design_spec": design_spec,
                                    "is_image": True,
                                    "usage": data.get('usage', {})
                                }
                            else:
                                raise Exception(f"HTTP fallback: Model returned text instead of image: {message_content[:200] if message_content else 'No content'}")
                        else:
                            raise Exception("HTTP fallback: No images or choices in response")
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
