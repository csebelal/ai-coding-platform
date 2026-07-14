from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """Creates implementation plans from task descriptions"""
    
    agent_type = AgentType.PLANNER
    
    SYSTEM_PROMPT = """You are a senior software architect. Your job is to analyze a task description and create a detailed implementation plan.

Output your plan as a JSON object with this structure:
{
    "summary": "Brief summary of what will be implemented",
    "files_to_modify": [
        {
            "path": "path/to/file.py",
            "action": "create|modify|delete",
            "reason": "Why this file needs to change"
        }
    ],
    "implementation_steps": [
        {
            "step": 1,
            "description": "What to do",
            "files": ["file1.py", "file2.py"],
            "details": "Detailed instructions"
        }
    ],
    "dependencies": ["list of any new packages needed"],
    "risks": ["potential issues to watch out for"],
    "estimated_complexity": "low|medium|high"
}

Be specific about file paths, function names, and implementation details. Reference existing code patterns when possible."""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input context"""
        return bool(context.description and len(context.description) > 10)
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the planner agent"""
        try:
            # Build user prompt with context
            user_prompt = self._build_user_prompt(context)
            
            # Call AI
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-chat",
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse response
            plan = self._parse_plan(response.content)
            
            # Calculate cost
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=plan,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Planner agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt with context"""
        parts = [f"## Task Description\n{context.description}"]
        
        # Add repository context
        if context.repository_card:
            parts.append(f"\n## Repository Info\n{json.dumps(context.repository_card, indent=2)[:1000]}")
        
        # Add relevant files
        if context.relevant_files:
            parts.append("\n## Relevant Files")
            for file in context.relevant_files[:3]:
                parts.append(f"- {file.get('file_path', 'unknown')}")
        
        # Add relevant symbols
        if context.relevant_symbols:
            parts.append("\n## Relevant Symbols")
            for symbol in context.relevant_symbols[:5]:
                parts.append(f"- {symbol.get('name', 'unknown')} ({symbol.get('symbol_type', '')})")
        
        return "\n".join(parts)
    
    def _parse_plan(self, content: str) -> Dict[str, Any]:
        """Parse AI response into plan"""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            plan = json.loads(json_str)
            
            # Ensure required fields
            plan.setdefault("summary", "")
            plan.setdefault("files_to_modify", [])
            plan.setdefault("implementation_steps", [])
            plan.setdefault("dependencies", [])
            plan.setdefault("risks", [])
            plan.setdefault("estimated_complexity", "medium")
            
            return plan
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response
            return {
                "summary": content[:500],
                "files_to_modify": [],
                "implementation_steps": [{"step": 1, "description": content[:1000], "files": [], "details": ""}],
                "dependencies": [],
                "risks": ["Could not parse structured plan from AI response"],
                "estimated_complexity": "medium",
                "raw_response": content
            }
