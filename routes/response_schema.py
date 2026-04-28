"""
Response schema definitions for API endpoints
Defines standardized response formats for consistent API interactions
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Enumeration of response statuses"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    status: ResponseStatus = Field(..., description="Status of the response")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = Field(None, description="Unique identifier for the request")


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")


class SuccessResponse(BaseResponse):
    """Success response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class SessionResponse(SuccessResponse):
    """Session-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Session data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Session created successfully",
                "data": {
                    "session_id": "sess_12345",
                    "user_id": "user_67890",
                    "created_at": "2024-01-01T12:00:00Z",
                    "context": {}
                }
            }
        }


class MemoryResponse(SuccessResponse):
    """Memory-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Memory data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Memory retrieved successfully",
                "data": {
                    "memory_id": "mem_abcde",
                    "content": "Sample memory content",
                    "metadata": {
                        "source": "user_interaction",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }


class AgentResponse(SuccessResponse):
    """Agent-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Agent execution data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Agent executed successfully",
                "data": {
                    "agent_id": "agent_123",
                    "session_id": "sess_456",
                    "result": {
                        "output": "Agent response",
                        "state": {}
                    },
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class WorkflowResponse(SuccessResponse):
    """Workflow-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Workflow execution data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Workflow executed successfully",
                "data": {
                    "workflow": "conversation_workflow",
                    "session_id": "sess_789",
                    "results": [
                        {
                            "agent_id": "parser_agent",
                            "status": "completed",
                            "result": {}
                        }
                    ],
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class HealthResponse(SuccessResponse):
    """Health check response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Health check data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "System is healthy",
                "data": {
                    "status": "healthy",
                    "version": "1.0.0",
                    "uptime": "3600",
                    "services": {
                        "database": "connected",
                        "redis": "connected",
                        "memory": "available"
                    }
                }
            }
        }


class ChatResponse(SuccessResponse):
    """Chat response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Chat response data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Chat response generated",
                "data": {
                    "session_id": "sess_123",
                    "response": "This is the AI response to your message",
                    "context": {
                        "relevant_memories": [],
                        "agent_used": "response_agent"
                    },
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class UserResponse(SuccessResponse):
    """User-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="User data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "User retrieved successfully",
                "data": {
                    "user_id": "user_123",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class PromptResponse(SuccessResponse):
    """Prompt-related response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Prompt data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Prompt retrieved successfully",
                "data": {
                    "prompt_id": "prompt_123",
                    "content": "You are a helpful AI assistant...",
                    "template_variables": ["user_name"],
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class AnalyticsResponse(SuccessResponse):
    """Analytics response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Analytics data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Analytics data retrieved",
                "data": {
                    "metrics": {
                        "total_sessions": 100,
                        "avg_response_time": 0.5,
                        "active_users": 50
                    },
                    "timeframe": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-01-01T23:59:59Z"
                    }
                }
            }
        }


class FeedbackResponse(SuccessResponse):
    """Feedback response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Feedback data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Feedback submitted successfully",
                "data": {
                    "feedback_id": "feedback_123",
                    "user_id": "user_123",
                    "rating": 5,
                    "comment": "Great service!",
                    "submitted_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class HistoryResponse(SuccessResponse):
    """History response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="History data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "History retrieved successfully",
                "data": {
                    "sessions": [
                        {
                            "session_id": "sess_123",
                            "user_id": "user_123",
                            "created_at": "2024-01-01T12:00:00Z",
                            "last_message": "Hello there!",
                            "messages_count": 5
                        }
                    ]
                }
            }
        }


class NewsletterResponse(SuccessResponse):
    """Newsletter response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Newsletter data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Newsletter subscription processed",
                "data": {
                    "subscription_id": "sub_123",
                    "email": "user@example.com",
                    "status": "subscribed",
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class TTSResponse(SuccessResponse):
    """Text-to-Speech response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="TTS data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Audio generated successfully",
                "data": {
                    "audio_id": "audio_123",
                    "text": "Hello world",
                    "voice": "default",
                    "duration": 2.5,
                    "audio_url": "https://example.com/audio_123.mp3"
                }
            }
        }


class MCPResponse(SuccessResponse):
    """MCP (Multi-Client Protocol) response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="MCP data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "MCP request processed",
                "data": {
                    "request_id": "req_123",
                    "client_id": "client_456",
                    "response": "MCP response data",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class UsageResponse(SuccessResponse):
    """Usage response model"""
    data: Optional[Dict[str, Any]] = Field(None, description="Usage data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Usage data retrieved",
                "data": {
                    "user_id": "user_123",
                    "usage": {
                        "tokens_used": 1000,
                        "requests_count": 50,
                        "storage_used": 1024
                    },
                    "period": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-01-01T23:59:59Z"
                    }
                }
            }
        }


# Response factory for creating standardized responses
class ResponseFactory:
    """Factory for creating standardized API responses"""
    
    @staticmethod
    def success(message: str = "Operation completed successfully", 
                data: Optional[Dict[str, Any]] = None) -> SuccessResponse:
        """Create a success response"""
        return SuccessResponse(
            status=ResponseStatus.SUCCESS,
            message=message,
            data=data
        )
    
    @staticmethod
    def error(message: str = "Operation failed", 
              error_code: Optional[str] = None,
              error_details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """Create an error response"""
        return ErrorResponse(
            status=ResponseStatus.ERROR,
            message=message,
            error_code=error_code,
            error_details=error_details
        )
    
    @staticmethod
    def warning(message: str = "Warning issued", 
                data: Optional[Dict[str, Any]] = None) -> BaseResponse:
        """Create a warning response"""
        return BaseResponse(
            status=ResponseStatus.WARNING,
            message=message,
            data=data
        )
    
    @staticmethod
    def info(message: str = "Information provided", 
             data: Optional[Dict[str, Any]] = None) -> BaseResponse:
        """Create an info response"""
        return BaseResponse(
            status=ResponseStatus.INFO,
            message=message,
            data=data
        )


# API response schema definitions
API_RESPONSE_SCHEMAS = {
    "health": HealthResponse,
    "session": SessionResponse,
    "memory": MemoryResponse,
    "agent": AgentResponse,
    "workflow": WorkflowResponse,
    "chat": ChatResponse,
    "user": UserResponse,
    "prompt": PromptResponse,
    "analytics": AnalyticsResponse,
    "feedback": FeedbackResponse,
    "history": HistoryResponse,
    "newsletter": NewsletterResponse,
    "tts": TTSResponse,
    "mcp": MCPResponse,
    "usage": UsageResponse
}