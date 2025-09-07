# DRS Docker Setup

This document provides instructions for running the Decision Review System (DRS) using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd /path/to/drs-project
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to be healthy:**
   ```bash
   docker-compose ps
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432
   - Redis: localhost:6379
   - MinIO (file storage): http://localhost:9000

## Services Overview

### Development Services (Default)

- **db**: PostgreSQL 15 database
- **redis**: Redis 7 for caching
- **backend**: FastAPI backend service
- **frontend**: React frontend service

### Production Services (Profile: production)

- **nginx**: Nginx reverse proxy with SSL termination
- **backend**: FastAPI backend service
- **frontend**: React frontend service (served by nginx)

### Optional Services (Profile: storage)

- **minio**: MinIO S3-compatible object storage

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database
POSTGRES_DB=drs_db
POSTGRES_USER=drs_user
POSTGRES_PASSWORD=drs_password

# Redis
REDIS_URL=redis://redis:6379

# Backend
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=/app/uploads
LOG_LEVEL=INFO

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# MinIO (optional)
MINIO_ACCESS_KEY=drs_access_key
MINIO_SECRET_KEY=drs_secret_key
```

## Development Workflow

### Start Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec db psql -U drs_user -d drs_db

# Reset database
docker-compose down -v
docker-compose up -d db
```

### Backend Development

```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d backend

# Run tests
docker-compose exec backend pytest
```

### Frontend Development

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Install new dependencies
docker-compose exec frontend npm install <package-name>
```

## Production Deployment

### Using Production Profile

```bash
# Start production services
docker-compose --profile production up -d

# Access via nginx
# Frontend: http://localhost
# Backend API: http://localhost/api
```

### SSL Configuration

For production, replace the self-signed certificates in `docker/ssl/` with valid certificates:

```bash
# Copy your certificates
cp /path/to/your/cert.pem docker/ssl/cert.pem
cp /path/to/your/key.pem docker/ssl/key.pem
```

### Environment Configuration

Update the environment variables in `docker-compose.yml` for production:

```yaml
environment:
  - SECRET_KEY=your-production-secret-key
  - DATABASE_URL=postgresql://prod_user:prod_password@prod-db:5432/prod_db
  - REDIS_URL=redis://prod-redis:6379
```

## File Storage Options

### Local Storage (Default)

Files are stored in the `uploads` Docker volume. Access uploaded files:

```bash
docker-compose exec backend ls -la /app/uploads
```

### MinIO Storage (S3-compatible)

Enable MinIO for cloud-like file storage:

```bash
# Start with storage profile
docker-compose --profile storage up -d

# Access MinIO console
# URL: http://localhost:9001
# Username: drs_access_key
# Password: drs_secret_key
```

## Monitoring and Debugging

### Health Checks

```bash
# Check service health
docker-compose ps

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

### Database Inspection

```bash
# Connect to database
docker-compose exec db psql -U drs_user -d drs_db

# List tables
\d

# View users
SELECT * FROM users;

# View reviews
SELECT * FROM reviews;
```

### Performance Monitoring

```bash
# Backend performance
docker-compose exec backend python -c "import psutil; print(psutil.cpu_percent())"

# Database connections
docker-compose exec db psql -U drs_user -d drs_db -c "SELECT count(*) FROM pg_stat_activity;"
```

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :3000
   lsof -i :5432
   ```

2. **Database connection issues:**
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d db
   ```

3. **Build failures:**
   ```bash
   # Clean build
   docker-compose build --no-cache
   ```

4. **Permission issues:**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER .
   ```

### Logs and Debugging

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service logs
docker-compose logs backend

# Last N lines
docker-compose logs --tail=100 backend
```

## Backup and Restore

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U drs_user drs_db > backup.sql

# Backup with timestamp
docker-compose exec db pg_dump -U drs_user drs_db > "backup_$(date +%Y%m%d_%H%M%S).sql"
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U drs_user -d drs_db < backup.sql
```

### Volume Backup

```bash
# Backup uploads volume
docker run --rm -v drs_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz -C /data .
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Scale frontend services
docker-compose up -d --scale frontend=2
```

### Resource Limits

Update `docker-compose.yml` to set resource limits:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
```

## Security Considerations

1. **Change default passwords** in production
2. **Use strong SECRET_KEY** for JWT tokens
3. **Enable SSL/TLS** in production
4. **Restrict database access** to specific IPs
5. **Regular security updates** of base images
6. **Monitor logs** for suspicious activity

## Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Verify service health: `docker-compose ps`
3. Review configuration files
4. Check Docker and Docker Compose versions
5. Ensure sufficient system resources

## Development Tips

- Use `docker-compose up` (without `-d`) for debugging
- Mount source code as volumes for hot reloading
- Use `.dockerignore` to exclude unnecessary files
- Keep Docker images small by using multi-stage builds
- Use health checks to ensure service dependencies
