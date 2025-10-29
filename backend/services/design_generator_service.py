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
        """Generate visual mockup IMAGE using Gemini Nano Banana (imagen-3)"""
        try:
            # Gemini Nano Banana (imagen-3.0-generate-002) - image generation model
            selected_model = model or "google/imagen-3.0-generate-002"
            
            logger.info(f"🎨 Generating visual mockup IMAGE with: {selected_model}")
            
            # Промпт для генерации изображения UI
            image_prompt = f"""Create a clean, modern UI mockup image for: {user_request}

Design specifications:
{design_spec}

Style: Professional web interface mockup with clean design, modern colors, realistic layout. Show the main screen with all key UI elements clearly visible."""
            
            # ПРАВИЛЬНЫЙ ФОРМАТ для OpenRouter image generation через httpx:
            # OpenRouter требует специальный заголовок и формат для imagen
            import httpx
            
            api_key = os.environ.get('OPENROUTER_API_KEY')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
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
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=60.0
                )
                
                data = response.json()
                
                if response.status_code != 200:
                    logger.error(f"❌ OpenRouter error: {data}")
                    raise Exception(f"OpenRouter API error: {data.get('error', {}).get('message', 'Unknown error')}")
                
                # Проверяем ответ
                if 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    message = choice.get('message', {})
                    content = message.get('content', '')
                    
                    # Imagen-3 возвращает base64 в content
                    if content and (content.startswith('data:image') or content.startswith('http')):
                        logger.info(f"✅ Image generated successfully: {len(content)} chars")
                        
                        return {
                            "mockup_data": content,
                            "design_spec": design_spec,
                            "is_image": True,
                            "usage": data.get('usage', {})
                        }
                    else:
                        # Модель вернула текст вместо изображения
                        logger.warning(f"⚠️ Model returned text instead of image: {content[:200]}")
                        
                        return {
                            "mockup_data": f"⚠️ Image generation unavailable. Model returned text:\n\n{content}",
                            "design_spec": design_spec,
                            "is_image": False,
                            "error": "Model returned text instead of image"
                        }
                else:
                    logger.error(f"❌ Unexpected response format: {data}")
                    return {
                        "mockup_data": f"⚠️ Unexpected response format",
                        "design_spec": design_spec,
                        "is_image": False,
                        "error": "Unexpected response"
                    }
            
        except Exception as e:
            logger.error(f"❌ Error generating mockup: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: вернем текстовое описание
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
