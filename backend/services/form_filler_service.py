"""
Smart Form Filler - автоматическое заполнение форм на основе DOM elements и generated data
ЦЕЛЬ: Упростить автоматизацию и сделать её более надёжной без зависимости от vision модели
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormFillerService:
    """
    Определяет формы на странице и автоматически заполняет их используя generated data
    """
    
    def analyze_form(self, vision_elements: List[Dict[str, Any]], url: str) -> Optional[Dict[str, Any]]:
        """
        Анализирует элементы и определяет есть ли форма для заполнения
        
        Returns:
            {
                'form_type': 'registration' | 'login' | 'profile',
                'fields': [{'cell': 'E4', 'type': 'email', 'label': '...'}, ...],
                'submit_button': {'cell': 'E17', 'label': 'Register'}
            }
        """
        if not vision_elements:
            return None
        
        # Ищем INPUT поля
        input_fields = [e for e in vision_elements if e.get('type', '').lower() in ['input', 'textarea']]
        
        if len(input_fields) < 2:
            return None  # Слишком мало полей для формы
        
        logger.info(f"🔍 [FORM FILLER] Found {len(input_fields)} input fields")
        
        # Определяем тип формы по URL или количеству полей
        form_type = self._detect_form_type(url, len(input_fields))
        
        # Ищем кнопку submit
        submit_button = None
        submit_keywords = ['register', 'sign up', 'submit', 'create account', 'continue', 'next']
        for elem in vision_elements:
            label = (elem.get('label') or '').lower()
            if any(kw in label for kw in submit_keywords):
                if elem.get('type', '').lower() in ['button', 'a']:
                    submit_button = elem
                    break
        
        # Классифицируем поля
        classified_fields = self._classify_fields(input_fields)
        
        result = {
            'form_type': form_type,
            'fields': classified_fields,
            'submit_button': submit_button,
            'confidence': 0.8 if len(classified_fields) >= 2 else 0.5
        }
        
        logger.info(f"📋 [FORM FILLER] Detected {form_type} form with {len(classified_fields)} fields")
        return result
    
    def _detect_form_type(self, url: str, field_count: int) -> str:
        """Определяет тип формы"""
        url_lower = url.lower()
        
        if 'register' in url_lower or 'signup' in url_lower or 'join' in url_lower:
            return 'registration'
        elif 'login' in url_lower or 'signin' in url_lower:
            return 'login'
        elif 'profile' in url_lower or 'settings' in url_lower:
            return 'profile'
        elif field_count >= 4:
            return 'registration'  # Много полей = скорее всего регистрация
        elif field_count <= 2:
            return 'login'
        else:
            return 'unknown'
    
    def _classify_fields(self, input_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Классифицирует INPUT поля по их позиции и порядку
        
        Обычный порядок в формах регистрации:
        1. Email/Username
        2. Password
        3. Confirm Password (опционально)
        4. First Name / Full Name
        5. Other fields
        """
        classified = []
        
        # Сортируем поля по позиции (сверху вниз, слева направо)
        sorted_fields = sorted(input_fields, key=lambda f: (
            int(f.get('cell', 'A1')[1:]),  # row number
            ord(f.get('cell', 'A1')[0])    # column letter
        ))
        
        field_types = ['email', 'password', 'password_confirm', 'username', 'first_name', 'last_name']
        
        for idx, field in enumerate(sorted_fields):
            field_type = field_types[idx] if idx < len(field_types) else 'other'
            
            classified.append({
                'cell': field.get('cell'),
                'bbox': field.get('bbox'),
                'label': field.get('label'),
                'suggested_type': field_type,
                'order': idx + 1
            })
        
        return classified
    
    def generate_fill_actions(self, form_info: Dict[str, Any], generated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерирует последовательность действий для заполнения формы
        
        Returns:
            [
                {'action': 'TYPE_AT_CELL', 'cell': 'E4', 'text': 'email@example.com'},
                {'action': 'TYPE_AT_CELL', 'cell': 'E7', 'text': 'password123'},
                {'action': 'CLICK_CELL', 'cell': 'E17'}
            ]
        """
        actions = []
        
        for field in form_info.get('fields', []):
            field_type = field.get('suggested_type')
            cell = field.get('cell')
            
            # Определяем какие данные использовать
            text = None
            if field_type == 'email':
                text = generated_data.get('email')
            elif field_type == 'username':
                text = generated_data.get('username')
            elif field_type in ['password', 'password_confirm']:
                text = generated_data.get('password')
            elif field_type == 'first_name':
                text = generated_data.get('first_name')
            elif field_type == 'last_name':
                text = generated_data.get('last_name')
            
            if text and cell:
                actions.append({
                    'action': 'TYPE_AT_CELL',
                    'cell': cell,
                    'text': text,
                    'field_type': field_type
                })
        
        # Добавляем клик на submit button
        submit_btn = form_info.get('submit_button')
        if submit_btn and submit_btn.get('cell'):
            actions.append({
                'action': 'CLICK_CELL',
                'cell': submit_btn.get('cell')
            })
        
        logger.info(f"✅ [FORM FILLER] Generated {len(actions)} fill actions")
        return actions


form_filler_service = FormFillerService()
