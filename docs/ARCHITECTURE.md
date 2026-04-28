# System Architecture

This document provides a comprehensive overview of the PromptForge Multi-Agent System architecture, detailing the design principles, components, and relationships between different parts of the system.

## High-Level Architecture

The system follows a microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Middleware    │
│   (Next.js)     │───▶│   (FastAPI)     │───▶│   (Tracing,    │
│                 │    │                 │    │    Metrics,     │
└─────────────────┘    └─────────────────┘    │    Rate Limiting│
                                          └─────────────────┘
                                                    │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agents        │    │   Memory        │    │   Multi-modal   │
│   (Orchestrator)│───▶│   (LangMem,     │───▶│   (Voice/Image) │
│                 │    │    SuperMemory, │    │                 │
└─────────────────┘    │    HybridRecall)│    └─────────────────┘
                       └─────────────────┘
                                    │
                       ┌─────────────────┐
                       │   Storage       │
                       │   (PostgreSQL,  │
                       │    Redis)       │
                       └─────────────────┘
```

## Component Architecture

### 1. Agents Module

The agents module implements the core multi-agent orchestration system with specialized handlers:

#### Agent Handlers
- **Conversation Handler**: Manages conversational flows
- **Follow-up Handler**: Handles contextual follow-ups
- **Swarm Intelligence Handler**: Coordinates multiple agents
- **Unified Agent**: Central orchestrator for all agent types

#### Key Features
- Personality-based routing
- Context preservation across conversations
- Intent-based agent selection
- Conversation state management

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                   Agent Router                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Conversation│  │ Follow-up   │  │ Swarm       │    │
│  │ Handler     │  │ Handler     │  │ Intelligence│    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                  │         │         │               │
│                  ▼         ▼         ▼               │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Agent Coordinator                       │ │
│  │  - Intent classification                          │ │
│  │  - Context management                            │ │
│  │  - Agent selection                               │ │
│  │  - Response orchestration                        │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2. Memory Systems

The memory systems provide persistent and intelligent storage for conversation context and knowledge:

#### LangMem (Language Memory)
- Semantic search capabilities
- Hybrid recall (BM25 + Vector)
- Context-aware retrieval
- Memory lifecycle management

#### SuperMemory (Context Memory)
- MCP-exclusive conversational context
- Temporal updates (new info supersedes old)
- Relationship tracking between facts
- Trust level calculation for MCP clients

#### HybridRecall
- Reciprocal Rank Fusion (RRF) for result merging
- Maximal Marginal Relevance (MMR) for diversity
- Cross-encoder reranking capability
- Lazy provisioning of memory indices

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    Memory Manager                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   LangMem   │  │ SuperMemory │  │ HybridRecall│    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                  │         │         │               │
│                  ▼         ▼         ▼               │
│  ┌───────────────────────────────────────────────────┐ │
│  │                Memory Storage                     │ │
│  │  - PostgreSQL (persistent)                       │ │
│  │  - Redis (caching)                               │ │
│  │  - Vector database (pgvector)                    │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3. Middleware Layer

The middleware layer provides cross-cutting concerns for the system:

#### OpenTelemetry Tracing
- Distributed tracing for requests
- Span creation and propagation
- Performance monitoring
- Error tracking

#### Metrics Collection
- Request/response timing
- Error rates
- Resource utilization
- Custom business metrics

#### Rate Limiting
- Per-user rate limiting
- API endpoint protection
- Burst control
- Quota management

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    Middleware Layer                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Tracing     │  │ Metrics     │  │ Rate        │    │
│  │ Middleware  │  │ Collection  │  │ Limiting    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                  │         │         │               │
│                  ▼         ▼         ▼               │
│  ┌───────────────────────────────────────────────────┐ │
│  │              FastAPI App                          │ │
│  │  - Request handling                               │ │
│  │  - Response processing                            │ │
│  │  - Error handling                                 │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4. Multi-modal Processing

The system supports various input/output modalities:

#### Voice Processing
- Audio recording and streaming
- Speech-to-text transcription
- Voice quality analysis
- Voice output synthesis

#### Image Processing
- Image upload and validation
- Image content analysis
- Visual context extraction
- Image metadata handling

#### File Handling
- File type validation
- File size limitations
- Security scanning
- Cross-format conversion

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                   Multi-modal Processing                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Voice       │  │ Image       │  │ File        │    │
│  │ Processing  │  │ Processing  │  │ Handling    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                  │         │         │               │
│                  ▼         ▼         ▼               │
│  ┌───────────────────────────────────────────────────┐ │
│  │                Input/Output Processing            │ │
│  │  - Format conversion                              │ │
│  │  - Validation                                     │ │
│  │  - Security                                       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Request Flow
1. **Inbound Request**: API Gateway receives request
2. **Authentication**: Security middleware validates token
3. **Routing**: Agent Router determines appropriate handler
4. **Memory Retrieval**: Memory systems fetch context
5. **Processing**: Agent executes based on intent
6. **Response Generation**: Output formatted for delivery
7. **Memory Storage**: New context stored for future use
8. **Outbound Response**: Response sent back to client

### Data Persistence
- **Persistent Storage**: PostgreSQL for structured data
- **Caching Layer**: Redis for frequently accessed data
- **Vector Storage**: pgvector for semantic search
- **Temporary Storage**: Local file system for media

## Technology Stack

### Backend Technologies
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector
- **Cache**: Redis
- **Message Queue**: Not yet implemented (planned)
- **Orchestration**: Docker + Docker Compose

### Frontend Technologies
- **Framework**: Next.js (React)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context API
- **Build Tool**: Vite

### DevOps Technologies
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana (planned)
- **Logging**: ELK Stack (planned)

## Deployment Architecture

### Containerized Deployment
```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Backend     │  │ Database    │  │ Redis       │    │
│  │ (FastAPI)   │  │ (PostgreSQL)│  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                  │         │         │               │
│                  ▼         ▼         ▼               │
│  ┌───────────────────────────────────────────────────┐ │
│  │                Services                           │ │
│  │  - API Server                                     │ │
│  │  - Background Workers                             │ │
│  │  - Cache Server                                   │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Scalability Patterns
- **Horizontal Scaling**: Multiple backend instances
- **Database Sharding**: Not yet implemented (planned)
- **Caching Strategy**: Redis cluster (planned)
- **Load Balancing**: NGINX or cloud load balancer

## Security Architecture

### Defense-in-Depth Approach
1. **Network Security**: Firewalls, TLS encryption
2. **Application Security**: Input validation, authentication
3. **Data Security**: Encryption, access controls
4. **Operational Security**: Monitoring, auditing

### Authentication Flow
1. Client sends credentials
2. Authentication service validates
3. JWT token generated and returned
4. Subsequent requests include token
5. Middleware validates token on each request

## Performance Architecture

### Caching Strategy
- **API Response Caching**: Frequently accessed data
- **Memory Caching**: Recent conversation context
- **Database Query Caching**: Common queries
- **Static Asset Caching**: Frontend assets

### Optimization Techniques
- **Lazy Loading**: Load resources on demand
- **Batch Processing**: Group operations for efficiency
- **Connection Pooling**: Database and Redis connections
- **Asynchronous Processing**: Non-blocking operations

## Monitoring and Observability

### Key Metrics
- **API Metrics**: Response times, error rates, throughput
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Active users, conversation volume
- **Security Metrics**: Authentication attempts, security events

### Alerting Strategy
- **Critical Alerts**: System failures, security breaches
- **Warning Alerts**: Performance degradation, high load
- **Informational Alerts**: Normal operations, maintenance

## Future Architecture Evolution

### Phase 1: MVP (Current State)
- Monolithic deployment
- Basic agent orchestration
- Fundamental memory systems
- REST API endpoints

### Phase 2: Enhanced Features
- Microservices decomposition
- Advanced agent intelligence
- Enhanced memory capabilities
- Multi-modal expansion

### Phase 3: Production Scale
- Auto-scaling infrastructure
- Advanced caching strategies
- Distributed processing
- Enterprise-grade security

This architecture provides a solid foundation for a production-ready multi-agent system while maintaining flexibility for future enhancements.