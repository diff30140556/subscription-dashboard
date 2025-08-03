'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

/** Customer 型別：對應 Supabase 資料表欄位 */
interface Customer {
  customerID: string;
  gender: string;
  SeniorCitizen: number;
  Partner: string;
  Dependents: string;
  tenure: number;
  PhoneService: string;
  MultipleLines: string;
  InternetService: string;
  OnlineSecurity: string;
  OnlineBackup: string;
  DeviceProtection: string;
  TechSupport: string;
  StreamingTV: string;
  StreamingMovies: string;
  Contract: string;
  PaperlessBilling: string;
  PaymentMethod: string;
  MonthlyCharges: number;
  TotalCharges: number;
  Churn: string;
}

/** 分佈型別 */
interface KeyCountPct {
  key: string;
  count: number;
  pct: number;
}
interface RangeCountPct {
  range: string;
  count: number;
  pct: number;
}

/** 可選 Metrics 集合 */
interface Metrics {
  churnRate?: number;
  avgTenure?: number;
  avgMonthlyCharges?: number;
}

/** Summary 型別（完整轉換成 camelCase） */
interface AnalysisSummary {
  generatedAt?: string;

  totals?: {
    churned?: number;
  };

  averages?: {
    tenure?: number;
    monthlyCharges?: number;
    totalCharges?: number;
  };

  byContract?: KeyCountPct[];
  byPayment?: KeyCountPct[];
  tenureRanges?: RangeCountPct[];
  monthlyChargeRanges?: RangeCountPct[];

  churnRate?: number;
  segments?: Array<{ segment: string; churnRate: number }>;
  topDrivers?: Array<{ feature: string; importance: number }>;
  note?: string;

  overallChurn?: number;
  avgTenure?: number;
  avgMonthlyCharges?: number;
  metrics?: Metrics;
}

/** 工具：判斷 unknown 是否為 Record */
type AnyRecord = Record<string, unknown>;
const isRecord = (x: unknown): x is AnyRecord =>
  typeof x === 'object' && x !== null;

/** 工具：安全轉換成 number */
const toNumber = (v: unknown): number | undefined => {
  if (v === undefined || v === null) return undefined;
  if (typeof v === 'number' && !Number.isNaN(v)) return v;
  if (typeof v === 'string') {
    const cleaned = v.trim().replace(/%/g, '').replace(/,/g, '');
    const n = Number(cleaned);
    return Number.isNaN(n) ? undefined : n;
  }
  return undefined;
};

/** 工具：安全讀取物件中的 number 欄位 */
const pickNumber = (obj: AnyRecord, key: string): number | undefined =>
  typeof obj[key] === 'number' ? (obj[key] as number) : toNumber(obj[key]);

/** 工具：轉換陣列 [{ key,count,pct }] */
const mapKeyCountPct = (arr: unknown): KeyCountPct[] | undefined => {
  if (!Array.isArray(arr)) return undefined;
  const out: KeyCountPct[] = [];
  for (const item of arr) {
    if (!isRecord(item)) continue;
    const key = typeof item.key === 'string' ? item.key : undefined;
    const count = pickNumber(item, 'count');
    const pct = pickNumber(item, 'pct');
    if (key && typeof count === 'number' && typeof pct === 'number') {
      out.push({ key, count, pct });
    }
  }
  return out.length ? out : undefined;
};

/** 工具：轉換陣列 [{ range,count,pct }] */
const mapRangeCountPct = (arr: unknown): RangeCountPct[] | undefined => {
  if (!Array.isArray(arr)) return undefined;
  const out: RangeCountPct[] = [];
  for (const item of arr) {
    if (!isRecord(item)) continue;
    const range = typeof item.range === 'string' ? item.range : undefined;
    const count = pickNumber(item, 'count');
    const pct = pickNumber(item, 'pct');
    if (range && typeof count === 'number' && typeof pct === 'number') {
      out.push({ range, count, pct });
    }
  }
  return out.length ? out : undefined;
};

