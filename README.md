# Decision Review System (DRS)

A modern web application for ball tracking and trajectory analysis in sports, built with cutting-edge computer vision and 3D visualization technologies.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd drs
make setup

# Or with Docker
make docker-up
```

Visit: **http://localhost:3000**

## 🏗️ Architecture

### Backend
- **FastAPI** - High-performance async web framework
- **OpenCV** - Computer vision for ball tracking
- **PostgreSQL** - Robust data persistence
- **JWT** - Secure authentication
- **SQLAlchemy** - ORM with async support

### Frontend
- **React** - Modern UI framework
- **Three.js** - 3D trajectory visualization
- **Material-UI** - Professional component library
- **Axios** - HTTP client with interceptors

### Infrastructure
- **Docker** - Complete containerization
- **Nginx** - Production reverse proxy
- **Redis** - Caching layer
- **MinIO** - S3-compatible file storage

## 📋 Features

- ✅ **Video Upload** - Support for multiple video formats
- ✅ **Ball Tracking** - Real-time computer vision analysis
- ✅ **3D Visualization** - Interactive trajectory viewer
- ✅ **Review System** - Collaborative decision making
- ✅ **User Management** - JWT-based authentication
- ✅ **API Documentation** - Auto-generated OpenAPI/Swagger
- ✅ **Comprehensive Testing** - Unit, integration, e2e tests
- ✅ **Production Ready** - Docker deployment

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Commands

```bash
# Development
make dev              # Start both servers
make dev-backend      # Backend only
make dev-frontend     # Frontend only

# Testing
make test             # All tests
make test-backend     # Backend tests
make test-frontend    # Frontend tests
make test-e2e         # E2E tests

# Docker
make docker-up        # Start services
make docker-down      # Stop services
make docker-logs      # View logs

# Code Quality
make lint             # Check code style
make format           # Format code
make clean            # Clean caches
```

## 📁 Project Structure

```
drs/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── main.py      # Application entry
│   └── tests/           # Backend tests
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── api/         # API client
│   │   └── App.js       # Main app
│   └── tests/           # Frontend tests
├── docker/               # Docker configuration
├── specs/                # Design documents
└── docker-compose.yml    # Service orchestration
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User authentication |
| POST | `/videos/upload` | Upload video file |
| POST | `/videos/{id}/track` | Process ball tracking |
| GET | `/videos/{id}/trajectory` | Get trajectory data |
| POST | `/reviews` | Create review session |
| GET | `/reviews/{id}` | Get review details |

**Full API Documentation**: http://localhost:8000/docs

## 🧪 Testing

```bash
# Backend tests with coverage
make test-backend

# Frontend tests
make test-frontend

# E2E tests
make test-e2e
```

## 🚢 Deployment

### Development
```bash
make docker-up
```

### Production
```bash
make build-prod
make deploy-prod
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@db:5432/drs_db

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# File Storage
UPLOAD_DIR=/app/uploads

# External Services
REDIS_URL=redis://redis:6379
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@drs-project.com

---

**Built with ❤️ using modern web technologies**
