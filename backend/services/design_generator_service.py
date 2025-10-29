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
            # Use image generation model (Gemini Nano Banana or GPT-5 Image)
            selected_model = model or "google/gemini-2.5-flash-image-preview"
            
            # Create detailed mockup prompt
            mockup_prompt = self.mockup_prompt.format(design_spec=design_spec)
            
            logger.info(f"Generating visual mockup with model: {selected_model}")
            
            # For image generation, we need to use the images endpoint
            # Note: OpenRouter might have different endpoints for different models
            # Gemini can generate images through chat completions
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "user",
                        "content": f"Create a UI mockup image for this application:\n\n{user_request}\n\nDesign specifications:\n{design_spec}\n\nGenerate a clean, professional mockup image showing the main interface."
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract image URL or base64 from response
            # Note: Response format depends on model
            mockup_data = response.choices[0].message.content
            
            logger.info("Visual mockup generated successfully")
            
            return {
                "mockup_data": mockup_data,
                "design_spec": design_spec,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
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
