מןר# 🚀 KKL FMS - Deployment Guide

**Owner:** Nir Avutbul (nirab96Developer)

---

## 📋 Prerequisites

- DigitalOcean Droplet (8GB RAM, Ubuntu 22.04)
- GitLab repository access
- Domain (optional, for SSL)

---

## 🔧 Quick Start

### 1. Clone Repository

```bash
git clone git@gitlab.com:YOUR_USERNAME/kkl-forest.git
cd kkl-forest
```

### 2. Backend Setup

```bash
cd app_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd app_frontend
npm install
npm run dev -- --host 0.0.0.0
```

---

## 🐳 Docker Deployment (Recommended for Production)

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# Check status
docker-compose ps
```

---

## 🔐 Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@your-db-server:5432/kkl_fms

# Security
SECRET_KEY=your-very-long-random-secret-key
JWT_SECRET=your-jwt-secret-key

# Environment
ENV=production
```

### Frontend (.env)

```env
VITE_API_URL=http://your-server:8000/api/v1
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-key
```

---

## 📞 Support

- Owner: Nir Avutbul
- Email: avitbulnir@gmail.com
- GitLab: YOUR_USERNAME
