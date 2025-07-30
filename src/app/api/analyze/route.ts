// app/api/analyze/route.ts
import { NextResponse } from 'next/server';
import { analyzeChurnedCustomers } from '../../../scripts/analyze_churn';

// 由實際函式推導回傳型別，避免落入 any
type AnalyzeSummary = Awaited<ReturnType<typeof analyzeChurnedCustomers>>;

export async function GET() {
    try {
        // 若你的 RLS 允許 anon 讀取，用預設即可；
        // 如果需要繞過 RLS，改成：{ useServiceRole: true }，並在伺服器環境設定 SUPABASE_SERVICE_ROLE_KEY
        const summary = await analyzeChurnedCustomers(/* { useServiceRole: true } */);
        return NextResponse.json<AnalyzeSummary>(summary);
    } catch (e) {
        // e 預設為 unknown：以 instanceof Error 縮小
        const message = e instanceof Error ? e.message : String(e);
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
