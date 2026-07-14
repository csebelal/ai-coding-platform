from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Researches codebase patterns and gathers context for other agents"""
    
    agent_type = AgentType.RESEARCHER
    
    SYSTEM_PROMPT = """You are a codebase researcher. Your job is to analyze the existing codebase and gather relevant context for the implementation.

Output your research as a JSON object with this structure:
{
    "codebase_patterns": [
        {
            "pattern": "Name of the pattern found",
            "description": "How it works",
            "examples": ["file.py:42"]
        }
    ],
    "relevant_files": [
        {
            "path": "path/to/file.py",
            "relevance": "high|medium|low",
            "reason": "Why this file is relevant"
        }
    ],
    "conventions": ["coding conventions observed in the codebase"],
    "dependencies": ["existing libraries and utilities to reuse"],
    "recommendations": ["suggestions for implementation based on codebase patterns"]
}

Focus on:
- Existing patterns that should be followed
- Code that can be reused or extended
- Potential conflicts or dependencies
- Coding conventions and style"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input"""
        return bool(context.description and len(context.description) > 5)
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the researcher agent"""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-chat",
                temperature=0.2,
                max_tokens=2000
            )
            
            research = self._parse_research(response.content)
            
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=research,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Researcher agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"## Task Description\n{context.description}"]
        
        if context.repository_card:
            parts.append(f"\n## Repository Info\n{json.dumps(context.repository_card, indent=2)[:1000]}")
        
        if context.relevant_files:
            parts.append("\n## Relevant Files")
            for file in context.relevant_files[:5]:
                file_path = file.get('file_path', 'unknown')
                content = file.get('content', '')
                parts.append(f"\n### {file_path}")
                if content:
                    parts.append(f"```\n{content[:1000]}\n```")
        
        if context.relevant_symbols:
            parts.append("\n## Relevant Symbols")
            for symbol in context.relevant_symbols[:10]:
                name = symbol.get('name', 'unknown')
                symbol_type = symbol.get('symbol_type', '')
                content = symbol.get('content', '')
                parts.append(f"\n### {name} ({symbol_type})")
                if content:
                    parts.append(f"```python\n{content[:500]}\n```")
        
        return "\n".join(parts)
    
    def _parse_research(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            research = json.loads(json_str)
            research.setdefault("codebase_patterns", [])
            research.setdefault("relevant_files", [])
            research.setdefault("conventions", [])
            research.setdefault("dependencies", [])
            research.setdefault("recommendations", [])
            
            return research
            
        except json.JSONDecodeError:
            return {
                "codebase_patterns": [],
                "relevant_files": [],
                "conventions": [],
                "dependencies": [],
                "recommendations": [],
                "raw_response": content
            }
