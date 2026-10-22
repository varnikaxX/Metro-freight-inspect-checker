import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  ScanLine,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from "lucide-react";

// ---------- Mock Data ----------

const kpiData = [
  {
    label: "Total Scans Today",
    value: "4,812",
    delta: "+12.4% vs yesterday",
    deltaPositive: true,
    icon: ScanLine,
    accent: "text-sky-400",
    ring: "ring-sky-500/20",
  },
  {
    label: "System Compliance Rate",
    value: "91.7%",
    delta: "+0.8% vs last week",
    deltaPositive: true,
    icon: ShieldCheck,
    accent: "text-emerald-400",
    ring: "ring-emerald-500/20",
  },
  {
    label: "High-Priority Violations",
    value: "37",
    delta: "+5 since last shift",
    deltaPositive: false,
    icon: AlertTriangle,
    accent: "text-rose-400",
    ring: "ring-rose-500/20",
  },
];

const violationData = [
  { rule: "MRP Rule 6(1)(F)", short: "MRP", count: 128 },
  { rule: "Net Qty Rule 6(1)(D)", short: "Net Qty", count: 94 },
  { rule: "Mfr Details Rule 6(1)(A)", short: "Mfr Details", count: 61 },
  { rule: "Origin Rule 6(1)", short: "Origin", count: 39 },
];

const scans = [
  {
    id: "SCN-88213",
    timestamp: "2026-08-29 09:42:11",
    brand: "Parle Agro",
    status: "Pass",
    missing: "—",
  },
  {
    id: "SCN-88214",
    timestamp: "2026-08-29 09:41:47",
    brand: "Britannia Industries",
    status: "Fail",
    missing: "MRP, Net Quantity",
  },
  {
    id: "SCN-88215",
    timestamp: "2026-08-29 09:40:59",
    brand: "Dabur India",
    status: "Pass",
    missing: "—",
  },
  {
    id: "SCN-88216",
    timestamp: "2026-08-29 09:40:12",
    brand: "Haldiram's",
    status: "Fail",
    missing: "Manufacturer Address",
  },
  {
    id: "SCN-88217",
    timestamp: "2026-08-29 09:39:38",
    brand: "ITC Foods",
    status: "Pass",
    missing: "—",
  },
  {
    id: "SCN-88218",
    timestamp: "2026-08-29 09:38:54",
    brand: "Marico Limited",
    status: "Fail",
    missing: "Country of Origin",
  },
  {
    id: "SCN-88219",
    timestamp: "2026-08-29 09:38:02",
    brand: "Nestlé India",
    status: "Pass",
    missing: "—",
  },
  {
    id: "SCN-88220",
    timestamp: "2026-08-29 09:37:29",
    brand: "Amul (GCMMF)",
    status: "Fail",
    missing: "MRP, Manufacturer Address",
  },
  {
    id: "SCN-88221",
    timestamp: "2026-08-29 09:36:41",
    brand: "Patanjali Ayurved",
    status: "Pass",
    missing: "—",
  },
  {
    id: "SCN-88222",
    timestamp: "2026-08-29 09:35:58",
    brand: "Hindustan Unilever",
    status: "Fail",
    missing: "Net Quantity",
  },
];

// ---------- Small building blocks ----------

