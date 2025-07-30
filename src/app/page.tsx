'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface Customer {
  customerID: string
  gender: string
  SeniorCitizen: number
  Partner: string
  Dependents: string
  tenure: number
  PhoneService: string
  MultipleLines: string
  InternetService: string
  OnlineSecurity: string
  OnlineBackup: string
  DeviceProtection: string
  TechSupport: string
  StreamingTV: string
  StreamingMovies: string
  Contract: string
  PaperlessBilling: string
  PaymentMethod: string
  MonthlyCharges: number
  TotalCharges: number
  Churn: string
}

interface AnalysisSummary {
  churnRate?: number
  averages?: {
    tenure?: number
    monthlyCharges?: number
    totalCharges?: number
  }
  segments?: Array<{ segment: string; churnRate: number }>
  topDrivers?: Array<{ feature: string; importance: number }>
  generatedAt?: string
  note?: string
  [key: string]: any
}

// 🆕 工具：安全轉 number（字串/百分比都可）
const toNumber = (v: any): number | undefined => {
  if (v === undefined || v === null) return undefined
  if (typeof v === 'number' && !Number.isNaN(v)) return v
  if (typeof v === 'string') {
    const cleaned = v.trim().replace(/%/g, '').replace(/,/g, '')
    const n = Number(cleaned)
    return Number.isNaN(n) ? undefined : n
  }
  return undefined
}

// 🆕 正規化：把 /api/analyze 的 raw 對齊到 UI 期望的鍵名
const normalizeSummary = (raw: any): AnalysisSummary => {
  const s = raw?.summary ?? raw?.data ?? raw ?? {}

  const avgTenure = toNumber(s.averages?.avgTenure)
  const avgMonthly = toNumber(s.averages?.avgMonthly)
  const avgTotal = toNumber(s.averages?.avgTotal)

  return {
    // 先把原始資料攤開，下方再用我們想要的鍵名覆蓋，避免被 s.averages 蓋回去
    ...s,

    // 對齊成你 UI 使用的 camelCase
    generatedAt: s.generated_at,

    // 用我們整理後的 averages 覆蓋掉 s.averages
    averages: {
      tenure: avgTenure,
      monthlyCharges: avgMonthly,
      totalCharges: avgTotal,
    },

    // churnRate 先留空（由 Supabase 計算）
    churnRate: undefined,
  }
}

export default function Home() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [summary, setSummary] = useState<AnalysisSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // 🆕 新增：用 Supabase 計算 churn rate（churned/total）
  const [computedChurnRate, setComputedChurnRate] = useState<number | undefined>(undefined)

  useEffect(() => {
    const fetchData = async () => {
      const { data, error } = await supabase
        .from('churn_customers')
        .select('*')
        .limit(10)

      if (error) {
        console.error('Supabase error:', error)
      } else {
        setCustomers(data)
      }
    }
    fetchData()
  }, [])

  // 🆕 計算 churn rate（不影響你原本取前 10 筆的 UI）
  useEffect(() => {
    let mounted = true
    const calcChurnRate = async () => {
      try {
        // 總筆數
        const { count: totalCount, error: totalErr } = await supabase
          .from('churn_customers')
          .select('*', { count: 'exact', head: true })
        if (totalErr) throw totalErr

        // churn=Yes 筆數
        const { count: churnedCount, error: churnErr } = await supabase
          .from('churn_customers')
          .select('*', { count: 'exact', head: true })
          .eq('Churn', 'Yes')
        if (churnErr) throw churnErr

        if (mounted && typeof totalCount === 'number' && totalCount > 0 && typeof churnedCount === 'number') {
          setComputedChurnRate(churnedCount / totalCount) // 0~1
        }
      } catch (e) {
        console.error('Compute churn rate error:', e)
        if (mounted) setComputedChurnRate(undefined)
      }
    }
    calcChurnRate()
    return () => { mounted = false }
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    const fetchSummary = async () => {
      try {
        setSummaryLoading(true)
        setSummaryError(null)
        const res = await fetch('/api/analyze', {
          method: 'GET',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' },
        })
        if (!res.ok) {
          const text = await res.text().catch(() => '')
          throw new Error(`Analyze API ${res.status}: ${text || res.statusText}`)
        }
        const data = await res.json()
        console.log('Analyze raw:', data)
        // 🆕 用 normalize 對齊鍵名
        const norm = normalizeSummary(data)
        setSummary(norm)
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error('Analyze API error:', err)
          setSummaryError(err.message || 'Failed to load summary')
        }
      } finally {
        setSummaryLoading(false)
      }
    }

    fetchSummary()
    return () => controller.abort()
  }, [])

  const formatPercent = (v?: number) => {
    if (v === undefined || v === null || Number.isNaN(v)) return '—'
    return v > 1 ? `${v.toFixed(1)}%` : `${(v * 100).toFixed(1)}%`
  }

  const formatNumber = (v?: number) =>
    v === undefined || v === null || Number.isNaN(v) ? '—' : Number(v).toLocaleString('en-US')

  return (
    <main className="p-4">
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
              <td className="border px-4 py-2">{customer.SeniorCitizen ? 'Yes' : 'No'}</td>
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
          <div className="rounded-lg border p-4 animate-pulse">
            正在載入摘要…
          </div>
        )}

        {summaryError && (
          <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
            無法載入摘要：{summaryError}
          </div>
        )}

        {!summaryLoading && !summaryError && summary && (
          <div className="space-y-4">
            {/* 關鍵 KPI 卡片 */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border p-4">
                <div className="text-sm text-gray-500">Churn Rate</div>
                <div className="text-2xl font-bold mt-1">
                  {formatPercent(
                    // 🆕 優先使用 Supabase 計算的值；未算到再 fallback API 的（若將來 API 有提供）
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
                    // 🆕 取 normalize 後的 averages.tenure（對齊 averages.avgTenure）
                    summary.averages?.tenure ??
                    summary.avgTenure ??           // 兼容舊鍵
                    summary.metrics?.avgTenure
                  )}
                </div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm text-gray-500">Avg Monthly Charges</div>
                <div className="text-2xl font-bold mt-1">
                  {formatNumber(
                    // 🆕 取 normalize 後的 averages.monthlyCharges（對齊 averages.avgMonthly）
                    summary.averages?.monthlyCharges ??
                    summary.avgMonthlyCharges ??    // 兼容舊鍵
                    summary.metrics?.avgMonthlyCharges
                  )}
                </div>
              </div>
            </div>

            {/* 產出時間 / 備註 */}
            {(summary.generatedAt || summary.note) ? (
              <div className="text-sm text-gray-600">
                {summary.generatedAt ? <>Generated at: {summary.generatedAt}</> : null}
                {summary.generatedAt && summary.note ? ' · ' : null}
                {summary.note ? <>Note: {summary.note}</> : null}
              </div>
            ) : null}

            {/* 可折疊：原始 JSON（方便 debug） */}
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
  )
}
