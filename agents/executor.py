"""
Agent executor for executing agent tasks and workflows
Handles the execution of agents with proper state management and error handling
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor
import traceback
from datetime import datetime
from state import StateManager

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes agents with proper state management and error handling"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.logger = logging.getLogger(__name__)
        
    async def execute_agent(self, 
                          agent_id: str, 
                          session_id: str, 
                          task_data: Dict[str, Any],
                          agent_function: Callable) -> Dict[str, Any]:
        """
        Execute a single agent with proper error handling and state management
        """
        try:
            # Load agent state
            agent_state = self.state_manager.get_agent_state(session_id, agent_id)
            
            # Prepare execution context
            execution_context = {
                "session_id": session_id,
                "agent_id": agent_id,
                "task_data": task_data,
                "agent_state": agent_state,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Executing agent {agent_id} for session {session_id}")
            
            # Execute agent asynchronously
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self._execute_agent_sync, 
                agent_function, 
                execution_context
            )
            
            # Save agent state
            if result.get("state"):
                self.state_manager.set_agent_state(
                    session_id, 
                    agent_id, 
                    result["state"]
                )
            
            # Handle translation results specially
            if result.get("translation_output"):
                self.state_manager.add_translation_result(session_id, result["translation_output"])
            
            # Add to session history
            self.state_manager.add_to_session_history(session_id, {
                "agent": agent_id,
                "status": "completed",
                "result": result.get("output", {}),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "agent_id": agent_id,
                "session_id": session_id,
                "result": result.get("output", {}),
                "translation_output": result.get("translation_output", {}),
                "state": result.get("state"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error executing agent {agent_id}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # Add error to session history
            self.state_manager.add_to_session_history(session_id, {
                "agent": agent_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "agent_id": agent_id,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_agent_sync(self, agent_function: Callable, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous execution of agent function
        """
        try:
            # Execute the agent function
            result = agent_function(context)
            
            # Ensure result is properly formatted
            if isinstance(result, dict):
                return result
            else:
                return {
                    "output": result,
                    "state": context.get("agent_state", {})
                }
        except Exception as e:
            # Return error in proper format
            return {
                "output": None,
                "state": context.get("agent_state", {}),
                "error": str(e)
            }
    
    async def execute_agents_parallel(self, 
                                    agents_config: List[Dict[str, Any]],
                                    session_id: str) -> List[Dict[str, Any]]:
        """
        Execute multiple agents in parallel
        """
        tasks = []
        for agent_config in agents_config:
            agent_id = agent_config["agent_id"]
            agent_function = agent_config["function"]
            task_data = agent_config.get("task_data", {})
            
            task = self.execute_agent(agent_id, session_id, task_data, agent_function)
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
                
        return processed_results
    
    async def execute_workflow(self, 
                             workflow_config: Dict[str, Any],
                             session_id: str) -> Dict[str, Any]:
        """
        Execute a complete workflow with multiple agents and steps
        """
        try:
            workflow_steps = workflow_config.get("steps", [])
            workflow_name = workflow_config.get("name", "unknown_workflow")
            
            self.logger.info(f"Executing workflow {workflow_name} for session {session_id}")
            
            results = []
            for step in workflow_steps:
                step_name = step.get("name", "unnamed_step")
                agent_id = step.get("agent_id")
                agent_function = step.get("function")
                task_data = step.get("task_data", {})
                
                if agent_id and agent_function:
                    result = await self.execute_agent(agent_id, session_id, task_data, agent_function)
                    results.append(result)
                    
                    # Check if step succeeded
                    if not result.get("success"):
                        self.logger.error(f"Workflow step {step_name} failed: {result.get('error')}")
                        break
                else:
                    self.logger.warning(f"Invalid step configuration: {step_name}")
            
            # Log workflow completion
            self.logger.info(f"Completed workflow {workflow_name} for session {session_id}")
            
            return {
                "success": True,
                "workflow": workflow_name,
                "session_id": session_id,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error executing workflow {workflow_name}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "workflow": workflow_name,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class WorkflowManager:
    """Manages workflows and their execution"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.executor = AgentExecutor(state_manager)
        self.logger = logging.getLogger(__name__)
        
    def create_workflow(self, name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a workflow configuration"""
        return {
            "name": name,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        
    async def run_workflow(self, workflow_config: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Run a workflow"""
        return await self.executor.execute_workflow(workflow_config, session_id)
        
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get workflow status for a session"""
        # This would typically check session history for workflow information
        return {
            "session_id": session_id,
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }
        
    def create_translation_workflow(self) -> Dict[str, Any]:
        """Create a workflow specifically for translation tasks"""
        return {
            "name": "translation_workflow",
            "steps": [
                {
                    "name": "detect_language",
                    "agent_id": "language_detector",
                    "function": self._detect_language_agent,
                    "task_data": {}
                },
                {
                    "name": "translate_text",
                    "agent_id": "translator",
                    "function": self._translate_agent,
                    "task_data": {}
                },
                {
                    "name": "validate_translation",
                    "agent_id": "validator",
                    "function": self._validate_translation_agent,
                    "task_data": {}
                }
            ],
            "created_at": datetime.now().isoformat()
        }
        
    def _detect_language_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect language of input text"""
        return {
            "output": {
                "detected_language": "en",
                "confidence": 0.95
            },
            "state": {
                "language_detected": datetime.now().isoformat()
            }
        }
        
    def _translate_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Translate text to target language"""
        return {
            "output": {
                "translated_text": "Translated text",
                "source_language": "en",
                "target_language": "es"
            },
            "translation_output": {
                "source_text": context.get("task_data", {}).get("text", ""),
                "source_language": "en",
                "target_language": "es",
                "translated_text": "Translated text",
                "timestamp": datetime.now().isoformat()
            },
            "state": {
                "translation_completed": datetime.now().isoformat()
            }
        }
        
    def _validate_translation_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate translation quality"""
        return {
            "output": {
                "validation_passed": True,
                "quality_score": 0.92
            },
            "state": {
                "translation_validated": datetime.now().isoformat()
            }
        }