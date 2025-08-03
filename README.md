# Churn Analysis Platform

A comprehensive customer churn analysis platform with separate frontend and backend services for independent deployment.

## Architecture

This project is organized into two independent services:

- **Frontend** (`frontend/`) - Next.js dashboard deployed on Vercel
- **Backend** (`backend/`) - Python FastAPI service with ML models and AI insights

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Start the backend server:
```bash
python main.py
```

The API will be available at http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Deployment

### Frontend (Vercel)
- Push to GitHub
- Connect repository to Vercel
- Set environment variables in Vercel dashboard
- Deploy automatically

### Backend (Various Options)
- Railway
- Render
- Heroku
- DigitalOcean App Platform
- AWS Lambda (with Mangum)

## Features

- **Real-time churn analysis** with PostgreSQL/Supabase
- **ML-powered predictions** using scikit-learn
- **AI-powered insights** with OpenAI GPT-4o
- **Interactive dashboard** with Next.js
- **Comprehensive API** with FastAPI
- **Production-ready** with proper error handling and logging

## API Documentation

Once the backend is running, visit:
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/redoc - Alternative API documentation

## Contributing

1. Make changes to the appropriate service (frontend/ or backend/)
2. Test locally
3. Submit pull request

For more details, see the README files in each service directory.