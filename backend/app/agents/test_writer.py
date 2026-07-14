from typing import Dict, Any, List
import json
import logging

from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class TestWriterAgent(BaseAgent):
    """Generates tests based on implementation plans and code"""
    
    agent_type = AgentType.TEST_WRITER
    
    SYSTEM_PROMPT = """You are an expert test engineer. Your job is to write comprehensive tests for the implementation.

Output your tests as a JSON object with this structure:
{
    "test_files": [
        {
            "path": "tests/test_feature.py",
            "content": "full test file content",
            "framework": "pytest",
            "explanation": "What these tests cover"
        }
    ],
    "test_plan": {
        "unit_tests": ["list of unit test descriptions"],
        "integration_tests": ["list of integration test descriptions"],
        "edge_cases": ["list of edge cases to test"]
    },
    "coverage_notes": "Notes on test coverage and what additional tests might be needed"
}

Guidelines:
- Use pytest as the default framework
- Include both happy path and error cases
- Mock external dependencies
- Use descriptive test names
- Include docstrings explaining what each test verifies"""
    
    def validate_input(self, context: AgentContext) -> bool:
        """Validate input - needs plan or code from previous agents"""
        return bool(
            context.description and
            (context.previous_results.get("planner") or context.previous_results.get("coder"))
        )
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the test writer agent"""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await ai_client.generate(
                system=self.SYSTEM_PROMPT,
                user=user_prompt,
                model="deepseek/deepseek-chat",
                temperature=0.2,
                max_tokens=3000
            )
            
            tests = self._parse_tests(response.content)
            
            cost = ai_client.calculate_cost(
                response.model,
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
            
            return AgentResult(
                success=True,
                data=tests,
                tokens_used=response.total_tokens,
                cost_usd=cost,
                metadata={"model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Test writer agent error: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"## Task Description\n{context.description}"]
        
        plan = context.previous_results.get("planner", {})
        if plan:
            parts.append(f"\n## Implementation Plan\n{json.dumps(plan, indent=2)[:3000]}")
        
        code = context.previous_results.get("coder", {})
        if code:
            parts.append(f"\n## Implementation Code\n{json.dumps(code, indent=2)[:3000]}")
        
        if context.relevant_files:
            parts.append("\n## Existing Code Patterns")
            for file in context.relevant_files[:3]:
                parts.append(f"\n### {file.get('file_path', 'unknown')}")
                if file.get("content"):
                    parts.append(f"```python\n{file['content'][:500]}\n```")
        
        return "\n".join(parts)
    
    def _parse_tests(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            tests = json.loads(json_str)
            tests.setdefault("test_files", [])
            tests.setdefault("test_plan", {"unit_tests": [], "integration_tests": [], "edge_cases": []})
            tests.setdefault("coverage_notes", "")
            
            return tests
            
        except json.JSONDecodeError:
            return {
                "test_files": [],
                "test_plan": {"unit_tests": [], "integration_tests": [], "edge_cases": []},
                "coverage_notes": "Could not parse structured tests from AI response",
                "raw_response": content
            }
