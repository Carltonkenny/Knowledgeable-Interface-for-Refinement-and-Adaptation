# PromptForge Multi-Agent System

A cutting-edge multi-agent AI system with advanced memory management, multi-modal processing, and intelligent orchestration.

## Architecture Overview

This system consists of several interconnected components:

1. **Agents Module**: Multi-agent orchestration with personality-based routing
2. **Memory Systems**: Advanced LangMem with hybrid recall and SuperMemory
3. **Middleware Layer**: OpenTelemetry tracing, metrics, and rate limiting
4. **Multi-modal Processing**: Image, voice, and file handling capabilities
5. **API Routes**: FastAPI endpoints for all system functionality
6. **Frontend Application**: Next.js web interface

## Production Readiness Status

✅ **Current Status**: 7.5/10 (Ready for production with additional work)

### Completed Features
- ✅ Core multi-agent orchestration
- ✅ Advanced memory systems (LangMem, SuperMemory, HybridRecall)
- ✅ Multi-modal processing capabilities
- ✅ Containerized deployment (Docker)
- ✅ Comprehensive API endpoints
- ✅ Middleware with tracing and metrics
- ✅ Security-focused design

### Remaining Work
- 🔧 Complete frontend implementation
- 🔧 Add comprehensive testing (80%+ coverage)
- 🔧 Finalize security hardening
- 🔧 Implement monitoring and observability
- 🔧 Complete documentation

## Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL database
- Node.js 18+ (for frontend)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd promptforge

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Setup database
# (Database setup instructions in docs/)

# Run tests to verify setup
python scripts/run_tests.py
```

### Running the System

```bash
# Start all services with Docker Compose
docker-compose up

# Or run individual components
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Key Components

### Memory Systems
- **LangMem**: Language memory with semantic search
- **SuperMemory**: Contextual memory for MCP clients
- **HybridRecall**: BM25 + Vector search fusion

### Agents
- Conversation handler
- Follow-up handler
- Swarm intelligence handler
- Unified agent orchestrator

### Multi-modal Processing
- Voice processing with transcription
- Image handling and analysis
- File validation and processing

## API Endpoints

```http
GET /health              # Health check
POST /api/v1/users       # User management
POST /api/v1/prompts     # Prompt management
POST /api/v1/sessions    # Session management
POST /api/v1/analytics   # Analytics data
POST /api/v1/feedback    # Feedback submission
GET /api/v1/history      # History retrieval
POST /api/v1/newsletter  # Newsletter subscription
POST /api/v1/tts         # Text-to-speech
POST /api/v1/mcp         # MCP integration
POST /api/v1/usage       # Usage tracking
```

## Testing

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test suites
python scripts/run_tests.py memory
python scripts/run_tests.py production
```

## Deployment

### Production Deployment
```bash
# Build production images
docker build -t promptforge:latest .

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Security Considerations
- All API endpoints require authentication
- Input validation and sanitization
- Rate limiting implemented
- Secure database connections
- Environment-based configuration

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For support, please open an issue on the GitHub repository or contact the development team.