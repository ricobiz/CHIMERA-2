"""
Head Brain Service - Главная модель для планирования автоматизации
Использует умную LLM (GPT-5, Claude Sonnet 4, Grok 4, Gemini) для:
1. Анализа задачи
2. Определения требований (прогретый профиль, данные)
3. Создания общего плана для спинного мозга
4. Генерации необходимых данных (реалистичных!)
"""

import os
import json
import random
import logging
from typing import Dict, Any, List, Optional
import httpx
from faker import Faker

logger = logging.getLogger(__name__)

# Назначаемая модель (можно менять)
DEFAULT_HEAD_MODEL = os.environ.get('HEAD_BRAIN_MODEL', 'openai/gpt-4o')

# Faker для реалистичной генерации данных
fake = Faker(['en_US', 'en_GB'])  # Английские локали для реалистичности

def _gen_realistic_data() -> Dict[str, str]:
    """Генерация РЕАЛИСТИЧНЫХ данных с помощью Faker"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = f"{first_name.lower()}.{last_name.lower()}.{random.randint(100, 999)}"
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": fake.email(),
        "password": fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "birthday": fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%Y-%m-%d'),
        "phone_number": fake.phone_number(),
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "country": "US",
        "postal_code": fake.postcode(),
        "company": fake.company(),
        "job_title": fake.job(),
    }


class HeadBrainService:
    """
    Головной мозг - главная модель для планирования.
    Вызывается ОДИН РАЗ в начале автоматизации.
    """
    
    def __init__(self):
        self.model = DEFAULT_HEAD_MODEL
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not set, head brain will not work")
    
    async def analyze_and_plan(self, goal: str, profile_info: Optional[Dict] = None, user_data: Optional[Dict] = None, auto_generate: bool = False) -> Dict[str, Any]:
        """
        Главная функция головного мозга:
        1. Анализирует задачу
        2. Определяет требования
        3. **ОСТАНАВЛИВАЕТСЯ** если нужны данные но их нет
        4. Создаёт план
        5. Генерирует данные ТОЛЬКО если auto_generate=True
        
        Args:
            goal: Задача пользователя
            profile_info: Информация о профиле
            user_data: Данные от пользователя (опционально)
            auto_generate: Автоматически генерировать данные без вопроса (по умолчанию False)
            
        Returns:
            Если нужны данные но их нет → {"status": "NEEDS_USER_DATA", "required_fields": [...]}
            Если всё ОК → полный analysis
        """
        
        logger.info(f"🧠 [HEAD BRAIN] Analyzing task: {goal}")
        
        # Проверяем доступность прогретого профиля
        has_warm_profile = bool(profile_info and profile_info.get('is_warm'))
        profile_proxy_type = (profile_info or {}).get('proxy_type')
        
        # Формируем промпт для головного мозга
        system_prompt = """Ты - главный стратег автоматизации браузера. Твоя задача:
1. СТРУКТУРИРОВАТЬ задачу пользователя и извлечь все данные
2. Определить что нужно для выполнения (прогретый профиль, телефон, данные)
3. Оценить можно ли выполнить без телефона (если профиль прогретый)
4. Создать стратегию и общий план

ВАЖНО:
- ОБЯЗАТЕЛЬНО извлеки URL сайта из задачи пользователя
- Если задача = регистрация на строгом сайте (Gmail, Facebook) БЕЗ прогретого профиля → нужен телефон (вероятность 90%)
- Если задача = регистрация С прогретым профилем → можно попробовать БЕЗ телефона (вероятность 60-70%)
- Если задача = простая навигация → прогрев не нужен

Верни JSON:
{
  "target_url": "https://example.com (ОБЯЗАТЕЛЬНО извлеки из задачи пользователя)",
  "understood_task": "Краткое описание задачи",
  "task_type": "registration" | "navigation" | "form_fill" | "data_extraction",
  "requirements": {
    "needs_warm_profile": true/false,
    "needs_phone": true/false (только если точно нужен),
    "mandatory_data": ["first_name", "last_name", ...],
    "optional_data": ["phone_number", ...]
  },
  "strategy": "attempt_without_phone" | "require_phone" | "simple_navigation",
  "success_probability": 0.0-1.0,
  "plan_outline": "Краткий план для средней модели",
  "can_proceed": true/false,
  "reason": "Почему можем/не можем продолжить"
}"""
        
        user_prompt = f"""Задача: {goal}

Доступные ресурсы:
- Прогретый профиль: {'ДА' if has_warm_profile else 'НЕТ'}
- Тип прокси: {profile_proxy_type or 'нет'}
- Телефон: НЕТ

