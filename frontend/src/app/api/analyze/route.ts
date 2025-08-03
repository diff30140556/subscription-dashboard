// app/api/analyze/route.ts
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
    try {
        // Call the Python backend API for churn analysis
        const response = await fetch(`${API_BASE_URL}/api/churn/kpis`);

        if (!response.ok) {
            throw new Error(`Backend API error: ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (e) {
        // e 預設為 unknown：以 instanceof Error 縮小
        const message = e instanceof Error ? e.message : String(e);
        console.error('Error calling backend API:', message);
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
