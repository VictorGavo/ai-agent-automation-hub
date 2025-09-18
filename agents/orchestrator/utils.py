# agents/orchestrator/utils.py  
"""Utility classes for the Orchestrator Agent"""
import re
import os
import logging
from typing import Dict, List, Optional, Any
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

class TaskValidator:
    """Validates and analyzes task descriptions"""
    
    def __init__(self):
        self.min_description_length = 10
        self.max_description_length = 2000
        self.forbidden_keywords = ["hack", "exploit", "crack", "illegal"]
    
    async def validate_description(self, description: str) -> Dict[str, Any]:
        """Validate task description for basic requirements"""
        if not description or len(description.strip()) < self.min_description_length:
            return {
                "valid": False,
                "reason": f"Description must be at least {self.min_description_length} characters"
            }
        
        if len(description) > self.max_description_length:
            return {
                "valid": False,
                "reason": f"Description too long (max {self.max_description_length} characters)"
            }
        
        # Check for forbidden content
        description_lower = description.lower()
        for keyword in self.forbidden_keywords:
            if keyword in description_lower:
                return {
                    "valid": False,
                    "reason": f"Description contains prohibited content: {keyword}"
                }
        
        return {"valid": True}
    
    def estimate_complexity(self, description: str) -> float:
        """Estimate task complexity in hours (1-4 hour limit)"""
        # Simple heuristic based on keywords and length
        complexity_keywords = {
            "simple": 0.5, "basic": 0.5, "quick": 0.5,
            "create": 1.0, "build": 1.5, "implement": 2.0,
            "complex": 2.5, "advanced": 3.0, "comprehensive": 3.5,
            "refactor": 2.0, "optimize": 1.5, "fix": 1.0,
            "database": 1.5, "api": 1.0, "frontend": 2.0,
            "testing": 1.0, "documentation": 0.5
        }
        
        base_hours = 1.0
        description_lower = description.lower()
        
        for keyword, hours in complexity_keywords.items():
            if keyword in description_lower:
                base_hours = max(base_hours, hours)
        
        # Adjust based on length
        if len(description) > 500:
            base_hours *= 1.2
        elif len(description) < 100:
            base_hours *= 0.8
        
        # Cap at 4 hours (dev bible rule)
        return min(base_hours, 4.0)

