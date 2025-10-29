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
        """Generate visual mockup image based on design specification"""
        try:
            # Выбираем модель генерации изображений
            # Gemini Nano Banana (imagen-3.0-generate-002) или gpt-image-1
            selected_model = model or "google/imagen-3.0-generate-002"
            
            logger.info(f"Generating visual mockup IMAGE with model: {selected_model}")
            
            # Создаем промпт для генерации изображения
            image_prompt = f"""Create a clean, modern UI mockup image for: {user_request}

Design specifications:
{design_spec}

Style: Professional, clean, modern web interface. Show the main screen with all key elements visible. High quality, realistic mockup."""
            
            # ВАРИАНТ 1: Если модель поддерживает прямую генерацию изображений (OpenAI, Gemini)
            if "gpt-image" in selected_model or "imagen" in selected_model:
                # Используем images endpoint
                try:
                    # Для OpenRouter + image models нужен специальный формат
                    response = self.client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {
                                "role": "user",
                                "content": image_prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    # Ответ может содержать URL или base64
                    content = response.choices[0].message.content
                    
                    # Проверяем формат ответа
                    if content and (content.startswith('http') or content.startswith('data:image')):
                        mockup_url = content
                    else:
                        # Если модель вернула текст вместо URL - это ошибка
                        logger.warning(f"Model returned text instead of image URL: {content[:100]}")
                        mockup_url = None
                    
                    logger.info(f"Visual mockup generated: {mockup_url[:50] if mockup_url else 'No image'}")
                    
                    return {
                        "mockup_data": mockup_url if mockup_url else content,
                        "design_spec": design_spec,
                        "is_image": bool(mockup_url),
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                            "total_tokens": response.usage.total_tokens if response.usage else 0
                        }
                    }
                except Exception as img_error:
                    logger.error(f"Image generation failed: {str(img_error)}")
                    # Fallback: вернем текстовое описание
                    return {
                        "mockup_data": f"⚠️ Image generation unavailable. Design description:\n\n{design_spec}",
                        "design_spec": design_spec,
                        "is_image": False,
                        "error": str(img_error)
                    }
            else:
                # Если модель не поддерживает изображения - вернем текст
                logger.warning(f"Model {selected_model} doesn't support image generation")
                return {
                    "mockup_data": f"📝 Text-only design specification:\n\n{design_spec}",
                    "design_spec": design_spec,
                    "is_image": False
                }
            
        except Exception as e:
            logger.error(f"Error generating mockup: {str(e)}")
            raise Exception(f"Failed to generate mockup: {str(e)}")
    
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
