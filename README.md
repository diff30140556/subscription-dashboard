This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Python Data Pipeline

This project includes a Python data cleaning and aggregation pipeline for churn analysis.

### Setup Python Environment

**Activate virtual environment:**

**Windows Git Bash:**
```bash
source venv/Scripts/activate
```

**Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Database Setup

Create the summary table in Supabase by running this SQL in the Supabase SQL editor:

```sql
create table if not exists churn_summary (
  id uuid primary key default gen_random_uuid(),
  snapshot_ts timestamptz not null default now(),
  payload jsonb not null
);
create index if not exists idx_churn_summary_snapshot on churn_summary (snapshot_ts desc);
```

### Running the Pipeline

**Test Supabase connectivity:**
```bash
python scripts/test_supabase.py
```

**Run the main aggregation pipeline:**
```bash
python scripts/clean_and_aggregate.py
```

### Environment Variables

**Security Note:** 
- `.env` contains `SUPABASE_SERVICE_ROLE_KEY` for backend Python scripts - **never commit this file**
- `.env.local` contains `NEXT_PUBLIC_*` variables for frontend - safe for client use
- Only use service role key in server-side Python scripts, never in frontend code

### Accessing Results in Next.js

Example Server Component to display the latest churn summary:

```typescript
// app/churn/summary/page.tsx
import { createClient } from '@/lib/supabase'

export default async function ChurnSummaryPage() {
  const supabase = createClient()
  
  const { data: summary } = await supabase
    .from('churn_summary')
    .select('*')
    .order('snapshot_ts', { ascending: false })
    .limit(1)
    .single()

  if (!summary) {
    return <div>No summary data available</div>
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Latest Churn Summary</h1>
      <p className="mb-4">Generated: {new Date(summary.snapshot_ts).toLocaleString()}</p>
      <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
        {JSON.stringify(summary.payload, null, 2)}
      </pre>
    </div>
  )
}
```
