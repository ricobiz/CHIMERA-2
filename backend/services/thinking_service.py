"""
AI Thinking & Reasoning Service
Даёт агенту способность МЫСЛИТЬ перед ответом
Приоритет: честность, точность, верификация
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
import httpx
from services.openrouter_service import openrouter_service
# from services.ai_memory_service import memory_service  # Disabled for MVP

logger = logging.getLogger(__name__)

class ThinkingService:
    """
    Сервис глубокого мышления для AI агента
    
    Принципы:
    1. НИКОГДА не врать и не придумывать
    2. Признавать незнание
    3. Верифицировать через внешние источники
    4. Рефлексировать перед ответом
    5. Быть партнёром, не предателем доверия
    """
    
    def __init__(self):
        self.thinking_model = "anthropic/claude-3.5-sonnet"  # Лучшая модель для reasoning
        self.max_thinking_depth = 3  # Глубина размышлений
    
    async def deep_think(
        self,
        user_query: str,
        context: str = "",
        memories: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Глубокое размышление перед ответом
        
        Returns:
            {
                'thinking_process': str,  # Внутренний монолог
                'confidence': float,      # 0.0 - 1.0
                'needs_verification': bool,
                'uncertainties': List[str],
                'search_queries': List[str],
                'final_reasoning': str
            }
        """
        logger.info(f"🧠 Starting deep thinking for: '{user_query[:50]}'...")
        
        thinking_result = {
            'thinking_process': [],
            'confidence': 0.0,
            'needs_verification': False,
            'uncertainties': [],
            'search_queries': [],
            'final_reasoning': ''
        }
        
        # Step 1: Internal reflection
        step1 = await self._internal_reflection(user_query, context, memories)
        thinking_result['thinking_process'].append({
            'step': 'reflection',
            'content': step1['reflection']
        })
        thinking_result['uncertainties'].extend(step1['uncertainties'])
        
        # Step 2: Knowledge assessment
        step2 = await self._assess_knowledge(user_query, step1)
        thinking_result['thinking_process'].append({
            'step': 'knowledge_assessment',
            'content': step2['assessment']
        })
        thinking_result['confidence'] = step2['confidence']
        thinking_result['needs_verification'] = step2['needs_verification']
        
        # Step 3: External verification if needed
        if step2['needs_verification']:
            step3 = await self._verify_with_external_sources(
                user_query, 
                step2['uncertain_points']
            )
            thinking_result['thinking_process'].append({
                'step': 'external_verification',
                'content': step3['verification']
            })
            thinking_result['search_queries'] = step3['queries']
            thinking_result['confidence'] = step3['updated_confidence']
        
        # Step 4: Final reasoning synthesis
        final = await self._synthesize_reasoning(
            user_query,
            thinking_result['thinking_process'],
            thinking_result['confidence']
        )
        thinking_result['final_reasoning'] = final['reasoning']
        
        logger.info(f"✓ Thinking complete. Confidence: {thinking_result['confidence']:.2f}")
        
        return thinking_result
    
    async def _internal_reflection(
        self,
        query: str,
        context: str,
        memories: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """
        Внутренняя рефлексия: что я знаю? что не знаю?
        """
        memory_context = ""
        if memories:
            memory_context = "\n".join([f"- {m['memory']}" for m in memories[:3]])
        
        reflection_prompt = f"""You are performing internal reflection before answering.

User Query: {query}

Context: {context}

Your Memories:
{memory_context}

Reflect deeply and honestly:
1. What do I DEFINITELY know about this?
2. What am I UNCERTAIN about?
3. What might I be WRONG about?
4. What do I need to VERIFY?

Be brutally honest. It's better to say "I don't know" than to guess.

Format your response as:
KNOWN: [what you're certain about]
UNCERTAIN: [what you're not sure about]
NEED_TO_VERIFY: [what requires checking]"""
        
        try:
            response = await openrouter_service.chat_completion(
                messages=[{"role": "user", "content": reflection_prompt}],
                model=self.thinking_model,
                temperature=0.3  # Lower temp for more focused thinking
            )
            
            reflection = response['choices'][0]['message']['content']
            
            # Parse uncertainties
            uncertainties = []
            if 'UNCERTAIN:' in reflection:
                uncertain_section = reflection.split('UNCERTAIN:')[1].split('NEED_TO_VERIFY:')[0]
                uncertainties = [u.strip() for u in uncertain_section.split('\n') if u.strip()]
            
            return {
                'reflection': reflection,
                'uncertainties': uncertainties
            }
            
        except Exception as e:
            logger.error(f"Reflection error: {str(e)}")
            return {
                'reflection': "Unable to perform deep reflection",
                'uncertainties': []
            }
    
    async def _assess_knowledge(
        self,
        query: str,
        reflection: Dict
    ) -> Dict[str, Any]:
        """
        Оценить уровень знаний и необходимость верификации
        """
        assessment_prompt = f"""Based on this internal reflection, assess your knowledge confidence.

User Query: {query}

Your Reflection:
{reflection['reflection']}

Provide:
1. Confidence score (0.0 to 1.0) - be CONSERVATIVE
2. Do you need external verification? (yes/no)
3. What specific points need verification?

Rules:
- If confidence < 0.7 → MUST verify
- If making factual claims → MUST verify
- If uncertain about details → MUST verify
- If it's opinion/creative → verification not needed

Format:
CONFIDENCE: [0.0-1.0]
NEEDS_VERIFICATION: [yes/no]
UNCERTAIN_POINTS: [list specific things to verify]"""
        
        try:
            response = await openrouter_service.chat_completion(
                messages=[{"role": "user", "content": assessment_prompt}],
                model=self.thinking_model,
                temperature=0.2
            )
            
            assessment = response['choices'][0]['message']['content']
            
            # Parse confidence
            confidence = 0.5  # Default conservative
            if 'CONFIDENCE:' in assessment:
                conf_line = [l for l in assessment.split('\n') if 'CONFIDENCE:' in l][0]
                try:
                    confidence = float(conf_line.split('CONFIDENCE:')[1].strip())
                except:
                    pass
            
            # Parse verification need
            needs_verification = 'yes' in assessment.lower() and 'needs_verification: yes' in assessment.lower()
            
            # Parse uncertain points
            uncertain_points = []
            if 'UNCERTAIN_POINTS:' in assessment:
                points_section = assessment.split('UNCERTAIN_POINTS:')[1]
                uncertain_points = [p.strip() for p in points_section.split('\n') if p.strip() and p.strip().startswith('-')]
            
            return {
                'assessment': assessment,
                'confidence': confidence,
                'needs_verification': needs_verification or confidence < 0.7,
                'uncertain_points': uncertain_points
            }
            
        except Exception as e:
            logger.error(f"Assessment error: {str(e)}")
            return {
                'assessment': "Unable to assess knowledge",
                'confidence': 0.3,  # Very low when error
                'needs_verification': True,
                'uncertain_points': []
            }
    
    async def _verify_with_external_sources(
        self,
        query: str,
        uncertain_points: List[str]
    ) -> Dict[str, Any]:
        """
        Верификация через внешние источники (web search)
        """
        logger.info("🔍 Performing external verification...")
        
        # Generate search queries
        queries = await self._generate_search_queries(query, uncertain_points)
        
        # Perform web searches
        search_results = []
        for search_query in queries[:3]:  # Max 3 searches
            try:
                result = await self._web_search(search_query)
                search_results.append({
                    'query': search_query,
                    'results': result
                })
            except Exception as e:
                logger.error(f"Search error for '{search_query}': {str(e)}")
        
        # Analyze search results
        verification_prompt = f"""You performed web searches to verify your knowledge.

Original Query: {query}

Uncertain Points:
{chr(10).join(f'- {p}' for p in uncertain_points)}

Search Results:
{self._format_search_results(search_results)}

Based on these external sources:
1. What is now VERIFIED?
2. What remains UNCERTAIN?
3. Updated confidence level (0.0-1.0)?

Be honest: if sources don't help, say so."""
        
        try:
            response = await openrouter_service.chat_completion(
                messages=[{"role": "user", "content": verification_prompt}],
                model=self.thinking_model,
                temperature=0.2
            )
            
            verification = response['choices'][0]['message']['content']
            
            # Parse updated confidence
            updated_confidence = 0.7  # Default after verification
            if 'confidence' in verification.lower():
                # Try to extract confidence
                try:
                    import re
                    conf_match = re.search(r'confidence[:\s]+([0-9.]+)', verification.lower())
                    if conf_match:
                        updated_confidence = float(conf_match.group(1))
                except:
                    pass
            
            return {
                'verification': verification,
                'queries': [q['query'] for q in search_results],
                'updated_confidence': updated_confidence
            }
            
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            return {
                'verification': "Unable to verify with external sources",
                'queries': [],
                'updated_confidence': 0.5
            }
    
    async def _generate_search_queries(
        self,
        query: str,
        uncertain_points: List[str]
    ) -> List[str]:
        """
        Генерировать поисковые запросы для верификации
        """
        if not uncertain_points:
            return [query]
        
        # Simple heuristic-based query generation
        queries = []
        
        for point in uncertain_points[:3]:
            # Clean and format the point as a search query
            search_query = point.replace('-', '').strip()
            if search_query:
                queries.append(f"{query} {search_query}")
        
        return queries if queries else [query]
    
    async def _web_search(self, query: str) -> str:
        """
        Perform web search (placeholder - integrate with real search API)
        """
        # TODO: Integrate with actual web search API
        # For now, return placeholder
        logger.info(f"Web search: {query}")
        return f"[Search results for: {query}]"
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for LLM"""
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"Query {i}: {result['query']}")
            formatted.append(f"Results: {result['results']}")
        return "\n\n".join(formatted)
    
    async def _synthesize_reasoning(
        self,
        query: str,
        thinking_process: List[Dict],
        confidence: float
    ) -> Dict[str, str]:
        """
        Синтезировать финальное обоснование
        """
        process_summary = "\n\n".join([
            f"Step {i+1} ({step['step']}):\n{step['content']}"
            for i, step in enumerate(thinking_process)
        ])
        
        synthesis_prompt = f"""Synthesize your thinking process into a clear reasoning.

User Query: {query}

Your Thinking Process:
{process_summary}

Final Confidence: {confidence:.2f}

Create a concise reasoning that:
1. Explains your thought process
2. States what you're confident about
3. Admits what you're uncertain about
4. Explains why (if confidence < 0.8)

Be transparent and honest."""
        
        try:
            response = await openrouter_service.chat_completion(
                messages=[{"role": "user", "content": synthesis_prompt}],
                model=self.thinking_model,
                temperature=0.3
            )
            
            reasoning = response['choices'][0]['message']['content']
            
            return {'reasoning': reasoning}
            
        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}")
            return {'reasoning': f"Thinking process completed with {confidence:.0%} confidence"}
    
    def format_thinking_for_display(self, thinking_result: Dict) -> str:
        """
        Форматировать процесс мышления для показа пользователю
        """
        output = ["💭 **Internal Thinking Process:**\n"]
        
        for step in thinking_result['thinking_process']:
            output.append(f"**{step['step'].title()}:**")
            output.append(step['content'][:200] + "..." if len(step['content']) > 200 else step['content'])
            output.append("")
        
        output.append(f"**Final Confidence:** {thinking_result['confidence']:.0%}")
        
        if thinking_result['uncertainties']:
            output.append("\n**Remaining Uncertainties:**")
            for unc in thinking_result['uncertainties']:
                output.append(f"- {unc}")
        
        return "\n".join(output)


# Global instance
thinking_service = ThinkingService()