/** normalizeSummary：將 raw 轉成前端預期的 camelCase */
const normalizeSummary = (raw: unknown): AnalysisSummary => {
  const base = isRecord(raw) ? raw : {};
  const src = isRecord(base.summary) ? (base.summary as AnyRecord) : base;

  const result: AnalysisSummary = {};

  result.generatedAt =
    typeof src.generatedAt === 'string'
      ? (src.generatedAt as string)
      : typeof src.generated_at === 'string'
        ? (src.generated_at as string)
        : undefined;

  // Handle KPIs API response format
  if (isRecord(src.kpis)) {
    const kpis = src.kpis as AnyRecord;
    
    // Extract values from KPIs
    result.churnRate = pickNumber(kpis, 'churn_rate_overall');
    result.avgTenure = pickNumber(kpis, 'avg_tenure');
    result.avgMonthlyCharges = pickNumber(kpis, 'avg_monthly');
    
    // Set up totals and averages for compatibility
    const churned = pickNumber(kpis, 'churned_users');
    if (churned !== undefined) {
      result.totals = { churned };
    }
    
    result.averages = {
      tenure: pickNumber(kpis, 'avg_tenure'),
      monthlyCharges: pickNumber(kpis, 'avg_monthly'),
      totalCharges: undefined
    };
  }

  // totals (fallback for other formats)
  if (isRecord(src.totals)) {
    const t = src.totals as AnyRecord;
    const churned = pickNumber(t, 'churned');
    result.totals = churned !== undefined ? { churned } : undefined;
  }

  // averages (fallback for other formats)
  if (isRecord(src.averages)) {
    const a = src.averages as AnyRecord;
    result.averages = {
      tenure: pickNumber(a, 'tenure') ?? pickNumber(a, 'avgTenure'),
      monthlyCharges:
        pickNumber(a, 'monthlyCharges') ?? pickNumber(a, 'avgMonthly'),
      totalCharges:
        pickNumber(a, 'totalCharges') ?? pickNumber(a, 'avgTotal'),
    };
  }

  result.byContract = mapKeyCountPct(src.by_contract);
  result.byPayment = mapKeyCountPct(src.by_payment);
  result.tenureRanges = mapRangeCountPct(src.tenure_ranges);
  result.monthlyChargeRanges = mapRangeCountPct(src.monthly_charge_ranges);

  if (typeof src.note === 'string') result.note = src.note as string;
  if (typeof src.churnRate === 'number') result.churnRate = src.churnRate as number;
  if (typeof src.overallChurn === 'number')
    result.overallChurn = src.overallChurn as number;

  if (typeof src.avgTenure === 'number') result.avgTenure = src.avgTenure as number;
  if (typeof src.avgMonthlyCharges === 'number')
    result.avgMonthlyCharges = src.avgMonthlyCharges as number;

  if (isRecord(src.metrics)) {
    const m = src.metrics as AnyRecord;
    result.metrics = {
      churnRate:
        typeof m.churnRate === 'number' ? (m.churnRate as number) : undefined,
      avgTenure:
        typeof m.avgTenure === 'number' ? (m.avgTenure as number) : undefined,
      avgMonthlyCharges:
        typeof m.avgMonthlyCharges === 'number'
          ? (m.avgMonthlyCharges as number)
          : undefined,
    };
  }

  if (Array.isArray(src.segments)) {
    result.segments = src.segments as AnalysisSummary['segments'];
  }
  if (Array.isArray(src.topDrivers)) {
    result.topDrivers = src.topDrivers as AnalysisSummary['topDrivers'];
  }

  return result;
};

