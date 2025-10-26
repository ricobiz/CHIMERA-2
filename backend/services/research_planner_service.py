import os
import logging
from openai import OpenAI
from typing import Dict, List
import httpx

logger = logging.getLogger(__name__)

class ResearchPlannerService:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        self.research_prompt = """You are an expert Research Planner. Your role is to investigate and analyze the CURRENT state of technology and best practices BEFORE starting any complex development task.

**User Request:** {user_request}

**Your Task:**
1. **Analyze Complexity**: Determine if this task requires research (anything beyond a simple calculator/todo app needs research)
2. **Identify Research Areas**: What aspects need investigation?
   - Current best practices and patterns
   - Modern technology stacks and libraries (latest versions)
   - Recent market solutions and competitors
   - Common pitfalls and how to avoid them
   - Performance and scalability considerations
   - Security best practices
   - UI/UX trends for this type of application

3. **Generate Search Queries**: Create 3-5 specific search queries to find the most relevant and up-to-date information
   Example queries:
   - "best practices for [feature] 2025"
   - "modern [technology] stack for [app type]"
   - "latest [framework] version features"
   - "[app type] implementation guide 2025"

4. **Research Report Structure**: After gathering information, provide:
   - **Recommended Tech Stack**: Specific libraries/frameworks with versions
   - **Key Implementation Patterns**: Modern approaches that work best
   - **Common Mistakes to Avoid**: Based on recent discussions
   - **Performance Tips**: Latest optimization techniques
   - **Security Considerations**: Current best practices
   - **Alternative Approaches**: Different ways to solve the problem

**Output Format:**
```json
{{
  "complexity_assessment": "simple|moderate|complex",
  "requires_research": true/false,
  "research_queries": [
    "specific search query 1",
    "specific search query 2",
    "specific search query 3"
  ],
  "reasoning": "Why research is needed for this task"
}}
```

Be specific and actionable. Focus on CURRENT (2025) information, not outdated knowledge."""

        self.synthesis_prompt = """You are an expert Research Synthesizer. You've gathered information from web searches. Now synthesize it into actionable recommendations.

**Original User Request:** {user_request}

**Research Results:**
{research_results}

**Your Task:**
Synthesize the research into a comprehensive development guide:

1. **Recommended Tech Stack**
   - Frontend: specific libraries/frameworks (with versions)
   - Backend: frameworks, databases (with versions)
   - Additional tools: testing, deployment, etc.

2. **Key Implementation Patterns**
   - Best practices from research
   - Code patterns and architectures
   - State management approaches

3. **Step-by-Step Implementation Guide**
   - High-level phases
   - Important considerations for each phase
   - Integration points

4. **Common Pitfalls to Avoid**
   - Based on research findings
   - How to prevent them

5. **Performance & Security**
   - Optimization techniques
   - Security best practices

6. **Modern Alternatives**
   - Different approaches found in research
   - Pros/cons of each

**Output Format:**
Provide a detailed markdown report that a developer can follow. Be specific, cite recent sources when relevant, and focus on 2025 best practices.
"""

    async def analyze_task_complexity(self, user_request: str, model: str = None) -> Dict:
        """Analyze if task requires research and generate search queries"""
        try:
            selected_model = model or "anthropic/claude-3.5-sonnet"
            
            prompt = self.research_prompt.format(user_request=user_request)
            
            logger.info(f"Analyzing task complexity with model: {selected_model}")
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON from response
            import json
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(result_text)
            
            # Add usage info
            analysis["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            logger.info(f"Task complexity: {analysis.get('complexity_assessment')}, requires_research: {analysis.get('requires_research')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing task complexity: {str(e)}")
            # Return simple fallback
            return {
                "complexity_assessment": "simple",
                "requires_research": False,
                "research_queries": [],
                "reasoning": "Error in analysis, proceeding without research",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    async def perform_web_research(self, queries: List[str]) -> List[Dict]:
        """Perform web searches for research queries"""
        research_results = []
        
        # Use a simple web search approach (can be enhanced with better search API)
        for query in queries[:5]:  # Limit to 5 queries
            try:
                logger.info(f"Searching web for: {query}")
                
                # Use a search API or service (placeholder for now)
                # In production, integrate with Google Search API, Bing API, or similar
                # For now, we'll simulate with a note that actual search would happen here
                
                result = {
                    "query": query,
                    "summary": f"Web search results for: {query}",
                    "sources": []
                }
                
                research_results.append(result)
                
            except Exception as e:
                logger.error(f"Error searching for '{query}': {str(e)}")
                continue
        
        return research_results

    async def synthesize_research(
        self, 
        user_request: str, 
        research_results: List[Dict],
        model: str = None
    ) -> Dict:
        """Synthesize research results into actionable development guide"""
        try:
            selected_model = model or "anthropic/claude-3.5-sonnet"
            
            # Format research results
            results_text = "\n\n".join([
                f"Query: {r['query']}\nFindings: {r['summary']}"
                for r in research_results
            ])
            
            prompt = self.synthesis_prompt.format(
                user_request=user_request,
                research_results=results_text
            )
            
            logger.info(f"Synthesizing research with model: {selected_model}")
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            synthesis = response.choices[0].message.content
            
            logger.info("Research synthesis completed")
            
            return {
                "research_report": synthesis,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing research: {str(e)}")
            return {
                "research_report": "Error synthesizing research. Proceeding with standard knowledge.",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    async def conduct_full_research(self, user_request: str, model: str = None) -> Dict:
        """Full research pipeline: analyze → search → synthesize"""
        try:
            # Step 1: Analyze task complexity
            analysis = await self.analyze_task_complexity(user_request, model)
            
            # If research not needed, return early
            if not analysis.get("requires_research"):
                return {
                    "requires_research": False,
                    "complexity": analysis.get("complexity_assessment"),
                    "reasoning": analysis.get("reasoning"),
                    "research_report": None,
                    "total_usage": analysis.get("usage")
                }
            
            # Step 2: Perform web research
            queries = analysis.get("research_queries", [])
            research_results = await self.perform_web_research(queries)
            
            # Step 3: Synthesize findings
            synthesis = await self.synthesize_research(user_request, research_results, model)
            
            # Combine usage
            total_usage = {
                "prompt_tokens": analysis["usage"]["prompt_tokens"] + synthesis["usage"]["prompt_tokens"],
                "completion_tokens": analysis["usage"]["completion_tokens"] + synthesis["usage"]["completion_tokens"],
                "total_tokens": analysis["usage"]["total_tokens"] + synthesis["usage"]["total_tokens"]
            }
            
            return {
                "requires_research": True,
                "complexity": analysis.get("complexity_assessment"),
                "reasoning": analysis.get("reasoning"),
                "research_queries": queries,
                "research_report": synthesis["research_report"],
                "total_usage": total_usage
            }
            
        except Exception as e:
            logger.error(f"Error in full research pipeline: {str(e)}")
            return {
                "requires_research": False,
                "complexity": "unknown",
                "reasoning": f"Error: {str(e)}",
                "research_report": None,
                "total_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

research_planner_service = ResearchPlannerService()
