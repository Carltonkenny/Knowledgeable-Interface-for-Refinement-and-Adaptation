# Deployment Guide

This document provides comprehensive instructions for deploying the PromptForge Multi-Agent System in production environments.

## Production Readiness Assessment

**Current Status**: 7.5/10

### Ready for Production
- ✅ Core architecture stable
- ✅ Containerized deployment ready
- ✅ API endpoints fully functional
- ✅ Memory systems operational
- ✅ Security fundamentals in place

### Requires Attention
- ⚠️ Complete frontend implementation
- ⚠️ Full test coverage (target 80%+)
- ⚠️ Advanced monitoring and observability
- ⚠️ Production security hardening

## Deployment Options

### Option 1: Docker Compose (Recommended for Development/Testing)

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/promptforge
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=promptforge
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Option 2: Kubernetes (Enterprise Scale)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: promptforge-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: promptforge
  template:
    metadata:
      labels:
        app: promptforge
    spec:
      containers:
      - name: backend
        image: promptforge:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: promptforge-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: promptforge-service
spec:
  selector:
    app: promptforge
  ports:
  - port: 80
    targetPort: 8000
```

## Prerequisites

### Infrastructure Requirements
- **CPU**: Minimum 2 cores (4+ recommended)
- **Memory**: Minimum 4GB RAM (8+ recommended)
- **Storage**: 10GB+ available space
- **Network**: Outbound access for external APIs

### Software Dependencies
- Docker Engine 20.10+
- Docker Compose 2.0+
- PostgreSQL 13+
- Redis 6+

## Configuration Files

### Environment Variables

```env
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@db:5432/promptforge
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your_openai_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret_here
```

### Database Schema

```sql
-- Database schema for production
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE langmem_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Scaling Considerations

### Horizontal Scaling
- Backend services can be scaled horizontally
- Database connections should be pooled
- Redis should be configured for clustering
- Load balancing recommended for multiple backend instances

### Vertical Scaling
- Increase CPU and memory for high-concurrency scenarios
- Optimize database indexes for query performance
- Implement caching strategies for frequently accessed data

## Security Best Practices

### Network Security
- Use HTTPS/TLS for all communications
- Implement firewall rules to restrict access
- Use private networks for internal services
- Regular security audits and penetration testing

### Data Security
- Encrypt sensitive data at rest
- Implement secure key management
- Regular backups with encryption
- Audit logging for all sensitive operations

### Access Control
- Role-based access control (RBAC)
- JWT token validation
- API rate limiting
- Input validation and sanitization

## Monitoring and Observability

### Logging
```python
# Centralized logging configuration
import logging
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

### Metrics Collection
- CPU and memory usage
- Request latency and throughput
- Database query performance
- API error rates
- Cache hit ratios

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   - Verify database URL and credentials
   - Check network connectivity
   - Ensure database service is running

2. **Memory Limitations**
   - Monitor memory usage
   - Increase container memory limits
   - Optimize memory-intensive operations

3. **API Timeout Errors**
   - Increase timeout values
   - Optimize database queries
   - Implement request queuing

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check Redis connectivity
redis-cli ping

# View logs
docker logs promptforge_backend
```

## Upgrade Process

### Minor Version Updates
1. Backup database and configuration
2. Pull latest image
3. Stop services
4. Start services with new image
5. Verify functionality

### Major Version Updates
1. Review release notes
2. Perform backup
3. Test upgrade in staging
4. Apply upgrade to production
5. Monitor system performance

## Backup and Recovery

### Database Backup
```bash
# Daily backup script
pg_dump -h db -U user promptforge > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Configuration Backup
- Backup environment files
- Save Docker Compose configurations
- Document custom settings

## Performance Optimization

### Database Optimization
- Create appropriate indexes
- Regular vacuum and analyze operations
- Connection pooling configuration

### Memory Management
- Implement proper garbage collection
- Optimize memory usage in agents
- Use efficient data structures

### Caching Strategy
- Redis for session data
- CDN for static assets
- API response caching where appropriate

## Compliance Considerations

### Data Privacy
- GDPR compliance for European users
- CCPA compliance for California residents
- Data retention policies
- Right to erasure implementation

### Regulatory Compliance
- SOC 2 Type II compliance
- HIPAA compliance (if healthcare data)
- PCI-DSS compliance (if payment data)

## Support and Maintenance

### Regular Maintenance Tasks
- Weekly database maintenance
- Monthly security audits
- Quarterly performance reviews
- Annual compliance assessments

### Support Channels
- Issue tracking via GitHub
- Community forums
- Professional support contracts
- Documentation updates