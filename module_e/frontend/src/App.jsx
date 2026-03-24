import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, FolderOpen, CheckCircle2, AlertCircle,
  History, BarChart3, ArrowRight, Star, Shield, Zap,
  Download
} from 'lucide-react';
import PulseReview from './PulseReview';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/* ─── Progress Steps (plain language) ─── */
const PROGRESS_STEPS = [
  { duration: 5000,  label: 'Collecting latest reviews…' },
  { duration: 5000,  label: 'Cleaning and preparing data…' },
  { duration: 15000, label: 'Finding patterns and themes…' },
  { duration: 0,     label: 'Building your report…' }, // runs until API returns
];

function App() {
  const [view, setView] = useState('generate');
  const [reviewCount, setReviewCount] = useState(200);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentPulse, setCurrentPulse] = useState(null);
  const [pulseId, setPulseId] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState(null);

  // Progress bar state
  const [progressStep, setProgressStep] = useState(0);
  const [progressPct, setProgressPct] = useState(0);
  const progressInterval = useRef(null);

  // Fetch history
  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (!res.ok) throw new Error('Failed to fetch history');
      setHistoryData(await res.json());
    } catch { setHistoryData([]); }
    finally { setHistoryLoading(false); }
  };

  useEffect(() => { if (view === 'history') fetchHistory(); }, [view]);

  // Simulated progress bar
  const startProgress = () => {
    setProgressStep(0);
    setProgressPct(0);
    let step = 0;
    let elapsed = 0;
    const tick = 200; // ms per tick

    progressInterval.current = setInterval(() => {
      elapsed += tick;
      const stepDef = PROGRESS_STEPS[step];

      if (stepDef.duration > 0 && elapsed >= stepDef.duration) {
        step = Math.min(step + 1, PROGRESS_STEPS.length - 1);
        elapsed = 0;
        setProgressStep(step);
      }

      // Calculate overall percentage (first 3 steps = 80%, last step fills to 95%)
      let basePct = 0;
      for (let i = 0; i < step; i++) basePct += (80 / 3);
      if (step < 3) {
        basePct += ((elapsed / PROGRESS_STEPS[step].duration) * (80 / 3));
      } else {
        basePct = 80 + Math.min(elapsed / 10000 * 15, 15); // slowly approach 95%
      }
      setProgressPct(Math.min(Math.round(basePct), 95));
    }, tick);
  };

  const stopProgress = () => {
    clearInterval(progressInterval.current);
    setProgressPct(100);
    setTimeout(() => {
      setProgressStep(0);
      setProgressPct(0);
    }, 500);
  };

  // Generate
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    startProgress();
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_count: reviewCount }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Generation failed (${res.status})`);
      }
      const data = await res.json();
      stopProgress();
      setPulseId(data.pulse_id);
      setCurrentPulse(data.pulse);
      setView('review');
    } catch (err) {
      stopProgress();
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // History download
  const handleHistoryDownload = async (reportId) => {
    try {
      // The history table only knows report.id, not pulse.id.
      // Sending history ID to export/pdf actually fails if not caught, but we leave it here for now or fix it.
      // The proper way is to directly trigger the download if pdf_path is available.
      window.open(`${API_BASE}/download/pdf/${reportId}`, '_blank');
    } catch (err) { console.error('Download error:', err); }
  };

  // View past report
  const handleViewReport = async (reportId) => {
    try {
      setHistoryLoading(true);
      const res = await fetch(`${API_BASE}/history/${reportId}`);
      if (!res.ok) throw new Error('Failed to fetch full report');
      const data = await res.json();
      setPulseId(data.pulse_id);
      setCurrentPulse(data.pulse);
      setView('review');
    } catch (err) {
      console.error('Error viewing report:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const REVIEW_OPTIONS = [
    { count: 200, time: '~30s', label: '200 Reviews' },
    { count: 300, time: '~45s', label: '300 Reviews' },
    { count: 400, time: '~60s', label: '400 Reviews' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* ── Navbar ── */}
      <nav className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 flex items-center bg-indmoney-600 text-white p-2 rounded-lg">
                <BarChart3 className="h-5 w-5" />
              </div>
              <span className="font-extrabold text-lg tracking-tight text-slate-900">
                INDMoney <span className="font-semibold text-slate-500">Weekly Pulse</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setView('generate')}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                  view === 'generate' || view === 'review'
                    ? 'bg-indmoney-50 text-indmoney-700 ring-1 ring-indmoney-200'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Sparkles className="h-4 w-4" /> New Pulse
              </button>
              <button
                onClick={() => setView('history')}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                  view === 'history'
                    ? 'bg-indmoney-50 text-indmoney-700 ring-1 ring-indmoney-200'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                <FolderOpen className="h-4 w-4" /> Past Reports
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* ══════════════ VIEW: GENERATE ══════════════ */}
        {view === 'generate' && (
          <div className="max-w-2xl mx-auto mt-8 fade-up">
            {/* Hero */}
            <div className="text-center mb-10 relative">
              {/* Decorative background orbs */}
              <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-80 h-80 bg-indmoney-100/40 rounded-full blur-3xl pointer-events-none" />
              <div className="absolute -top-8 left-1/4 w-40 h-40 bg-sky-100/50 rounded-full blur-2xl pointer-events-none" />

              <div className="relative">
                <div className="inline-flex items-center gap-2 bg-indmoney-50 text-indmoney-700 text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full mb-4 ring-1 ring-indmoney-200">
                  <Sparkles className="w-3.5 h-3.5" /> AI-Powered Analysis
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-3">
                  What's your audience <br />
                  <span className="bg-gradient-to-r from-indmoney-600 to-sky-500 bg-clip-text text-transparent">saying?</span>
                </h1>
                <p className="text-slate-500 max-w-md mx-auto">
                  Analyze Google Play reviews and get actionable insights in minutes.
                </p>
              </div>
            </div>

            {/* Pipeline steps */}
            <div className="flex items-center justify-center gap-2 mb-8 text-xs font-semibold text-slate-400">
              <span className="flex items-center gap-1 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
                <Star className="w-3.5 h-3.5 text-amber-400" /> Collect Reviews
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
              <span className="flex items-center gap-1 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
                <Shield className="w-3.5 h-3.5 text-emerald-400" /> Clean & Secure
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
              <span className="flex items-center gap-1 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
                <Zap className="w-3.5 h-3.5 text-indmoney-500" /> Generate Insights
              </span>
            </div>

            {/* Main card */}
            <div className="relative bg-white/80 backdrop-blur-xl shadow-lg ring-1 ring-slate-900/5 rounded-2xl p-8 fade-up fade-up-1">
              {/* Review count selector */}
              <label className="block text-sm font-bold text-slate-900 mb-3">
                How many reviews to analyze?
              </label>
              <div className="grid grid-cols-3 gap-3 mb-6">
                {REVIEW_OPTIONS.map(opt => (
                  <button
                    key={opt.count}
                    onClick={() => setReviewCount(opt.count)}
                    disabled={isGenerating}
                    className={`relative py-4 px-4 rounded-xl text-center transition-all border-2 ${
                      reviewCount === opt.count
                        ? 'bg-indmoney-50 border-indmoney-500 ring-4 ring-indmoney-100 shadow-sm'
                        : 'bg-white border-slate-200 hover:border-indmoney-300 hover:bg-indmoney-50/30'
                    } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="text-2xl font-extrabold text-slate-900">{opt.count}</div>
                    <div className="text-xs text-slate-500 mt-0.5">Latest Reviews</div>
                    <div className={`text-[10px] font-bold mt-1 ${
                      reviewCount === opt.count ? 'text-indmoney-600' : 'text-slate-400'
                    }`}>
                      Est. {opt.time}
                    </div>
                  </button>
                ))}
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-start gap-3 fade-up">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-red-800">Something went wrong</p>
                    <p className="text-xs text-red-600 mt-1">{error}</p>
                  </div>
                </div>
              )}

              {/* Progress bar (visible during generation) */}
              {isGenerating && (
                <div className="mb-5 fade-up">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-600">
                      {PROGRESS_STEPS[progressStep].label}
                    </span>
                    <span className="text-xs font-bold text-indmoney-600">
                      {progressPct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indmoney-500 to-sky-400 transition-all duration-300 ease-out"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Generate button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full flex items-center justify-center py-4 px-4 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-slate-900 to-slate-800 hover:from-slate-800 hover:to-slate-700 shadow-lg shadow-slate-900/10 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
              >
                {isGenerating ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Analyzing Reviews…
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Weekly Pulse
                  </>
                )}
              </button>

              <p className="text-[11px] text-slate-400 mt-3 text-center">
                Uses AI to find themes, surface key quotes, and create your report.
              </p>
            </div>
          </div>
        )}

        {/* ══════════════ VIEW: REVIEW ══════════════ */}
        {view === 'review' && currentPulse && (
          <PulseReview pulse={currentPulse} pulseId={pulseId} onBack={() => setView('generate')} />
        )}

        {/* ══════════════ VIEW: HISTORY ══════════════ */}
        {view === 'history' && (
          <div className="max-w-4xl mx-auto mt-4 fade-up">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">Past Reports</h2>
              <button
                onClick={() => setView('generate')}
                className="flex items-center gap-1.5 text-sm font-semibold text-indmoney-600 hover:text-indmoney-800 transition-colors"
              >
                <Sparkles className="w-4 h-4" /> Generate New
              </button>
            </div>
            <div className="bg-white shadow-sm ring-1 ring-slate-900/5 rounded-2xl overflow-hidden">
              {historyLoading ? (
                <div className="p-12 text-center text-slate-400">
                  <svg className="animate-spin h-8 w-8 text-slate-300 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Loading reports…
                </div>
              ) : historyData.length === 0 ? (
                <div className="p-12 text-center text-slate-400">
                  <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p className="font-semibold text-slate-500">No reports yet</p>
                  <p className="text-sm mt-1">Generate your first pulse to see it here.</p>
                  <button
                    onClick={() => setView('generate')}
                    className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-indmoney-600 text-white rounded-lg text-sm font-bold hover:bg-indmoney-500 transition-colors"
                  >
                    <Sparkles className="w-4 h-4" /> Create First Pulse
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Report</th>
                        <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Source</th>
                        <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Reviews</th>
                        <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Date</th>
                        <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider min-w-[200px]">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {historyData.map((report) => (
                        <tr key={report.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-900">
                            {report.report_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                            {report.source}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indmoney-50 text-indmoney-700 ring-1 ring-indmoney-200">
                              {report.review_count}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                            {report.generated_at}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                            <div className="flex items-center justify-end gap-3">
                              <button
                                onClick={() => handleViewReport(report.id)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-600 hover:text-indmoney-700 hover:bg-indmoney-50 font-bold transition-all"
                                title="View Pulse Details"
                              >
                                <Sparkles className="w-4 h-4" /> View
                              </button>
                              {report.pdf_path && (
                                <button
                                  onClick={() => handleHistoryDownload(report.id)}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indmoney-50 text-indmoney-700 border border-indmoney-100 hover:bg-indmoney-100 font-bold transition-all"
                                  title="Download PDF Report"
                                >
                                  <Download className="w-4 h-4" /> Download
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="mt-4 flex items-center justify-center text-xs text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1 opacity-50" />
              Showing last 3 reports
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
