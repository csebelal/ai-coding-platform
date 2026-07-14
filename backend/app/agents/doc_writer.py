from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class DocWriterAgent(BaseAgent):
    """Generates documentation for implemented features"""
    
    agent_type = AgentType.DOC_WRITER
    
    SYSTEM_PROMPT = """You are a technical writer. Your job is to generate clear, comprehensive documentation for the implemented feature.

Output your documentation as a JSON object with this structure:
{
    "readme_section": "Markdown content for the README",
    "api_docs": [
        {
            "endpoint": "POST /api/v1/resource",
            "description": "What this endpoint does",
            "request_body": "JSON schema of request",
            "response_body": "JSON schema of response",
            "examples": ["curl example"]
        }
    ],
    "inline_comments": [
        {
            "file": "path/to/file.py",
            "line": 42,
            "comment": "Explanation of complex logic"
        }
    ],
    "architecture_notes": "High-level architecture decisions and rationale"
}

Guidelines:
- Write for developers who are new to the codebase
- Include practical examples
- Explain "why" not just "what"
- Keep documentation close to the code"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input - needs completed implementation"""
        return bool(
            context.description and
            context.previous_results.get("coder")
        )
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the doc writer agent"""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-chat",
                temperature=0.2,
                max_tokens=2000
            )
            
            docs = self._parse_docs(response.content)
            
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=docs,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Doc writer agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"## Task Description\n{context.description}"]
        
        plan = context.previous_results.get("planner", {})
        if plan:
            parts.append(f"\n## Implementation Plan\n{json.dumps(plan, indent=2)[:2000]}")
        
        code = context.previous_results.get("coder", {})
        if code:
            parts.append(f"\n## Implementation Code\n{json.dumps(code, indent=2)[:3000]}")
        
        review = context.previous_results.get("critic", {})
        if review:
            parts.append(f"\n## Code Review\n{json.dumps(review, indent=2)[:1000]}")
        
        return "\n".join(parts)
    
    def _parse_docs(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            docs = json.loads(json_str)
            docs.setdefault("readme_section", "")
            docs.setdefault("api_docs", [])
            docs.setdefault("inline_comments", [])
            docs.setdefault("architecture_notes", "")
            
            return docs
            
        except json.JSONDecodeError:
            return {
                "readme_section": content[:2000],
                "api_docs": [],
                "inline_comments": [],
                "architecture_notes": "",
                "raw_response": content
            }