function KpiCard({ item }) {
  const Icon = item.icon;
  return (
    <div
      className={`rounded-xl bg-slate-800/50 border border-slate-700/50 p-5 ring-1 ${item.ring} backdrop-blur-sm`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{item.label}</p>
          <p className="mt-2 text-3xl font-semibold text-slate-100 tracking-tight">
            {item.value}
          </p>
        </div>
        <div className={`p-2.5 rounded-lg bg-slate-900/60 ${item.accent}`}>
          <Icon size={20} strokeWidth={2} />
        </div>
      </div>
      <p
        className={`mt-3 text-xs font-medium ${
          item.deltaPositive ? "text-emerald-400" : "text-rose-400"
        }`}
      >
        {item.delta}
      </p>
    </div>
  );
}

function StatusBadge({ status }) {
  const isPass = status === "Pass";
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
        isPass
          ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30"
          : "bg-rose-500/10 text-rose-400 ring-1 ring-rose-500/30"
      }`}
    >
      {isPass ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
      {status}
    </span>
  );
}

function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 shadow-lg">
        <p className="text-xs text-slate-400">{d.rule}</p>
        <p className="text-sm font-semibold text-slate-100">
          {d.count} violations
        </p>
      </div>
    );
  }
  return null;
}

const BAR_COLORS = ["#f43f5e", "#fb923c", "#facc15", "#38bdf8"];

// ---------- Main Component ----------

export default function CommandCenterDashboard() {
  const [liveScans, setLiveScans] = useState([]);
  const [violationStats, setViolationStats] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // This connects to the Python backend API
    fetch('http://127.0.0.1:8000/api/v1/history')
      .then(response => response.json())
      .then(data => {
        // 1. Format the table data
        const formattedScans = data.map(item => ({
          id: item.scan_id,
          timestamp: "Just Now",
          brand: "Scanned Item", 
          status: item.overall_status === "COMPLIANT" ? "PASS" : "FAIL",
          missingFields: item.findings
                           .filter(f => f.status !== "PASSED")
                           .map(f => f.field)
                           .join(", ")
        }));
        
        // 2. Count the violations for the Bar Chart
        const counts = {};
        data.forEach(scan => {
          scan.findings.forEach(finding => {
            if (finding.status !== "PASSED" && finding.status !== "NOT_EVALUATED") {
              counts[finding.message] = (counts[finding.message] || 0) + 1;
            }
          });
        });

        const chartData = Object.keys(counts).map(key => ({
          name: key,
          count: counts[key]
        }));

        // 3. Update the dashboard with real data
        setLiveScans(formattedScans);
        setViolationStats(chartData);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Backend connection failed:", error);
        setIsLoading(false); // Fails safe if backend is off
      });
  }, []);
  return (
    <div className="min-h-screen w-full bg-slate-900 text-slate-100 font-sans">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-50">
              Metrology Verify
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Analytics Dashboard
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-slate-800/50 border border-slate-700/50 px-3 py-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-medium text-slate-300">
              Live &middot; Updated just now
            </span>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {kpiData.map((item) => (
            <KpiCard key={item.label} item={item} />
          ))}
        </div>

        {/* Chart + side panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
          <div className="lg:col-span-2 rounded-xl bg-slate-800/50 border border-slate-700/50 p-5">
            <h2 className="text-sm font-semibold text-slate-200 mb-1">
              Top Rule Violations
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Legal Metrology (Packaged Commodities) Rules, 2011
            </p>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={violationStats}
                  margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                  barCategoryGap="28%"
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="short"
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "#334155" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "#334155" }}
                    tickLine={false}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    cursor={{ fill: "#1e293b", opacity: 0.5 }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={56}>
                    {violationStats.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={BAR_COLORS[index % BAR_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-5">
            <h2 className="text-sm font-semibold text-slate-200 mb-4">
              Violation Breakdown
            </h2>
            <ul className="space-y-3">
              {violationStats.map((v, i) => (
                <li key={v.rule} className="flex items-center gap-3">
                  <span
                    className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: BAR_COLORS[i % BAR_COLORS.length] }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 truncate">{v.rule}</p>
                  </div>
                  <span className="text-xs font-semibold text-slate-100">
                    {v.count}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recent Scans Table */}
        <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">
              Recent Scans
            </h2>
            <span className="text-xs text-slate-500">
              Showing {scans.length} of 4,812
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700/70">
                  <th className="py-2.5 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Scan ID
                  </th>
                  <th className="py-2.5 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Timestamp
                  </th>
                  <th className="py-2.5 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Brand
                  </th>
                  <th className="py-2.5 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Status
                  </th>
                  <th className="py-2.5 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Missing Fields
                  </th>
                </tr>
              </thead>
              <tbody>
                {liveScans.map((scan) => (
                  <tr
                    key={scan.id}
                    className="border-b border-slate-800 hover:bg-slate-700/20 transition-colors"
                  >
                    <td className="py-3 pr-4 text-sm font-mono text-slate-300">
                      {scan.id}
                    </td>
                    <td className="py-3 pr-4 text-sm text-slate-400">
                      {scan.timestamp}
                    </td>
                    <td className="py-3 pr-4 text-sm text-slate-200">
                      {scan.brand}
                    </td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={scan.status} />
                    </td>
                    <td className="py-3 pr-4 text-sm text-slate-400">
                      {scan.missing}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
