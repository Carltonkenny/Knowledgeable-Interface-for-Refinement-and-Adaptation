# Deployment Guide

## Overview

This document provides comprehensive guidance for deploying the multi-agent system in production environments.

## Prerequisites

### System Requirements
- Python 3.11+
- Docker 20.10+
- Docker Compose 2.20+
- PostgreSQL 15+
- Redis 7+

### Environment Variables
The following environment variables must be configured:

```
DATABASE_URL=postgresql://user:password@db:5432/database_name
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your_secret_key_here
```

## Deployment Options

### Option 1: Docker Compose (Local/Development)
```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Copy environment file
cp .env.example .env
# Edit .env with actual values

# Start services
docker-compose up -d
```

### Option 2: Kubernetes (Production)
```yaml
# Example deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-agent-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multi-agent-api
  template:
    metadata:
      labels:
        app: multi-agent-api
    spec:
      containers:
      - name: api
        image: multi-agent-system:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: multi-agent-secrets
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
  name: multi-agent-api-service
spec:
  selector:
    app: multi-agent-api
  ports:
  - port: 80
    targetPort: 8000
```

### Option 3: Cloud Platform Deployment
#### Vercel (Frontend)
```bash
# Build frontend
cd promptforge-web
npm install
npm run build

# Deploy to Vercel
vercel
```

#### Railway (Backend)
```bash
# Push to GitHub and connect to Railway
# Configure environment variables in Railway dashboard
```

## Configuration Files

### Docker Compose Configuration
The `docker-compose.yml` file defines the complete stack:
- Backend API service
- Database (PostgreSQL)
- Cache (Redis)
- Frontend (Next.js)

### Environment Configuration
The `.env` file contains all necessary configuration values for different environments:
- Development
- Staging
- Production

## Scaling Considerations

### Horizontal Scaling
The system is designed to scale horizontally:
- API service: Multiple replicas can be deployed
- Database: Read replicas for read-heavy operations
- Cache: Redis cluster for high availability

### Vertical Scaling
Individual services can be scaled vertically:
- API service: More CPU and memory
- Database: Increased storage and connection limits
- Cache: Larger memory allocation

## Monitoring and Maintenance

### Health Checks
The system includes built-in health check endpoints:
- `/health` - Basic service health
- `/metrics` - Prometheus metrics endpoint

### Logging
All services log to stdout/stderr for container orchestration compatibility.
Logs should be aggregated using tools like ELK stack or similar.

### Backup Strategy
Regular database backups should be scheduled:
```bash
# Example backup script
pg_dump -h db -U username database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Security Best Practices

### Network Security
- Restrict access to internal services
- Use private networks for service communication
- Implement firewalls and network segmentation

### Application Security
- Regular security patches
- Environment variable management
- Secret rotation procedures
- Input validation and sanitization

### Data Security
- Encrypt sensitive data at rest
- Use secure transport protocols
- Regular data backup and recovery testing

## Troubleshooting

### Common Issues
1. **Database Connection Failures**
   - Check database service status
   - Verify connection string in environment variables
   - Confirm database credentials

2. **Service Not Starting**
   - Check logs for error messages
   - Verify environment variables
   - Confirm dependency services are running

3. **Performance Issues**
   - Monitor resource utilization
   - Check for memory leaks
   - Optimize database queries

### Debugging Commands
```bash
# View service logs
docker-compose logs api

# Execute commands in running container
docker-compose exec api bash

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart api
```

## Upgrade Process

### Minor Updates
1. Pull latest code
2. Rebuild Docker images
3. Restart services
4. Verify functionality

### Major Updates
1. Review release notes
2. Backup database and important data
3. Test upgrade in staging environment
4. Apply upgrade to production
5. Monitor system behavior post-upgrade

## Support and Maintenance

### Support Channels
- Issue tracking via GitHub
- Community forums
- Commercial support options

### Maintenance Windows
- Scheduled maintenance periods
- Emergency patch procedures
- Communication protocols for outages