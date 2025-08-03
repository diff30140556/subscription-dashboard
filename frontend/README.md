# Churn Analysis Frontend

Next.js frontend application for customer churn analysis dashboard.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Copy `.env.local.example` to `.env.local` and configure:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

3. Run the development server:
```bash
npm run dev
```

4. Open http://localhost:3000 in your browser.

## Deployment

This frontend is configured for deployment on Vercel:

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

### Environment Variables for Production

Make sure to set these in your Vercel dashboard:
- `NEXT_PUBLIC_API_URL` - URL of your deployed backend API
- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 13+ app router
│   ├── lib/              # Utility libraries
│   └── scripts/          # Utility scripts
├── public/               # Static assets
├── package.json          # Dependencies and scripts
└── next.config.ts        # Next.js configuration
```