from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class CriticAgent(BaseAgent):
    """Reviews code quality, style, and suggests improvements"""
    
    agent_type = AgentType.CRITIC
    
    SYSTEM_PROMPT = """You are a senior code reviewer. Your job is to review code for quality, correctness, and best practices.

Output your review as a JSON object with this structure:
{
    "overall_quality": "good|needs_improvement|poor",
    "approved": true,
    "issues": [
        {
            "severity": "critical|major|minor",
            "file": "path/to/file.py",
            "line": 42,
            "description": "What the issue is",
            "suggestion": "How to fix it"
        }
    ],
    "positive_aspects": ["things done well"],
    "summary": "Overall assessment of the code",
    "required_changes": ["list of changes that must be made before approval"]
}

Review criteria:
- Code correctness and logic
- Error handling completeness
- Security concerns
- Performance implications
- Code style and readability
- Test coverage adequacy
- Documentation completeness"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input - needs code from coder agent"""
        return bool(
            context.description and
            context.previous_results.get("coder")
        )
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the critic agent"""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-chat",
                temperature=0.1,
                max_tokens=2000
            )
            
            review = self._parse_review(response.content)
            
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=review.get("approved", False),
                data=review,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Critic agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"## Task Description\n{context.description}"]
        
        code = context.previous_results.get("coder", {})
        if code:
            parts.append(f"\n## Code to Review\n{json.dumps(code, indent=2)[:4000]}")
        
        tests = context.previous_results.get("test_writer", {})
        if tests:
            parts.append(f"\n## Tests\n{json.dumps(tests, indent=2)[:2000]}")
        
        if context.relevant_files:
            parts.append("\n## Existing Codebase Context")
            for file in context.relevant_files[:3]:
                parts.append(f"\n### {file.get('file_path', 'unknown')}")
                if file.get("content"):
                    parts.append(f"```python\n{file['content'][:500]}\n```")
        
        return "\n".join(parts)
    
    def _parse_review(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            review = json.loads(json_str)
            review.setdefault("overall_quality", "needs_improvement")
            review.setdefault("approved", False)
            review.setdefault("issues", [])
            review.setdefault("positive_aspects", [])
            review.setdefault("summary", "")
            review.setdefault("required_changes", [])
            
            return review
            
        except json.JSONDecodeError:
            return {
                "overall_quality": "needs_improvement",
                "approved": False,
                "issues": [],
                "positive_aspects": [],
                "summary": "Could not parse structured review from AI response",
                "required_changes": [],
                "raw_response": content
            }
