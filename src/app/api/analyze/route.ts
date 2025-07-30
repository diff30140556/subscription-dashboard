// app/api/analyze/route.ts
import { NextResponse } from 'next/server';
import { analyzeChurnedCustomers } from '../../../scripts/analyze_churn';

export async function GET() {
    try {
        // 若你的 RLS 允許 anon 讀取，用預設即可；
        // 如果需要繞過 RLS，改成：{ useServiceRole: true }，並在伺服器環境設定 SUPABASE_SERVICE_ROLE_KEY
        const summary = await analyzeChurnedCustomers(/* { useServiceRole: true } */);
        return NextResponse.json(summary);
    } catch (e: any) {
        return NextResponse.json({ error: e?.message ?? String(e) }, { status: 500 });
    }
}