Проанализируй и создай стратегию."""

        try:
            # Вызываем умную модель
            result = await self._call_openrouter(system_prompt, user_prompt)
            
            if not result or result.get('error'):
                logger.error(f"❌ [HEAD BRAIN] LLM error: {result}")
                # Fallback на простую логику
                return self._fallback_analysis(goal, has_warm_profile)
            
            # Генерируем или используем данные пользователя
            data_source = "generated"
            
            if user_data:
                # Используем данные пользователя + дополняем недостающее
                fn = user_data.get('first_name') or random.choice(FIRST_NAMES)
                ln = user_data.get('last_name') or random.choice(LAST_NAMES)
                
                data_bundle = {
                    "first_name": user_data.get('first_name', fn),
                    "last_name": user_data.get('last_name', ln),
                    "username": user_data.get('username') or user_data.get('email') or _gen_username(fn, ln),
                    "email": user_data.get('email'),
                    "password": user_data.get('password') or _gen_password(),
                    "birthday": user_data.get('birthday') or _gen_birthday(),
                    "phone_number": user_data.get('phone_number'),
                    "recovery_email": user_data.get('recovery_email'),
                    "address": user_data.get('address'),
                    "city": user_data.get('city'),
                    "country": user_data.get('country'),
                    "postal_code": user_data.get('postal_code'),
                }
                data_source = "user_provided"
                logger.info(f"✅ [HEAD BRAIN] Using user-provided data (filled {sum(1 for v in user_data.values() if v)} fields)")
            else:
                # Полностью генерируем данные
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                data_bundle = {
                    "first_name": fn,
                    "last_name": ln,
                    "username": _gen_username(fn, ln),
                    "email": f"{_gen_username(fn, ln)}@gmail.com",
                    "password": _gen_password(),
                    "birthday": _gen_birthday(),
                    "phone_number": None,
                    "recovery_email": None,
                    "address": None,
                    "city": None,
                    "country": "US",
                    "postal_code": None,
                }
                logger.info("✅ [HEAD BRAIN] Generated all data automatically")
            
            # Формируем финальный ответ
            analysis = {
                "task_id": result.get('task_id', 'head-' + str(random.randint(1000, 9999))),
                "target_url": result.get('target_url', ''),
                "understood_task": result.get('understood_task', goal),
                "task_type": result.get('task_type', 'unknown'),
                "requirements": result.get('requirements', {}),
                "strategy": result.get('strategy', 'attempt_without_phone'),
                "success_probability": result.get('success_probability', 0.65),
                "plan_outline": result.get('plan_outline', ''),
                "data_bundle": data_bundle,
                "data_source": data_source,  # user_provided или generated
                "can_proceed": result.get('can_proceed', True),
                "reason": result.get('reason', 'Analysis complete'),
                "profile_status": {
                    "is_warm": has_warm_profile,
                    "proxy_type": profile_proxy_type
                }
            }
            
            logger.info(f"✅ [HEAD BRAIN] Analysis complete: strategy={analysis['strategy']}, data_source={data_source}, can_proceed={analysis['can_proceed']}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ [HEAD BRAIN] Exception: {e}")
            return self._fallback_analysis(goal, has_warm_profile, user_data)
    
    def _fallback_analysis(self, goal: str, has_warm_profile: bool, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Простая fallback логика если LLM не работает"""
        logger.warning("⚠️ [HEAD BRAIN] Using fallback analysis")
        
        goal_lower = goal.lower()
        is_registration = any(kw in goal_lower for kw in ['register', 'регистр', 'sign up', 'create account'])
        
        # Извлекаем URL через regex
        import re
        url_match = re.search(r'https?://[^\s]+', goal)
        target_url = url_match.group(0) if url_match else ''
        
        # Определяем тип сайта
        if 'gmail' in goal_lower or 'google' in goal_lower:
            target_url = target_url or 'https://accounts.google.com/signup'
        elif 'facebook' in goal_lower:
            target_url = target_url or 'https://www.facebook.com/reg'
        
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        
        # Данные пользователя или генерируем
        data_source = "generated"
        if user_data:
            fn = user_data.get('first_name', fn)
            ln = user_data.get('last_name', ln)
            data_bundle = {
                "first_name": user_data.get('first_name', fn),
                "last_name": user_data.get('last_name', ln),
                "username": user_data.get('username') or user_data.get('email') or _gen_username(fn, ln),
                "email": user_data.get('email'),
                "password": user_data.get('password') or _gen_password(),
                "birthday": user_data.get('birthday') or _gen_birthday(),
                "phone_number": user_data.get('phone_number'),
                "recovery_email": user_data.get('recovery_email'),
            }
            data_source = "user_provided"
        else:
            data_bundle = {
                "first_name": fn,
                "last_name": ln,
                "username": _gen_username(fn, ln),
                "email": f"{_gen_username(fn, ln)}@gmail.com",
                "password": _gen_password(),
                "birthday": _gen_birthday(),
                "phone_number": None,
                "recovery_email": None,
            }
        
        return {
            "task_id": f"fallback-{random.randint(1000, 9999)}",
            "target_url": target_url,
            "understood_task": goal,
            "task_type": "registration" if is_registration else "navigation",
            "requirements": {
                "needs_warm_profile": is_registration,
                "needs_phone": is_registration and not has_warm_profile,
                "mandatory_data": ["first_name", "last_name", "username", "password", "birthday"] if is_registration else [],
                "optional_data": ["phone_number", "recovery_email"]
            },
            "strategy": "attempt_without_phone" if has_warm_profile else "require_phone_or_warn",
            "success_probability": 0.7 if has_warm_profile else 0.3,
            "plan_outline": "Navigate → Fill registration form → Handle captcha/phone if needed → Submit",
            "data_bundle": data_bundle,
            "data_source": data_source,
            "can_proceed": True,
            "reason": "Fallback analysis - will attempt task",
            "profile_status": {
                "is_warm": has_warm_profile,
                "proxy_type": None
            }
        }
    
    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Вызов OpenRouter API для анализа"""
        if not self.api_key:
            return {"error": "No API key"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://chimera-aios.app"),
            "X-Title": os.environ.get("OPENROUTER_X_TITLE", "Chimera AIOS"),
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    logger.error(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")
                    return {"error": f"HTTP {resp.status_code}"}
                
                data = resp.json()
                content = data['choices'][0]['message']['content']
                
                # Парсим JSON
                try:
                    result = json.loads(content)
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON: {content[:200]}")
                    return {"error": "Invalid JSON from LLM"}
                    
        except Exception as e:
            logger.error(f"OpenRouter call failed: {e}")
            return {"error": str(e)}


# Singleton
head_brain_service = HeadBrainService()
