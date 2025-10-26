"""
Context Window Management System
Отслеживает контекстное окно и автоматически сжимает историю
"""
import logging
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from services.openrouter_service import openrouter_service
from services.ai_memory_service import memory_service

logger = logging.getLogger(__name__)

class ContextWindowManager:
    """
    Управление контекстным окном модели
    
    Возможности:
    - Отслеживание использования токенов
    - Автоматическое сжатие при приближении к лимиту
    - Создание новых сессий с preserved context
    - Связывание сессий (session chains)
    - Поиск по всей цепочке сессий
    """
    
    # Лимиты для разных моделей
    MODEL_LIMITS = {
        "anthropic/claude-3.5-sonnet": 200000,
        "anthropic/claude-3-opus": 200000,
        "anthropic/claude-3-haiku": 200000,
        "openai/gpt-4": 8192,
        "openai/gpt-4-turbo": 128000,
        "openai/gpt-4o": 128000,
        "google/gemini-pro": 32768,
        "google/gemini-2.5-pro": 2000000,
        "default": 8192
    }
    
    # Thresholds для действий
    COMPRESSION_THRESHOLD = 0.75  # 75% использования → начать сжатие
    NEW_SESSION_THRESHOLD = 0.90  # 90% → создать новую сессию
    
    def __init__(self):
        # Initialize tokenizer (using cl100k_base for GPT-4 style counting)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Tiktoken not available, using approximation")
    
    def count_tokens(self, text: str) -> int:
        """Подсчёт токенов в тексте"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: ~4 chars per token
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """Подсчёт токенов во всех сообщениях"""
        total = 0
        for msg in messages:
            # Count role + content
            total += self.count_tokens(msg.get('role', ''))
            total += self.count_tokens(msg.get('content', ''))
            # Add overhead (role markers, etc)
            total += 4
        return total
    
    async def get_model_limit(self, model: str) -> int:
        """
        Получить лимит контекста для модели
        Пытается получить из OpenRouter API, если не получается - использует fallback
        """
        try:
            # Try to fetch from OpenRouter API
            models_data = await openrouter_service.get_models()
            
            # Find our model
            for model_data in models_data.get('data', []):
                if model_data.get('id') == model:
                    context_length = model_data.get('context_length', 0)
                    if context_length > 0:
                        logger.info(f"✓ Model {model} context limit: {context_length} tokens (from OpenRouter)")
                        return context_length
            
            # Model not found in API, use fallback
            logger.warning(f"Model {model} not found in OpenRouter API, using fallback")
            
        except Exception as e:
            logger.warning(f"Failed to fetch model limits from OpenRouter: {str(e)}, using fallback")
        
        # Fallback to hardcoded limits
        return self.MODEL_LIMITS.get(model, self.MODEL_LIMITS["default"])
    
    async def calculate_usage(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """
        Рассчитать использование контекста
        
        Returns:
            {
                'current_tokens': int,
                'max_tokens': int,
                'percentage': float,
                'remaining': int,
                'needs_compression': bool,
                'needs_new_session': bool
            }
        """
        current = self.count_messages_tokens(messages)
        maximum = await self.get_model_limit(model)
        percentage = current / maximum if maximum > 0 else 0
        
        return {
            'current_tokens': current,
            'max_tokens': maximum,
            'percentage': percentage,
            'percentage_display': f"{percentage * 100:.1f}%",
            'remaining': maximum - current,
            'needs_compression': percentage >= self.COMPRESSION_THRESHOLD,
            'needs_new_session': percentage >= self.NEW_SESSION_THRESHOLD
        }
    
    async def compress_conversation(
        self,
        messages: List[Dict],
        model: str,
        target_reduction: float = 0.5
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Умное сжатие разговора
        
        Сохраняет:
        - System message
        - Последние N сообщений (самые свежие)
        - Важные факты и решения
        
        Args:
            messages: История сообщений
            model: Модель для сжатия
            target_reduction: Целевое сжатие (0.5 = сжать вдвое)
        
        Returns:
            (compressed_messages, compression_summary)
        """
        logger.info(f"🗜️ Starting conversation compression (target: {target_reduction * 100:.0f}% reduction)")
        
        if len(messages) <= 3:
            return messages, {'compressed': False, 'reason': 'Too few messages'}
        
        # Separate system message and conversation
        system_msg = None
        conversation = []
        
        for msg in messages:
            if msg.get('role') == 'system':
                system_msg = msg
            else:
                conversation.append(msg)
        
        # Keep last N messages (most recent context)
        keep_last_n = 4  # Last 2 exchanges
        recent_messages = conversation[-keep_last_n:] if len(conversation) > keep_last_n else conversation
        older_messages = conversation[:-keep_last_n] if len(conversation) > keep_last_n else []
        
        if not older_messages:
            return messages, {'compressed': False, 'reason': 'All messages are recent'}
        
        # Create summary of older messages
        summary = await self._summarize_conversation(older_messages, model)
        
        # Build compressed message list
        compressed = []
        
        if system_msg:
            compressed.append(system_msg)
        
        # Add summary as assistant message
        compressed.append({
            'role': 'assistant',
            'content': f"[Previous conversation summary]\n{summary['summary']}"
        })
        
        # Add recent messages
        compressed.extend(recent_messages)
        
        # Calculate compression stats
        original_tokens = self.count_messages_tokens(messages)
        compressed_tokens = self.count_messages_tokens(compressed)
        reduction = 1 - (compressed_tokens / original_tokens)
        
        compression_info = {
            'compressed': True,
            'original_tokens': original_tokens,
            'compressed_tokens': compressed_tokens,
            'reduction_percentage': reduction * 100,
            'messages_removed': len(older_messages),
            'messages_kept': len(recent_messages),
            'summary': summary['summary']
        }
        
        logger.info(f"✓ Compressed: {original_tokens} → {compressed_tokens} tokens ({reduction * 100:.1f}% reduction)")
        
        return compressed, compression_info
    
    async def _summarize_conversation(
        self,
        messages: List[Dict],
        model: str
    ) -> Dict[str, str]:
        """
        Создать сжатую сводку разговора с сохранением важного
        """
        # Format conversation for summarization
        conversation_text = "\n\n".join([
            f"{msg['role'].title()}: {msg['content']}"
            for msg in messages
        ])
        
        summary_prompt = f"""Summarize this conversation, preserving ALL important information:

{conversation_text}

Create a COMPREHENSIVE summary that includes:
1. Key facts mentioned by user (preferences, personal info, decisions)
2. Important questions asked and answers given
3. Tasks/goals discussed
4. Any commitments or promises made
5. Technical details or specific requirements

Be concise but DO NOT lose important context. This summary will replace the conversation.

Format as a flowing paragraph, not bullet points."""
        
        try:
            response = await openrouter_service.chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                model=model,
                temperature=0.3,
                max_tokens=1000
            )
            
            summary = response['choices'][0]['message']['content']
            
            return {'summary': summary}
            
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            # Fallback: simple truncation
            return {
                'summary': f"Previous conversation covered: {conversation_text[:500]}..."
            }
    
    async def create_new_session_with_context(
        self,
        current_session_id: str,
        compressed_messages: List[Dict],
        compression_info: Dict
    ) -> Dict[str, Any]:
        """
        Создать новую сессию с сохранённым контекстом
        
        Returns:
            {
                'new_session_id': str,
                'parent_session_id': str,
                'context_preserved': str,
                'chain_length': int
            }
        """
        from datetime import datetime
        import uuid
        
        new_session_id = str(uuid.uuid4())
        
        # Store in MongoDB with session chain info
        # (Assuming session_routes handles this)
        
        session_data = {
            'session_id': new_session_id,
            'parent_session_id': current_session_id,
            'created_at': datetime.now().isoformat(),
            'context_summary': compression_info.get('summary', ''),
            'original_session': current_session_id,
            'chain_depth': await self._get_chain_depth(current_session_id) + 1,
            'compressed_messages': compressed_messages
        }
        
        logger.info(f"🔗 Created new session {new_session_id} chained from {current_session_id}")
        
        # Remember in AI memory
        await memory_service.remember_conversation(
            user_message=f"Session {current_session_id} reached context limit",
            assistant_response=f"Created new session {new_session_id} with preserved context",
            session_id=new_session_id,
            important=True
        )
        
        return session_data
    
    async def _get_chain_depth(self, session_id: str) -> int:
        """Получить глубину цепочки сессий"""
        # TODO: Query MongoDB to find parent chain
        # For now, return 0
        return 0
    
    async def get_session_chain(self, session_id: str) -> List[str]:
        """
        Получить всю цепочку связанных сессий
        
        Returns:
            [oldest_session_id, ..., current_session_id]
        """
        # TODO: Implement MongoDB query
        # Query parent_session_id recursively
        chain = [session_id]
        
        # Placeholder
        return chain
    
    async def search_across_sessions(
        self,
        session_chain: List[str],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Поиск по всей цепочке сессий
        
        Использует vector memory для поиска релевантного контекста
        из всех связанных сессий
        """
        results = []
        
        for session_id in session_chain:
            # Search in memory for this session
            memories = await memory_service.recall(
                query=query,
                memory_type="conversation",
                n_results=3
            )
            
            # Filter by session_id
            session_memories = [
                m for m in memories 
                if m.get('metadata', {}).get('session_id') == session_id
            ]
            
            results.extend(session_memories)
        
        # Sort by relevance
        results.sort(key=lambda x: x.get('distance', 999))
        
        return results[:5]  # Top 5 across all sessions
    
    def format_context_warning(self, usage: Dict) -> str:
        """Форматировать предупреждение о контексте для UI"""
        percentage = usage['percentage']
        
        if percentage >= 0.95:
            return f"⚠️ Context nearly full ({usage['percentage_display']}) - Creating new session..."
        elif percentage >= 0.80:
            return f"⚠️ Context usage high ({usage['percentage_display']}) - Will compress soon"
        elif percentage >= 0.60:
            return f"ℹ️ Context usage: {usage['percentage_display']}"
        else:
            return ""
    
    async def auto_manage_context(
        self,
        messages: List[Dict],
        session_id: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Автоматическое управление контекстом
        
        Вызывается перед каждым chat request
        
        Returns:
            {
                'action': 'none' | 'compress' | 'new_session',
                'messages': List[Dict],  # Potentially compressed
                'new_session_id': Optional[str],
                'warning': str
            }
        """
        usage = self.calculate_usage(messages, model)
        
        result = {
            'action': 'none',
            'messages': messages,
            'new_session_id': None,
            'warning': self.format_context_warning(usage),
            'usage': usage
        }
        
        # Check if new session needed
        if usage['needs_new_session']:
            logger.warning(f"⚠️ Context at {usage['percentage_display']} - Creating new session")
            
            # First compress
            compressed_msgs, compression_info = await self.compress_conversation(
                messages, model, target_reduction=0.7
            )
            
            # Create new session
            new_session = await self.create_new_session_with_context(
                session_id,
                compressed_msgs,
                compression_info
            )
            
            result['action'] = 'new_session'
            result['messages'] = compressed_msgs
            result['new_session_id'] = new_session['session_id']
            result['compression_info'] = compression_info
            result['warning'] = f"🔄 Context full. Started new session with preserved context."
            
        # Check if compression needed (but not new session)
        elif usage['needs_compression']:
            logger.info(f"ℹ️ Context at {usage['percentage_display']} - Compressing")
            
            compressed_msgs, compression_info = await self.compress_conversation(
                messages, model, target_reduction=0.5
            )
            
            result['action'] = 'compress'
            result['messages'] = compressed_msgs
            result['compression_info'] = compression_info
            result['warning'] = f"🗜️ Compressed conversation to save context space."
        
        return result


# Global instance
context_manager = ContextWindowManager()