class ClaudeClient:
    """Client for interacting with Claude API"""
    
    def __init__(self):
        self.client = None
        self.api_key = os.getenv("CLAUDE_API_KEY")
    
    async def initialize(self):
        """Initialize Claude client"""
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not found - Claude integration disabled")
            return
        
        try:
            self.client = AsyncAnthropic(api_key=self.api_key)
            logger.info("Claude client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
    
    async def analyze_task(self, description: str) -> Dict[str, Any]:
        """Analyze task description and determine if clarification is needed"""
        if not self.client:
            # Fallback analysis without Claude
            return self._fallback_analysis(description)
        
        try:
            system_prompt = """You are an AI development task analyzer. Analyze the given task description and determine:

1. If the task is clear enough to implement immediately, or if clarification is needed
2. What category it belongs to (backend, database, frontend, testing, documentation, deployment, general)
3. Estimated hours (1-4 max, following the 4-hour rule)
4. Success criteria
5. If clarification is needed, provide 1-5 specific questions

Respond in JSON format:
{
  "needs_clarification": boolean,
  "questions": ["question1", "question2"],
  "category": "backend|database|frontend|testing|documentation|deployment|general",
  "estimated_hours": float,
  "title": "short descriptive title",
  "success_criteria": ["criteria1", "criteria2"],
  "requires_approval": boolean,
  "metadata": {"key": "value"}
}"""
            
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    "role": "user", 
                    "content": f"Analyze this development task: {description}"
                }]
            )
            
            import json
            analysis = json.loads(response.content[0].text)
            
            # Validate and sanitize response
            return self._validate_analysis(analysis, description)
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._fallback_analysis(description)
    
    async def process_clarification(self, original_description: str, questions: List[str], answers: List[str]) -> Dict[str, Any]:
        """Process clarification answers and provide final task analysis"""
        if not self.client:
            return self._fallback_clarification_analysis(original_description, answers)
        
        try:
            clarification_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
            
            system_prompt = """Based on the original task and clarification, provide final task analysis in JSON format:
{
  "category": "backend|database|frontend|testing|documentation|deployment|general",
  "estimated_hours": float,
  "title": "updated title based on clarification",
  "success_criteria": ["specific criteria"],
  "requires_approval": boolean,
  "metadata": {"implementation_notes": "specific guidance"}
}"""
            
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Original task: {original_description}\n\nClarification:\n{clarification_text}"
                }]
            )
            
            import json
            analysis = json.loads(response.content[0].text)
            return self._validate_analysis(analysis, original_description)
            
        except Exception as e:
            logger.error(f"Claude clarification processing failed: {e}")
            return self._fallback_clarification_analysis(original_description, answers)
    
    def _fallback_analysis(self, description: str) -> Dict[str, Any]:
        """Fallback analysis when Claude is unavailable"""
        validator = TaskValidator()
        
        # Simple keyword-based category detection
        description_lower = description.lower()
        if any(word in description_lower for word in ["api", "endpoint", "flask", "route", "backend"]):
            category = "backend"
        elif any(word in description_lower for word in ["database", "sql", "table", "schema", "postgres"]):
            category = "database"
        elif any(word in description_lower for word in ["ui", "frontend", "html", "css", "javascript", "template"]):
            category = "frontend"
        elif any(word in description_lower for word in ["test", "testing", "pytest", "unit test"]):
            category = "testing"
        elif any(word in description_lower for word in ["docs", "documentation", "readme", "comments"]):
            category = "documentation"
        elif any(word in description_lower for word in ["deploy", "deployment", "docker", "container"]):
            category = "deployment"
        else:
            category = "general"
        
        estimated_hours = validator.estimate_complexity(description)
        
        # Simple heuristic for clarification needs
        needs_clarification = len(description.split()) < 10 or "?" in description
        
        questions = []
        if needs_clarification:
            if "create" in description_lower or "build" in description_lower:
                questions.append("What specific features should be included?")
                questions.append("Are there any technical requirements or constraints?")
            if "fix" in description_lower:
                questions.append("What exactly is the problem or bug?")
                questions.append("How should the fix be tested?")
        
        return {
            "needs_clarification": needs_clarification,
            "questions": questions,
            "category": category,
            "estimated_hours": estimated_hours,
            "title": description[:50] + "..." if len(description) > 50 else description,
            "success_criteria": [
                "Implementation completed according to specification",
                "All tests pass",
                "Code follows project standards"
            ],
            "requires_approval": True,
            "metadata": {"analysis_method": "fallback_heuristic"}
        }
    
    def _fallback_clarification_analysis(self, description: str, answers: List[str]) -> Dict[str, Any]:
        """Fallback clarification analysis"""
        base_analysis = self._fallback_analysis(description)
        
        # Update based on clarification answers
        combined_text = f"{description} {' '.join(answers)}"
        validator = TaskValidator()
        
        return {
            "category": base_analysis["category"],
            "estimated_hours": validator.estimate_complexity(combined_text),
            "title": base_analysis["title"],
            "success_criteria": base_analysis["success_criteria"] + [
                "Clarification requirements satisfied"
            ],
            "requires_approval": True,
            "metadata": {
                "analysis_method": "fallback_clarification",
                "clarification_provided": True
            }
        }
    
    def _validate_analysis(self, analysis: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Validate and sanitize Claude analysis response"""
        # Ensure required fields exist with defaults
        defaults = {
            "needs_clarification": False,
            "questions": [],
            "category": "general",
            "estimated_hours": 1.0,
            "title": description[:50],
            "success_criteria": ["Task completed successfully"],
            "requires_approval": True,
            "metadata": {}
        }
        
        for key, default_value in defaults.items():
            if key not in analysis:
                analysis[key] = default_value
        
        # Validate constraints
        analysis["estimated_hours"] = max(0.1, min(4.0, analysis["estimated_hours"]))
        
        if analysis["category"] not in ["backend", "database", "frontend", "testing", "documentation", "deployment", "general"]:
            analysis["category"] = "general"
        
        # Limit questions to 5 max
        if len(analysis["questions"]) > 5:
            analysis["questions"] = analysis["questions"][:5]
        
        return analysis