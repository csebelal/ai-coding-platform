from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class DebuggerAgent(BaseAgent):
    """Debugs failing tests and fixes code issues"""
    
    agent_type = AgentType.DEBUGGER
    
    SYSTEM_PROMPT = """You are an expert debugger. Your job is to analyze failing tests or code issues and provide fixes.

Output your fix as a JSON object with this structure:
{
    "root_cause": "Description of what's causing the issue",
    "fixes": [
        {
            "file": "path/to/file.py",
            "action": "modify",
            "original_code": "the code that needs fixing",
            "fixed_code": "the corrected code",
            "explanation": "Why this fix works"
        }
    ],
    "additional_changes": [
        {
            "file": "path/to/file.py",
            "action": "modify",
            "content": "additional changes needed",
            "reason": "Why these changes are needed"
        }
    ],
    "verification_steps": ["steps to verify the fix works"]
}

Guidelines:
- Focus on the root cause, not symptoms
- Make minimal changes to fix the issue
- Preserve existing functionality
- Consider edge cases"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input - needs failed verification or review"""
        return bool(
            context.description and
            (context.previous_results.get("critic") or context.previous_results.get("verifier"))
        )
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the debugger agent"""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-coder",
                temperature=0.1,
                max_tokens=3000
            )
            
            fix = self._parse_fix(response.content)
            
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=fix,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Debugger agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"## Task Description\n{context.description}"]
        
        code = context.previous_results.get("coder", {})
        if code:
            parts.append(f"\n## Current Code\n{json.dumps(code, indent=2)[:3000]}")
        
        critic = context.previous_results.get("critic", {})
        if critic:
            parts.append(f"\n## Review Issues\n{json.dumps(critic, indent=2)[:2000]}")
        
        verifier = context.previous_results.get("verifier", {})
        if verifier:
            parts.append(f"\n## Verification Failures\n{json.dumps(verifier, indent=2)[:2000]}")
        
        tests = context.previous_results.get("test_writer", {})
        if tests:
            parts.append(f"\n## Tests\n{json.dumps(tests, indent=2)[:2000]}")
        
        return "\n".join(parts)
    
    def _parse_fix(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            fix = json.loads(json_str)
            fix.setdefault("root_cause", "")
            fix.setdefault("fixes", [])
            fix.setdefault("additional_changes", [])
            fix.setdefault("verification_steps", [])
            
            return fix
            
        except json.JSONDecodeError:
            return {
                "root_cause": "Could not parse structured fix",
                "fixes": [],
                "additional_changes": [],
                "verification_steps": [],
                "raw_response": content
            }
