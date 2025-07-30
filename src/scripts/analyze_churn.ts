// scripts/analyze_churn.ts
import { createClient } from '@supabase/supabase-js';

export interface Customer {
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
  TotalCharges: string | number;
  Churn: string;
}

type Summary = {
  generated_at: string;
  totals: { churned: number };
  averages: { avgTenure: number; avgMonthly: number; avgTotal: number };
  by_contract: Array<{ key: string; count: number; pct: number }>;
  by_payment: Array<{ key: string; count: number; pct: number }>;
  tenure_ranges: Array<{ range: string; count: number; pct: number }>;
  monthly_charge_ranges: Array<{ range: string; count: number; pct: number }>;
};

export async function analyzeChurnedCustomers(opts?: {
  useServiceRole?: boolean;
}): Promise<Summary> {
  // 在「Server 環境」讀取環境變數（API route 會傳進來）
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = opts?.useServiceRole
    ? process.env.SUPABASE_SERVICE_ROLE_KEY!   // 需要放在伺服器環境變數，切記不要放到 .env.local
    : process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

  const supabase = createClient(url, key);

  // 讀取 churned 客戶
  const { data, error } = await supabase
    .from('churn_customers')
    .select('*')
    .eq('Churn', 'Yes');

  if (error) throw new Error(error.message);
  const churned = (data ?? []) as Customer[];
  const n = churned.length;

  // --------- 彙總統計（簡化版，和你原本邏輯對齊） ---------
  const patterns: Record<string, Record<string, number>> = {
    contract: {},
    paymentMethod: {},
  };
  const tenureBins = { '0-12': 0, '13-24': 0, '25-48': 0, '49+': 0 };
  const chargeBins = { '0-35': 0, '36-65': 0, '66-95': 0, '96+': 0 };

  let sumTenure = 0;
  let sumMonthly = 0;
  let sumTotal = 0;

  for (const c of churned) {
    // 累加平均
    sumTenure += c.tenure ?? 0;
    sumMonthly += Number(c.MonthlyCharges ?? 0);
    sumTotal += Number.parseFloat(String(c.TotalCharges ?? 0)) || 0;

    // 分組
    patterns.contract[c.Contract] = (patterns.contract[c.Contract] ?? 0) + 1;
    patterns.paymentMethod[c.PaymentMethod] =
      (patterns.paymentMethod[c.PaymentMethod] ?? 0) + 1;

    // 分箱：tenure
    if (c.tenure <= 12) tenureBins['0-12']++;
    else if (c.tenure <= 24) tenureBins['13-24']++;
    else if (c.tenure <= 48) tenureBins['25-48']++;
    else tenureBins['49+']++;

    // 分箱：MonthlyCharges
    const m = Number(c.MonthlyCharges ?? 0);
    if (m <= 35) chargeBins['0-35']++;
    else if (m <= 65) chargeBins['36-65']++;
    else if (m <= 95) chargeBins['66-95']++;
    else chargeBins['96+']++;
  }

  const pctify = (count: number) => (n ? +(count / n * 100).toFixed(2) : 0);

  const summary: Summary = {
    generated_at: new Date().toISOString(),
    totals: { churned: n },
    averages: {
      avgTenure: n ? +(sumTenure / n).toFixed(2) : 0,
      avgMonthly: n ? +(sumMonthly / n).toFixed(2) : 0,
      avgTotal: n ? +(sumTotal / n).toFixed(2) : 0,
    },
    by_contract: Object.entries(patterns.contract).map(([key, count]) => ({
      key,
      count,
      pct: pctify(count),
    })),
    by_payment: Object.entries(patterns.paymentMethod).map(([key, count]) => ({
      key,
      count,
      pct: pctify(count),
    })),
    tenure_ranges: Object.entries(tenureBins).map(([range, count]) => ({
      range,
      count,
      pct: pctify(count),
    })),
    monthly_charge_ranges: Object.entries(chargeBins).map(([range, count]) => ({
      range,
      count,
      pct: pctify(count),
    })),
  };

  return summary;
}
