# Churn Analysis Backend

FastAPI backend service for customer churn analysis with PostgreSQL/Supabase integration and AI-powered insights.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Copy `.env.example` to `.env` and fill in your credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=your_database_url
OPENAI_API_KEY=your_openai_api_key
```

3. Run the development server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn py.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/redoc - Alternative API documentation
- http://localhost:8000/health - Health check endpoint

## Project Structure

```
backend/
├── py/                     # Main Python package
│   ├── analysis/          # Data analysis modules
│   ├── api/               # FastAPI route handlers
│   ├── core/              # Core utilities (database, utils)
│   └── main.py            # FastAPI application
├── models/                # ML model files
├── scripts/               # Utility scripts
├── requirements.txt       # Python dependencies
├── main.py               # Entry point
└── .env                  # Environment variables
```

## Deployment

This backend is designed to be deployed independently from the frontend. Popular options include:
- Railway
- Render
- Heroku
- DigitalOcean App Platform
- AWS Lambda (with Mangum)