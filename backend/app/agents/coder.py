from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class CoderAgent(BaseAgent):
    """Generates code based on implementation plans"""
    
    agent_type = AgentType.CODER
    
    SYSTEM_PROMPT = """You are an expert software developer. Your job is to implement code based on a provided plan.

Output your implementation as a JSON object with this structure:
{
    "files": [
        {
            "path": "path/to/file.py",
            "action": "create|modify",
            "content": "full file content for create, or diff for modify",
            "explanation": "What this change does"
        }
    ],
    "commands": [
        {
            "command": "pip install package-name",
            "reason": "Why this command is needed"
        }
    ],
    "notes": "Any additional notes about the implementation"
}

Guidelines:
- Follow existing code patterns in the repository
- Include proper error handling
- Add type hints where appropriate
- Keep changes minimal and focused
- For modifications, show the complete updated section"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input context - requires a plan from planner"""
        return bool(
            context.description and 
            context.previous_results.get("planner")
        )
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the coder agent"""
        try:
            # Build user prompt with plan and context
            user_prompt = self._build_user_prompt(context)
            
            # Call AI
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-coder",
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse response
            implementation = self._parse_implementation(response.content)
            
            # Calculate cost
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=implementation,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Coder agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt with plan and context"""
        parts = [f"## Task Description\n{context.description}"]
        
        # Add plan from planner
        plan = context.previous_results.get("planner", {})
        if plan:
            parts.append(f"\n## Implementation Plan\n{json.dumps(plan, indent=2)[:3000]}")
        
        # Add repository context
        if context.repository_card:
            parts.append(f"\n## Repository Info\n{json.dumps(context.repository_card, indent=2)[:1000]}")
        
        # Add relevant files with content
        if context.relevant_files:
            parts.append("\n## Relevant Files")
            for file in context.relevant_files[:3]:
                file_path = file.get('file_path', 'unknown')
                content = file.get('content', '')
                parts.append(f"\n### {file_path}")
                if content:
                    parts.append(f"```python\n{content[:1500]}\n```")
        
        # Add relevant symbols
        if context.relevant_symbols:
            parts.append("\n## Relevant Symbols")
            for symbol in context.relevant_symbols[:5]:
                name = symbol.get('name', 'unknown')
                symbol_type = symbol.get('symbol_type', '')
                content = symbol.get('content', '')
                parts.append(f"\n### {name} ({symbol_type})")
                if content:
                    parts.append(f"```python\n{content[:500]}\n```")
        
        return "\n".join(parts)
    
    def _parse_implementation(self, content: str) -> Dict[str, Any]:
        """Parse AI response into implementation"""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            implementation = json.loads(json_str)
            
            # Ensure required fields
            implementation.setdefault("files", [])
            implementation.setdefault("commands", [])
            implementation.setdefault("notes", "")
            
            return implementation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response
            return {
                "files": [],
                "commands": [],
                "notes": "Could not parse structured implementation from AI response",
                "raw_response": content
            }