export default function Home() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [computedChurnRate, setComputedChurnRate] = useState<number | undefined>(undefined);

  useEffect(() => {
    const fetchData = async () => {
      const { data, error } = await supabase
        .from('churn_customers')
        .select('*')
        .limit(10);

      if (error) {
        console.error('Supabase error:', error);
      } else if (Array.isArray(data)) {
        setCustomers(data as Customer[]);
      }
    };
    fetchData();
  }, []);

  // 計算 churn rate
  useEffect(() => {
    let mounted = true;
    const calcChurnRate = async () => {
      try {
        const { count: totalCount, error: totalErr } = await supabase
          .from('churn_customers')
          .select('*', { count: 'exact', head: true });
        if (totalErr) throw totalErr;

        const { count: churnedCount, error: churnErr } = await supabase
          .from('churn_customers')
          .select('*', { count: 'exact', head: true })
          .eq('Churn', 'Yes');
        if (churnErr) throw churnErr;

        if (
          mounted &&
          typeof totalCount === 'number' &&
          totalCount > 0 &&
          typeof churnedCount === 'number'
        ) {
          setComputedChurnRate(churnedCount / totalCount);
        }
      } catch (e) {
        console.error('Compute churn rate error:', e);
        if (mounted) setComputedChurnRate(undefined);
      }
    };
    calcChurnRate();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const fetchSummary = async () => {
      try {
        setSummaryLoading(true);
        setSummaryError(null);
        const res = await fetch('/api/analyze', {
          method: 'GET',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' },
        });
        if (!res.ok) {
          const text = await res.text().catch(() => '');
          throw new Error(`Analyze API ${res.status}: ${text || res.statusText}`);
        }
        const data: unknown = await res.json();
        const norm = normalizeSummary(data);
        setSummary(norm);
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          // ignore abort
        } else if (err instanceof Error) {
          console.error('Analyze API error:', err);
          setSummaryError(err.message || 'Failed to load summary');
        } else {
          setSummaryError('Failed to load summary');
        }
      } finally {
        setSummaryLoading(false);
      }
    };

    fetchSummary();
    return () => controller.abort();
  }, []);

  const formatPercent = (v?: number) => {
    if (v === undefined || v === null || Number.isNaN(v)) return '—';
    return v > 1 ? `${v.toFixed(1)}%` : `${(v * 100).toFixed(1)}%`;
  };

  const formatNumber = (v?: number) => {
    if (v === undefined || v === null || Number.isNaN(v)) return '—';
    return v.toFixed(1);
  };

  return (
    <main className="p-4" suppressHydrationWarning={true}>
      <h1 className="text-2xl font-bold mb-4">Customer List</h1>
      <table className="table-auto border border-collapse w-full">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-4 py-2">Customer ID</th>
            <th className="border px-4 py-2">Gender</th>
            <th className="border px-4 py-2">Senior?</th>
            <th className="border px-4 py-2">Tenure</th>
            <th className="border px-4 py-2">Monthly Charges</th>
            <th className="border px-4 py-2">Churn</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={customer.customerID}>
              <td className="border px-4 py-2">{customer.customerID}</td>
              <td className="border px-4 py-2">{customer.gender}</td>
              <td className="border px-4 py-2">
                {customer.SeniorCitizen ? 'Yes' : 'No'}
              </td>
              <td className="border px-4 py-2">{customer.tenure}</td>
              <td className="border px-4 py-2">{customer.MonthlyCharges}</td>
              <td className="border px-4 py-2">{customer.Churn}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <section className="mt-6">
        <h2 className="text-xl font-semibold mb-3">Analysis Summary</h2>

        {summaryLoading && (
          <div className="rounded-lg border p-4 animate-pulse">Loading summary…</div>
        )}

        {summaryError && (
          <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
            Unable to load summary: {summaryError}
          </div>
        )}

        {!summaryLoading && !summaryError && summary && (
          <div className="space-y-4">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border p-4">
                <div className="text-sm text-gray-500">Churn Rate</div>
                <div className="text-2xl font-bold mt-1">
                  {formatPercent(
                    computedChurnRate ??
                    summary.churnRate ??
                    summary.overallChurn ??
                    summary.metrics?.churnRate
                  )}
                </div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm text-gray-500">Avg Tenure (months)</div>
                <div className="text-2xl font-bold mt-1">
                  {formatNumber(
                    summary.averages?.tenure ??
                    summary.avgTenure ??
                    summary.metrics?.avgTenure
                  )}
                </div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm text-gray-500">Avg Monthly Charges</div>
                <div className="text-2xl font-bold mt-1">
                  ${formatNumber(
                    summary.averages?.monthlyCharges ??
                    summary.avgMonthlyCharges ??
                    summary.metrics?.avgMonthlyCharges
                  )}
                </div>
              </div>
            </div>

            {/* Raw JSON for debugging */}
            <details className="rounded-lg border p-4">
              <summary className="cursor-pointer font-medium">Raw JSON</summary>
              <pre className="mt-3 text-sm overflow-auto">
                {JSON.stringify(summary, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </section>
    </main>
  );
}