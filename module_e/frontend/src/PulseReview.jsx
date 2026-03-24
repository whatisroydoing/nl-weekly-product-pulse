import React, { useState } from 'react';
import {
  Download, Mail, CheckCircle, FileText, Loader2,
  MessageSquareQuote, Zap, Sparkles, ChevronLeft
} from 'lucide-react';

const API_BASE = '/api';

/* ─── Helpers ─── */

function sentimentForTheme(quotes, themeLabel) {
  const related = quotes.filter(q => q.theme_label === themeLabel);
  if (related.length === 0) return 50;
  const avg = related.reduce((s, q) => s + q.rating, 0) / related.length;
  return Math.round((avg / 5) * 100);
}

function sentimentColor(pct) {
  if (pct >= 60) return 'bg-emerald-500';
  if (pct >= 40) return 'bg-amber-500';
  return 'bg-red-500';
}

function sentimentTextColor(pct) {
  if (pct >= 60) return 'text-emerald-600';
  if (pct >= 40) return 'text-amber-600';
  return 'text-red-600';
}

/* ─── Component ─── */

export default function PulseReview({ pulse, pulseId, onBack }) {
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');
  const [emailOpen, setEmailOpen] = useState(false);
  const [emails, setEmails] = useState('');
  const [pdfLoading, setPdfLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  const { metadata, themes, quotes, summary_note, action_items, footer } = pulse;
  const topThemes = themes.filter(t => t.is_top_3);

  // Deep Dive tabs — default to first top-3 theme
  const [activeTab, setActiveTab] = useState(topThemes.length > 0 ? topThemes[0].label : '');

  const notify = (message, type = 'success') => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 4000);
  };

  const handlePdf = async () => {
    setPdfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/export/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pulse_id: pulseId }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'PDF export failed');
      window.open(`${API_BASE}/download/pdf/${pulseId}`, '_blank');
      notify('PDF exported successfully.');
    } catch (err) { notify(err.message, 'error'); }
    finally { setPdfLoading(false); }
  };

  const handleEmail = async () => {
    const list = emails.split(',').map(e => e.trim()).filter(Boolean);
    if (!list.length) return notify('Enter at least one email.', 'error');
    if (list.length > 5) return notify('Maximum 5 recipients.', 'error');
    setEmailLoading(true);
    try {
      const res = await fetch(`${API_BASE}/export/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pulse_id: pulseId, recipients: list }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Email failed');
      const data = await res.json();
      notify(data.message || `Sent to ${list.length} recipient(s).`);
      setEmailOpen(false);
      setEmails('');
    } catch (err) { notify(err.message, 'error'); }
    finally { setEmailLoading(false); }
  };

  const activeQuotes = quotes.filter(q => q.theme_label === activeTab);

  return (
    <div className="max-w-4xl mx-auto pb-32">
      {/* Toast */}
      {showToast && (
        <div className={`fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 z-50 ${
          toastType === 'error' ? 'bg-red-600 text-white' : 'bg-slate-800 text-white'
        }`}>
          <CheckCircle className={`w-5 h-5 ${toastType === 'error' ? 'text-red-200' : 'text-emerald-400'}`} />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* ── Back link only (no redundant header) ── */}
      <div className="mb-8 fade-up">
        <button onClick={onBack} className="flex items-center gap-1 text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors">
          <ChevronLeft className="w-4 h-4" /> Back to Report Generation
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--section-gap)' }}>

        {/* ══════ Section 1: Identified Themes ══════ */}
        <section className="fade-up fade-up-1">
          <h2 className="section-heading">
            <FileText className="w-5 h-5 text-[var(--accent)]" />
            Identified Themes
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {themes.map((theme, i) => {
              const pct = sentimentForTheme(quotes, theme.label);
              return (
                <div
                  key={i}
                  className={`section-card fade-up fade-up-${Math.min(i + 1, 6)} ${
                    theme.is_top_3 ? 'theme-card-top3' : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold text-[var(--text-primary)] text-sm">{theme.label}</h3>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                      {theme.is_top_3 && (
                        <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 bg-[var(--top3-bg)] text-[var(--top3-accent)] rounded-full ring-1 ring-[var(--accent-ring)]">
                          Top 3
                        </span>
                      )}
                      <span className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider whitespace-nowrap">
                        {theme.review_count} Mentions
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-[var(--text-muted)]">Positive Sentiment</span>
                      <span className={`text-xs font-bold ${sentimentTextColor(pct)}`}>{pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full sentiment-bar ${sentimentColor(pct)}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ══════ Section 2: Deep Dive (Tabbed) ══════ */}
        <section className="fade-up fade-up-2">
          <h2 className="section-heading">
            <MessageSquareQuote className="w-5 h-5 text-[var(--accent)]" />
            Deep Dive
          </h2>

          {/* Tabs */}
          <div className="flex border-b border-[var(--section-border)] mb-5 overflow-x-auto">
            {topThemes.map((theme) => (
              <button
                key={theme.label}
                onClick={() => setActiveTab(theme.label)}
                className={`tab-btn ${activeTab === theme.label ? 'tab-btn-active' : ''}`}
              >
                {theme.label}
              </button>
            ))}
          </div>

          {/* Quotes for active tab */}
          <div className="space-y-3">
            {activeQuotes.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)] py-4 text-center">No quotes for this theme.</p>
            ) : (
              activeQuotes.map((quote, i) => (
                <div key={i} className="quote-card fade-up">
                  <p className="text-sm text-[var(--text-secondary)] italic leading-relaxed">
                    "{quote.text}"
                  </p>
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-slate-100 text-[var(--text-muted)] rounded">
                      {quote.theme_label}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded ${
                      quote.rating >= 4 ? 'bg-emerald-50 text-emerald-600' : quote.rating <= 2 ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-[var(--text-muted)]'
                    }`}>
                      {quote.rating}★
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* ══════ Section 3: Executive Summary (Single Essay) ══════ */}
        <section className="fade-up fade-up-3">
          <div className="bg-slate-900 rounded-[var(--section-radius)] p-6 md:p-8 text-white">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indmoney-400" />
              Executive Summary
            </h2>
            <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
              {summary_note}
            </div>
          </div>
        </section>

        {/* ══════ Section 4: Actionable Next Steps (Simplified) ══════ */}
        <section className="fade-up fade-up-4">
          <h2 className="section-heading">
            <Zap className="w-5 h-5 text-[var(--accent)]" />
            Actionable Next Steps
          </h2>
          <div className="space-y-4">
            {action_items.map((item, idx) => (
              <div key={item.id} className={`section-card fade-up fade-up-${Math.min(idx + 1, 6)}`}>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[var(--accent-light)] text-[var(--accent)] font-bold text-sm flex items-center justify-center flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[var(--text-primary)]">{item.title}</h3>
                    <p className="text-sm text-[var(--text-secondary)] mt-1 leading-relaxed">
                      {item.description}
                    </p>
                    <span className="inline-block mt-2 text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-slate-100 text-[var(--text-muted)] rounded">
                      {item.linked_theme}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Footer ── */}
        <div className="text-center text-xs text-[var(--text-muted)] font-medium pt-4">
          © 2026 INDMoney Product Analytics. Confidential.
        </div>
      </div>

      {/* ══════ Sticky Bottom CTA Bar ══════ */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-700 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <h3 className="text-white font-bold text-sm">Weekly Pulse Report Ready</h3>
            <p className="text-slate-400 text-xs mt-0.5">Review and share the complete insights with the executive stakeholders.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePdf}
              disabled={pdfLoading}
              className="flex items-center gap-2 px-4 py-2.5 bg-white text-slate-900 rounded-lg text-sm font-bold hover:bg-slate-100 transition-colors disabled:opacity-60"
            >
              {pdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Download PDF
            </button>

            <div className="relative">
              <button
                onClick={() => setEmailOpen(!emailOpen)}
                className="flex items-center gap-2 px-4 py-2.5 bg-indmoney-600 text-white rounded-lg text-sm font-bold hover:bg-indmoney-500 transition-colors"
              >
                <Mail className="w-4 h-4" />
                Send via Email
              </button>

              {emailOpen && (
                <div className="absolute bottom-full right-0 mb-2 w-80 bg-white rounded-xl shadow-2xl border border-[var(--section-border)] p-4 z-10">
                  <label className="block text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">
                    Recipients (Max 5, comma separated)
                  </label>
                  <input
                    type="text"
                    placeholder="product@indmoney.in, dev@indmoney.in"
                    className="w-full border border-[var(--section-border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] mb-3 focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition"
                    value={emails}
                    onChange={(e) => setEmails(e.target.value)}
                  />
                  <button
                    onClick={handleEmail}
                    disabled={emailLoading}
                    className="w-full bg-indmoney-600 text-white rounded-lg py-2 text-sm font-bold hover:bg-indmoney-700 transition disabled:opacity-60"
                  >
                    {emailLoading ? 'Sending...' : 'Send Report'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
