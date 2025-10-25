from fastapi import APIRouter, HTTPException
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["openrouter"])

# Popular models for code generation with approximate pricing
POPULAR_MODELS = [
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "input_cost_per_1m": 3.0,
        "output_cost_per_1m": 15.0,
        "context_length": 200000
    },
    {
        "id": "anthropic/claude-3-opus",
        "name": "Claude 3 Opus",
        "provider": "Anthropic",
        "input_cost_per_1m": 15.0,
        "output_cost_per_1m": 75.0,
        "context_length": 200000
    },
    {
        "id": "openai/gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "provider": "OpenAI",
        "input_cost_per_1m": 10.0,
        "output_cost_per_1m": 30.0,
        "context_length": 128000
    },
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI",
        "input_cost_per_1m": 2.5,
        "output_cost_per_1m": 10.0,
        "context_length": 128000
    },
    {
        "id": "google/gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google",
        "input_cost_per_1m": 1.25,
        "output_cost_per_1m": 5.0,
        "context_length": 1000000
    },
    {
        "id": "meta-llama/llama-4-scout",
        "name": "Llama 4 Scout",
        "provider": "Meta",
        "input_cost_per_1m": 0.5,
        "output_cost_per_1m": 1.5,
        "context_length": 128000
    },
    {
        "id": "qwen/qwen-2.5-coder-32b-instruct",
        "name": "Qwen 2.5 Coder 32B",
        "provider": "Qwen",
        "input_cost_per_1m": 0.3,
        "output_cost_per_1m": 0.9,
        "context_length": 32000
    },
    {
        "id": "mistralai/codestral-2501",
        "name": "Codestral 2501",
        "provider": "Mistral",
        "input_cost_per_1m": 0.3,
        "output_cost_per_1m": 0.9,
        "context_length": 256000
    }
]

@router.get("/models")
async def get_models():
    """Get list of available OpenRouter models for code generation"""
    return {"models": POPULAR_MODELS}