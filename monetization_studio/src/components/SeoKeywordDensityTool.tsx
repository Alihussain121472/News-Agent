import React, { useState } from 'react';
import {
  SAMPLE_ARTICLE_PRESETS,
  analyzeSeoKeywordDensity,
  HighCpmKeywordEntry,
} from '../utils/monetizationEngine';
import { Plus, Copy, Check, RotateCcw } from 'lucide-react';

export const SeoKeywordDensityTool: React.FC = () => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>(SAMPLE_ARTICLE_PRESETS[0].id);
  const [articleText, setArticleText] = useState<string>(SAMPLE_ARTICLE_PRESETS[0].content);
  const [primaryKeyword, setPrimaryKeyword] = useState<string>(
    SAMPLE_ARTICLE_PRESETS[0].primaryKeyword
  );
  const [categoryFilter, setCategoryFilter] = useState<string>('All');
  const [copiedArticle, setCopiedArticle] = useState<boolean>(false);
  const [lastInjectedPhrase, setLastInjectedPhrase] = useState<string | null>(null);

  const analysis = analyzeSeoKeywordDensity(articleText, primaryKeyword, categoryFilter);

  const handleSelectPreset = (presetId: string) => {
    const found = SAMPLE_ARTICLE_PRESETS.find((p) => p.id === presetId);
    if (found) {
      setSelectedPresetId(found.id);
      setArticleText(found.content);
      setPrimaryKeyword(found.primaryKeyword);
      setLastInjectedPhrase(null);
    }
  };

  const handleInjectHighCpmSentence = (entry: HighCpmKeywordEntry) => {
    const trimmed = articleText.trim();
    const nextText = trimmed
      ? `${trimmed}\n\n${entry.injectionSentence}`
      : entry.injectionSentence;
    setArticleText(nextText);
    setLastInjectedPhrase(entry.phrase);
  };

  const handleCopyArticle = () => {
    navigator.clipboard.writeText(articleText);
    setCopiedArticle(true);
    setTimeout(() => setCopiedArticle(false), 1800);
  };

  const categories = [
    'All',
    'Cloud & Infrastructure',
    'Databases & Data',
    'Cybersecurity & Zero Trust',
    'AI & MLOps',
    'DevOps & Kubernetes',
    'Career & Accredited Certs',
  ];

  return (
    <div className="space-y-10">
      {/* Main Analyzer Workbench */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              AdSense Contextual Auction Optimizer · Real-Time Keyword Density & High-CPM Bid Scanner
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              SEO Keyword Density & High-CPM Content Analyzer
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Google AdSense uses contextual crawlers (<code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">Mediapartners-Google</code>) to match your article text with enterprise advertisers. Paste your draft or load a live <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">novabrief.tech</code> article below to audit keyword density (<code className="font-mono text-xs">0.8%–2.5%</code> target) and inject high-CPM B2B phrases with one click.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {SAMPLE_ARTICLE_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleSelectPreset(preset.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition whitespace-nowrap shrink-0 ${
                  selectedPresetId === preset.id
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* 4-Column Live Telemetry Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 py-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500">Estimated Contextual Ad eCPM</div>
            <div className="text-2xl font-bold text-emerald-700 font-mono tabular-nums mt-1">
              ${analysis.estimatedContextualCpmUsd.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {analysis.detectedHighCpmKeywords.length} high-CPM advertiser triggers active
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Primary Keyword Density</div>
            <div
              className={`text-2xl font-bold font-mono tabular-nums mt-1 ${
                analysis.primaryKeywordStatus === 'Optimal (0.8%–2.5%)'
                  ? 'text-blue-600'
                  : analysis.primaryKeywordStatus === 'Over-Optimized (>2.5%)'
                  ? 'text-red-600'
                  : 'text-amber-700'
              }`}
            >
              {analysis.primaryKeywordDensityPct.toFixed(2)}% ({analysis.primaryKeywordCount}x)
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Status: {analysis.primaryKeywordStatus}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Article Word Count & Read Time</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              {analysis.wordCount.toLocaleString()} words
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              ~{analysis.readingTimeMinutes} min read · {analysis.characterCount.toLocaleString()} chars
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Recommended In-Article Ad Slots</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              {Math.max(2, Math.min(5, Math.floor(analysis.wordCount / 120) + 1))} Ad Units
            </div>
            <div className="text-xs text-slate-500 mt-1">
              1 fluid unit every ~250–300 words
            </div>
          </div>
        </div>

        {/* Two-Column Editor + Live Keyword Density Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
          {/* Left 7 Cols: Content Editor & Primary Keyword Input */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div className="flex-1">
                <label
                  htmlFor="primary-keyword-input"
                  className="block text-xs font-semibold text-slate-700 mb-1"
                >
                  Target Primary SEO Keyword Phrase
                </label>
                <input
                  id="primary-keyword-input"
                  type="text"
                  value={primaryKeyword}
                  onChange={(e) => setPrimaryKeyword(e.target.value)}
                  placeholder="e.g. cloud architecture or postgresql database"
                  className="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleSelectPreset(selectedPresetId)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset Draft</span>
                </button>
                <button
                  type="button"
                  onClick={handleCopyArticle}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  {copiedArticle ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied Optimized Text</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Optimized Text</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="seo-article-textarea"
                  className="text-xs font-semibold text-slate-700"
                >
                  Blog Article Body Content (Paste from <code className="font-mono">novabrief.tech/blog/*</code>)
                </label>
                {lastInjectedPhrase && (
                  <span className="text-xs font-mono text-emerald-700">
                    Injected high-CPM trigger: "{lastInjectedPhrase}"
                  </span>
                )}
              </div>
              <textarea
                id="seo-article-textarea"
                rows={13}
                value={articleText}
                onChange={(e) => setArticleText(e.target.value)}
                placeholder="Paste your blog post draft here to analyze keyword density and high-CPM advertiser triggers..."
                className="w-full p-4 text-xs sm:text-sm text-slate-800 bg-slate-50 border border-slate-300 rounded-xl leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
          </div>

          {/* Right 5 Cols: Top Term Density Table + Detected High-CPM Triggers */}
          <div className="lg:col-span-5 space-y-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-1">
                Live Term Frequency & Keyword Stuffing Guard
              </h3>
              <p className="text-xs text-slate-500 mb-3">
                Keep core terms between <code className="font-mono">1.0%–2.5%</code>. Terms exceeding <code className="font-mono">2.8%</code> trigger Google Panda/Helpful Content over-optimization filters.
              </p>

              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600">
                      <th className="py-2.5 px-3">Term</th>
                      <th className="py-2.5 px-3 text-right">Count</th>
                      <th className="py-2.5 px-3 text-right">Density</th>
                      <th className="py-2.5 px-3 text-right">SEO Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {analysis.topTerms.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-slate-400">
                          Paste article content to calculate term frequency.
                        </td>
                      </tr>
                    ) : (
                      analysis.topTerms.map((item) => (
                        <tr key={item.term} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-mono font-medium text-slate-900">
                            {item.term}
                          </td>
                          <td className="py-2 px-3 text-right font-mono text-slate-600 tabular-nums">
                            {item.count}x
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-semibold text-slate-900 tabular-nums">
                            {item.densityPct.toFixed(2)}%
                          </td>
                          <td
                            className={`py-2 px-3 text-right font-medium ${
                              item.status === 'Optimal (1.0%–2.5%)'
                                ? 'text-emerald-700'
                                : item.status === 'Stuffing Risk (>2.8%)'
                                ? 'text-red-600'
                                : 'text-slate-500'
                            }`}
                          >
                            {item.status}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Active High-CPM Keywords Found in Draft */}
            <div className="pt-2 border-t border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-bold text-slate-900">
                  Detected High-CPM Phrases in Draft ({analysis.detectedHighCpmKeywords.length})
                </h4>
                <span className="text-xs text-slate-500 font-mono">
                  Active AdSense Auction Signals
                </span>
              </div>

              {analysis.detectedHighCpmKeywords.length === 0 ? (
                <p className="text-xs text-slate-500 py-3">
                  No high-CPM enterprise phrases detected yet. Click <strong>"Insert Phrase"</strong> in the suggestion table below to boost your article's contextual ad auction rate.
                </p>
              ) : (
                <div className="divide-y divide-slate-200 border border-slate-200 rounded-xl">
                  {analysis.detectedHighCpmKeywords.map(({ entry, occurrences, densityPct }) => (
                    <div
                      key={entry.phrase}
                      className="p-3 flex items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <div className="font-mono font-bold text-slate-900">
                          {entry.phrase}
                        </div>
                        <div className="text-slate-500">
                          {entry.category} · {occurrences}x ({densityPct.toFixed(2)}% density)
                        </div>
                      </div>
                      <div className="text-right font-mono shrink-0 tabular-nums">
                        <div className="font-bold text-emerald-700">
                          ${entry.estimatedCpmUsd.toFixed(2)} CPM
                        </div>
                        <div className="text-slate-500">
                          ${entry.estimatedCpcUsd.toFixed(2)} CPC
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* High-CPM Keyword Suggestions & 1-Click Sentence Injector */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Contextual Ad Revenue Booster · Missing High-Bidding Advertiser Keywords
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              Suggested High-CPM Keywords to Target in This Article
            </h3>
            <p className="text-sm text-slate-600 mt-0.5">
              Adding 2–3 of these high-bidding B2B phrases into your H2 subheadings and opening paragraphs signals Google AdSense to serve enterprise Cloud, FinOps, Cybersecurity, and AI infrastructure ads instead of generic consumer ads.
            </p>
          </div>

          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg self-start overflow-x-auto max-w-full shrink-0">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap shrink-0 ${
                  categoryFilter === cat
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {cat === 'All' ? 'All' : cat.split(' & ')[0]}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-xl mt-6">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600">
                <th className="py-3 px-4">High-CPM Keyword Phrase</th>
                <th className="py-3 px-4">Best Placement Zone</th>
                <th className="py-3 px-4 text-right">Est. CPC Bid</th>
                <th className="py-3 px-4 text-right">Est. Ad eCPM</th>
                <th className="py-3 px-4">Suggested Contextual Sentence</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {analysis.missingHighCpmSuggestions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    All high-CPM keywords in this category are already present in your draft!
                  </td>
                </tr>
              ) : (
                analysis.missingHighCpmSuggestions.map((entry) => (
                  <tr key={entry.phrase} className="hover:bg-slate-50">
                    <td className="py-3.5 px-4 align-top">
                      <div className="font-mono font-bold text-slate-900">{entry.phrase}</div>
                      <div className="text-slate-500 mt-0.5">{entry.category}</div>
                    </td>
                    <td className="py-3.5 px-4 align-top text-slate-700 font-medium whitespace-nowrap">
                      {entry.placementTarget}
                    </td>
                    <td className="py-3.5 px-4 align-top text-right font-mono font-semibold text-slate-900 tabular-nums whitespace-nowrap">
                      ${entry.estimatedCpcUsd.toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4 align-top text-right font-mono font-bold text-emerald-700 tabular-nums whitespace-nowrap">
                      ${entry.estimatedCpmUsd.toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4 align-top text-slate-600 max-w-md leading-relaxed">
                      "{entry.injectionSentence}"
                    </td>
                    <td className="py-3.5 px-4 align-top text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => handleInjectHighCpmSentence(entry)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition whitespace-nowrap shrink-0"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Insert Phrase</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
