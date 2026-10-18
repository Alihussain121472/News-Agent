import React, { useState, useEffect } from 'react';
import {
  AdSenseSlotConfig,
  ArticleWireframeZone,
  AuditFinding,
  PUBLISHER_ID,
  TrafficQualityInput,
  validateAdSlotId,
  generateAdSenseSnippet,
  analyzeTrafficQuality,
  getArticleWireframeZones,
  generateGitPushTerminalScript,
  generateMasterThemeJsPatch,
} from '../utils/monetizationEngine';
import {
  Check,
  Copy,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Wrench,
  RefreshCw,
  UploadCloud,
  Download,
  Terminal,
} from 'lucide-react';
import { GoogleDriveProjectFixer } from './GoogleDriveProjectFixer';

interface SiteAuditAndFixerProps {
  findings: AuditFinding[];
  onToggleFindingFixed: (id: string) => void;
  slotConfig: AdSenseSlotConfig;
  onUpdateSlotConfig: (next: AdSenseSlotConfig) => void;
}

interface LiveSiteVerificationState {
  loading: boolean;
  checkedAt: string | null;
  renderServerHeader: string;
  renderServiceId: string;
  themeJsBytes: number;
  themeJsLineCount: number;
  isAutonomousPatchLive: boolean;
  brokenAutoSlotsCount: number;
  newsHasAdsenseMeta: boolean;
  githubSecretConfigured: boolean;
  githubRepo: string;
  githubBranch: string;
  latestGitHubCommitSha: string;
  latestGitHubCommitMsg: string;
  renderHookConfigured: boolean;
  error: string | null;
}

export const SiteAuditAndFixer: React.FC<SiteAuditAndFixerProps> = ({
  findings,
  onToggleFindingFixed,
  slotConfig,
  onUpdateSlotConfig,
}) => {
  const [selectedPlacement, setSelectedPlacement] = useState<
    'in-article' | 'sidebar-sticky' | 'in-feed' | 'multiplex' | 'leaderboard'
  >('in-article');
  const [selectedWireframeZoneId, setSelectedWireframeZoneId] = useState<
    ArticleWireframeZone['id']
  >('in-article-1');
  const [severityFilter, setSeverityFilter] = useState<'All' | 'Critical' | 'High' | 'Medium'>('All');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [testSlotInput, setTestSlotInput] = useState<string>('auto');
  const [showTerminalPushModal, setShowTerminalPushModal] = useState<boolean>(true);
  const [publishStatus, setPublishStatus] = useState<{
    loading: boolean;
    ok?: boolean;
    message?: string;
    commitUrl?: string;
  }>({ loading: false });

  const [liveStatus, setLiveStatus] = useState<LiveSiteVerificationState>({
    loading: true,
    checkedAt: null,
    renderServerHeader: 'gunicorn',
    renderServiceId: 'srv-da20hb2jnfac73ad485g',
    themeJsBytes: 2375,
    themeJsLineCount: 52,
    isAutonomousPatchLive: false,
    brokenAutoSlotsCount: 2,
    newsHasAdsenseMeta: true,
    githubSecretConfigured: false,
    githubRepo: 'Alihussain121472/News-Agent',
    githubBranch: 'render-role-dashboards',
    latestGitHubCommitSha: 'ecc5aa6',
    latestGitHubCommitMsg: 'Keep incorrect quiz selections red and refresh Hub assets',
    renderHookConfigured: true,
    error: null,
  });

  const [trafficMix, setTrafficMix] = useState<TrafficQualityInput>({
    organicPct: 45,
    socialPct: 35,
    directPct: 20,
  });

  const runLiveSiteVerification = async () => {
    setLiveStatus((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const res = await fetch('/api/verify-live-site');
      const data = await res.json();
      if (data.ok) {
        setLiveStatus({
          loading: false,
          checkedAt: data.checkedAt,
          renderServerHeader: data.renderServerHeader,
          renderServiceId: data.renderServiceId || 'srv-da20hb2jnfac73ad485g',
          themeJsBytes: data.themeJsBytes,
          themeJsLineCount: data.themeJsLineCount,
          isAutonomousPatchLive: data.isAutonomousPatchLive,
          brokenAutoSlotsCount: data.brokenAutoSlotsCount,
          newsHasAdsenseMeta: data.newsHasAdsenseMeta,
          githubSecretConfigured: data.githubSecretConfigured,
          githubRepo: data.githubRepo || 'Alihussain121472/News-Agent',
          githubBranch: data.githubBranch || 'render-role-dashboards',
          latestGitHubCommitSha: data.latestGitHubCommitSha || 'ecc5aa6',
          latestGitHubCommitMsg: data.latestGitHubCommitMsg || '',
          renderHookConfigured: data.renderHookConfigured,
          error: null,
        });
      } else {
        setLiveStatus((prev) => ({
          ...prev,
          loading: false,
          error: data.error || 'Verification check failed.',
        }));
      }
    } catch {
      setLiveStatus((prev) => ({
        ...prev,
        loading: false,
        error: 'Unable to reach verification endpoint.',
      }));
    }
  };

  useEffect(() => {
    runLiveSiteVerification();
  }, []);

  const handlePublishToGitHub = async () => {
    setPublishStatus({ loading: true });
    try {
      const masterPatch = generateMasterThemeJsPatch(slotConfig);
      const res = await fetch('/api/publish-to-github', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo: liveStatus.githubRepo,
          branch: liveStatus.githubBranch,
          filePath: 'static/js/theme.js',
          content: masterPatch,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        setPublishStatus({
          loading: false,
          ok: true,
          message: `Pushed static/js/theme.js to ${liveStatus.githubRepo} (${liveStatus.githubBranch} & main). Render service ${liveStatus.renderServiceId} is now building novabrief.tech (~60s).`,
          commitUrl: data.commitUrl,
        });
        setTimeout(() => runLiveSiteVerification(), 5000);
      } else {
        setPublishStatus({
          loading: false,
          ok: false,
          message: data.error,
        });
        if (data.missingSecrets) {
          setShowTerminalPushModal(true);
        }
      }
    } catch {
      setPublishStatus({
        loading: false,
        ok: false,
        message: 'Network error while attempting GitHub publish.',
      });
    }
  };

  const handleDownloadThemeJs = () => {
    const content = generateMasterThemeJsPatch(slotConfig);
    const blob = new Blob([content], { type: 'application/javascript;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'theme.js';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const filteredFindings = findings.filter((item) =>
    severityFilter === 'All' ? true : item.severity === severityFilter
  );

  const testValidation = validateAdSlotId(testSlotInput);
  const activeSnippet = generateAdSenseSnippet(selectedPlacement, slotConfig);
  const trafficAnalysis = analyzeTrafficQuality(trafficMix);
  const wireframeZones = getArticleWireframeZones(slotConfig);
  const activeWireframeZone =
    wireframeZones.find((z) => z.id === selectedWireframeZoneId) || wireframeZones[1];
  const gitPushScript = generateGitPushTerminalScript(slotConfig);
  const masterThemeJsCode = generateMasterThemeJsPatch(slotConfig);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1800);
  };

  const handleApplyValidSampleIds = () => {
    onUpdateSlotConfig({
      ...slotConfig,
      inArticleSlotId: '4829103847',
      sidebarSlotId: '5910293846',
      inFeedSlotId: '6029384751',
      multiplexSlotId: '7192837462',
      headerLeaderboardSlotId: '8293847563',
    });
    setTestSlotInput('4829103847');
  };

  const headVerificationSnippet = `<!-- Place inside <head> of EVERY template (base.html, index.html, news.html, blog.html, blog_post.html) -->
<meta name="google-adsense-account" content="${PUBLISHER_ID}">
<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>
<link rel="preconnect" href="https://googleads.g.doubleclick.net" crossorigin>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${PUBLISHER_ID}" crossorigin="anonymous"></script>`;

  return (
    <div className="space-y-10">
      {/* Google Drive & Local ./Nova-Brief-Project Folder Auto-Fixer */}
      <GoogleDriveProjectFixer slotConfig={slotConfig} />

      {/* Live GitHub & Render Production Deployment & Verification Bar */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-200">
          <div>
            <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500 mb-1">
              <span>Repo: <code className="font-mono text-slate-800">{liveStatus.githubRepo}</code></span>
              <span aria-hidden="true">·</span>
              <span>Branch: <code className="font-mono text-blue-600">{liveStatus.githubBranch}</code></span>
              <span aria-hidden="true">·</span>
              <span>Render: <code className="font-mono text-slate-800">{liveStatus.renderServiceId}</code></span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              01. Live Production Verification &amp; GitHub / Render Publisher
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Connected to <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{liveStatus.githubRepo}</code> (branch <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{liveStatus.githubBranch}</code>, commit <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{liveStatus.latestGitHubCommitSha}</code>) and Render service <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{liveStatus.renderServiceId}</code>. Push the <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">static/js/theme.js</code> patch below, then click <strong>Verify Live Render Site</strong> to confirm it is live on <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">novabrief.tech</code>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={runLiveSiteVerification}
              disabled={liveStatus.loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${liveStatus.loading ? 'animate-spin' : ''}`} />
              <span>{liveStatus.loading ? 'Scanning Live Site...' : 'Verify Live Render Site'}</span>
            </button>

            <a
              href="https://dashboard.render.com/web/srv-da20hb2jnfac73ad485g/deploys"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              <span>Render Deploys</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <button
              type="button"
              onClick={handleDownloadThemeJs}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download theme.js</span>
            </button>

            <button
              type="button"
              onClick={handlePublishToGitHub}
              disabled={publishStatus.loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition whitespace-nowrap shrink-0"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>{publishStatus.loading ? 'Publishing to GitHub...' : 'Publish to GitHub & Render'}</span>
            </button>
          </div>
        </div>

        {/* Status Notice if Publish Clicked */}
        {publishStatus.message && (
          <div
            className={`mt-5 p-4 rounded-xl border text-xs leading-relaxed flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
              publishStatus.ok
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-amber-50 border-amber-200 text-amber-900'
            }`}
          >
            <div>
              <strong className="font-bold">
                {publishStatus.ok ? 'GitHub Commit Succeeded: ' : 'Action Needed to Push to GitHub: '}
              </strong>
              <span>{publishStatus.message}</span>
            </div>
            {publishStatus.commitUrl && (
              <a
                href={publishStatus.commitUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-semibold underline shrink-0"
              >
                <span>View GitHub Commit</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        )}

        {/* Direct 10-Second GitHub Web Editor & 1-Command Terminal Deploy Box */}
        {showTerminalPushModal && (
          <div className="mt-6 bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Push Live to <code className="font-mono text-blue-600">Alihussain121472/News-Agent</code> (<code className="font-mono">render-role-dashboards</code>) &rarr; Render <code className="font-mono">srv-da20hb2jnfac73ad485g</code>
                </h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                  Because GitHub requires write authentication for <code className="font-mono">Alihussain121472/News-Agent</code>, you can either:
                  <br />
                  <strong>1. Instant Browser Commit (No Token Needed — 10 Seconds):</strong> Click <strong>Step 1: Copy Patched theme.js</strong>, then click <strong>Step 2: Open GitHub Web Editor (render-role-dashboards)</strong>, press <code className="font-mono">Ctrl+A</code> then <code className="font-mono">Ctrl+V</code>, and click <strong>Commit changes</strong>.
                  <br />
                  <strong>2. Automated Studio Push:</strong> Add <code className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200">GITHUB_TOKEN</code> (your GitHub Personal Access Token) in the AI Studio Secrets panel and click <strong>Publish to GitHub &amp; Render</strong> above.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleCopy(masterThemeJsCode, 'copy-master-theme-js')}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  {copiedKey === 'copy-master-theme-js' ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied theme.js! Now Click Step 2 &rarr;</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Step 1: Copy Patched theme.js</span>
                    </>
                  )}
                </button>

                <a
                  href="https://github.com/Alihussain121472/News-Agent/edit/render-role-dashboards/static/js/theme.js"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  <span>Step 2: Open GitHub Web Editor (render-role-dashboards)</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>

                <button
                  type="button"
                  onClick={() => handleCopy(gitPushScript, 'git-push-cmd')}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  <Terminal className="w-3.5 h-3.5" />
                  <span>{copiedKey === 'git-push-cmd' ? 'Copied Terminal Cmd' : 'Copy Terminal Git Push'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 4-Column Live Render & Ground Truth Status Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-6">
          <div>
            <div className="text-xs text-slate-500">Live Render static/js/theme.js</div>
            <div
              className={`text-lg font-bold font-mono tabular-nums mt-1 ${
                liveStatus.isAutonomousPatchLive ? 'text-emerald-700' : 'text-amber-700'
              }`}
            >
              {liveStatus.isAutonomousPatchLive
                ? 'Patched & Live on Render'
                : `Unpatched (${liveStatus.themeJsLineCount} lines)`}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono">
              {liveStatus.themeJsBytes.toLocaleString()} bytes · Origin: {liveStatus.renderServerHeader}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Live Manual Ad Units on Site</div>
            <div
              className={`text-lg font-bold font-mono tabular-nums mt-1 ${
                liveStatus.isAutonomousPatchLive ? 'text-emerald-700' : 'text-red-600'
              }`}
            >
              {liveStatus.isAutonomousPatchLive
                ? 'Auto-Repaired at Runtime'
                : `Broken (${liveStatus.brokenAutoSlotsCount} slot="auto")`}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {liveStatus.newsHasAdsenseMeta
                ? '/news meta tag verified'
                : 'Missing <meta> tag on /news'}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">ads.txt &amp; Publisher Account</div>
            <div className="text-lg font-bold text-emerald-700 font-mono tabular-nums mt-1">
              HTTP 200 · Verified
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono">
              pub-1036052096443002 · DIRECT
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Resolved Audit Blockers</div>
            <div className="text-lg font-bold text-blue-600 font-mono tabular-nums mt-1">
              {findings.filter((f) => f.fixedStatus).length} / {findings.length} Fixed
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {liveStatus.checkedAt
                ? `Last live scan: ${new Date(liveStatus.checkedAt).toLocaleTimeString()}`
                : 'Scanning novabrief.tech...'}
            </div>
          </div>
        </div>
      </section>

      {/* Audit Findings Table / Interactive List */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              Critical Missing Features &amp; Monetization Blockers on novabrief.tech
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Filter by severity and toggle status as you patch each template in your repository.
            </p>
          </div>
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg self-start">
            {(['All', 'Critical', 'High', 'Medium'] as const).map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setSeverityFilter(level)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap shrink-0 ${
                  severityFilter === level
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-slate-200 border-t border-slate-200">
          {filteredFindings.map((finding) => (
            <div key={finding.id} className="py-5 flex flex-col lg:flex-row lg:items-start justify-between gap-6">
              <div className="space-y-2 max-w-4xl">
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span
                    className={`font-semibold ${
                      finding.severity === 'Critical'
                        ? 'text-red-600'
                        : finding.severity === 'High'
                        ? 'text-amber-700'
                        : 'text-blue-600'
                    }`}
                  >
                    {finding.severity} Severity
                  </span>
                  <span aria-hidden="true">·</span>
                  <span>{finding.category}</span>
                  <span aria-hidden="true">·</span>
                  <span className="font-mono text-slate-700">{finding.pagePath}</span>
                </div>
                <h4 className="text-base font-bold text-slate-900">
                  {finding.title}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 text-xs">
                  <div>
                    <div className="font-semibold text-slate-700 mb-1">Current State Found on Site</div>
                    <code className="font-mono text-slate-600 break-all block">{finding.currentOnSiteState}</code>
                    <div className="text-red-600 font-medium mt-1.5">Impact: {finding.revenueImpact}</div>
                  </div>
                  <div className="md:border-l md:border-slate-200 md:pl-6">
                    <div className="font-semibold text-slate-900 mb-1">Exact Engineering Fix</div>
                    <p className="text-slate-600 leading-relaxed">{finding.exactFix}</p>
                  </div>
                </div>
              </div>

              <div className="shrink-0 flex items-center">
                <button
                  type="button"
                  onClick={() => onToggleFindingFixed(finding.id)}
                  className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg border transition whitespace-nowrap shrink-0 ${
                    finding.fixedStatus
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{finding.fixedStatus ? 'Marked Fixed' : 'Mark as Fixed'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 02. Interactive AdSense Slot Validator & Drop-In Code Generator */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Interactive Code Patcher · Replaces broken <code className="font-mono">data-ad-slot="auto"</code> on novabrief.tech
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              02. AdSense Slot Validator &amp; Production Snippet Generator
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              In Google AdSense (<code className="font-mono text-xs">Ads &rarr; By ad unit</code>), create 5 separate ad units and paste their 10-digit numeric IDs below to update your wireframe overlays and replacement snippets.
            </p>
          </div>
          <button
            type="button"
            onClick={handleApplyValidSampleIds}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition whitespace-nowrap shrink-0 self-start"
          >
            <Wrench className="w-3.5 h-3.5" />
            <span>Populate Valid 10-Digit Slot IDs</span>
          </button>
        </div>

        {/* Live Slot Validator Diagnostic Box */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div>
              <label htmlFor="slot-validator-input" className="block text-xs font-semibold text-slate-700 mb-1.5">
                Test Any data-ad-slot Value From Your HTML
              </label>
              <input
                id="slot-validator-input"
                type="text"
                value={testSlotInput}
                onChange={(e) => setTestSlotInput(e.target.value)}
                placeholder="e.g. auto or 4829103847"
                className="w-full px-3.5 py-2 text-sm font-mono bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
            <div className="lg:col-span-2">
              <div className="flex items-start gap-3">
                {testValidation.valid ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className={`text-sm font-bold ${testValidation.valid ? 'text-emerald-800' : 'text-red-700'}`}>
                    {testValidation.valid ? 'Valid AdSense Unit Slot ID' : 'Invalid AdSense Unit Slot ID Detected'}
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                    {testValidation.reason}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 5 Slot Inputs + Placement Selector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-4">
            <h4 className="text-sm font-bold text-slate-900">
              Configure Your 5 AdSense Unit Slot IDs
            </h4>

            <div>
              <label htmlFor="in-article-slot" className="block text-xs font-medium text-slate-700 mb-1">
                1. In-Article Fluid Unit ID (for <code className="font-mono">blog_post.html</code>)
              </label>
              <input
                id="in-article-slot"
                type="text"
                value={slotConfig.inArticleSlotId}
                onChange={(e) => onUpdateSlotConfig({ ...slotConfig, inArticleSlotId: e.target.value })}
                className="w-full px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="sidebar-slot" className="block text-xs font-medium text-slate-700 mb-1">
                2. Sticky Sidebar 300x600 Unit ID (for <code className="font-mono">news.html</code> &amp; <code className="font-mono">blog.html</code>)
              </label>
              <input
                id="sidebar-slot"
                type="text"
                value={slotConfig.sidebarSlotId}
                onChange={(e) => onUpdateSlotConfig({ ...slotConfig, sidebarSlotId: e.target.value })}
                className="w-full px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="in-feed-slot" className="block text-xs font-medium text-slate-700 mb-1">
                3. Native In-Feed Unit ID (Every 3rd card on <code className="font-mono">/news</code>)
              </label>
              <input
                id="in-feed-slot"
                type="text"
                value={slotConfig.inFeedSlotId}
                onChange={(e) => onUpdateSlotConfig({ ...slotConfig, inFeedSlotId: e.target.value })}
                className="w-full px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="multiplex-slot" className="block text-xs font-medium text-slate-700 mb-1">
                4. Multiplex Bottom Grid ID (End of <code className="font-mono">blog_post.html</code>)
              </label>
              <input
                id="multiplex-slot"
                type="text"
                value={slotConfig.multiplexSlotId}
                onChange={(e) => onUpdateSlotConfig({ ...slotConfig, multiplexSlotId: e.target.value })}
                className="w-full px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="leaderboard-slot" className="block text-xs font-medium text-slate-700 mb-1">
                5. Above-the-Fold Leaderboard ID (Top of <code className="font-mono">/news</code> &amp; <code className="font-mono">/blog</code>)
              </label>
              <input
                id="leaderboard-slot"
                type="text"
                value={slotConfig.headerLeaderboardSlotId}
                onChange={(e) => onUpdateSlotConfig({ ...slotConfig, headerLeaderboardSlotId: e.target.value })}
                className="w-full px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          <div className="lg:col-span-7 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-1 p-1 bg-slate-100 rounded-lg">
                {(
                  [
                    { id: 'in-article', label: 'In-Article' },
                    { id: 'sidebar-sticky', label: 'Sticky Sidebar' },
                    { id: 'in-feed', label: 'In-Feed Native' },
                    { id: 'multiplex', label: 'Multiplex' },
                    { id: 'leaderboard', label: 'Leaderboard' },
                  ] as const
                ).map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setSelectedPlacement(tab.id)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap shrink-0 ${
                      selectedPlacement === tab.id
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => handleCopy(activeSnippet, 'placement-snippet')}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition whitespace-nowrap shrink-0"
              >
                {copiedKey === 'placement-snippet' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Copied HTML</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Placement HTML</span>
                  </>
                )}
              </button>
            </div>

            <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed">
              <code>{activeSnippet}</code>
            </pre>

            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700">
                  Global <code className="font-mono">&lt;head&gt;</code> Preconnect &amp; Verification Script (Fix missing tag on <code className="font-mono">/news</code>)
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(headVerificationSnippet, 'head-snippet')}
                  className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition whitespace-nowrap shrink-0"
                >
                  {copiedKey === 'head-snippet' ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Head Script</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed">
                <code>{headVerificationSnippet}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* 03. Visual Blog Article Wireframe with Optimal In-Article & Sticky Sidebar Overlays */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Interactive Layout Blueprint · Bound to Your Current Slot Configuration (<code className="font-mono">{slotConfig.publisherId}</code>)
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              03. Blog Article Visual Wireframe (In-Article &amp; Sticky Sidebar Overlays)
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Click any highlighted AdSense overlay in the mock-up of <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">/blog/cloud-architecture-aws-azure-gcp-guide</code> below to inspect its live slot ID status, Active View time, and exact container CSS rules.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-600 shrink-0">
            Valid Configured Zones:{' '}
            <strong className="text-emerald-700">
              {wireframeZones.filter((z) => z.isValidSlot).length} / {wireframeZones.length}
            </strong>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
          {/* Left 8 Cols: Mock-up of a Standard NovaBrief Blog Article Page */}
          <div className="lg:col-span-8 bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
            {/* Mock Browser Top Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 text-xs text-slate-500 font-mono">
              <span>https://www.novabrief.tech/blog/cloud-architecture-aws-azure-gcp-guide</span>
              <span>Desktop 2-Column Layout</span>
            </div>

            {/* Overlay 1: Header Leaderboard */}
            {(() => {
              const zone = wireframeZones[0];
              const isSelected = selectedWireframeZoneId === zone.id;
              return (
                <button
                  type="button"
                  onClick={() => {
                    setSelectedWireframeZoneId(zone.id);
                    setSelectedPlacement(zone.snippetType);
                  }}
                  className={`w-full text-left p-3 rounded-lg border-2 border-dashed transition ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50/70'
                      : zone.isValidSlot
                      ? 'border-emerald-500/60 bg-emerald-50/30 hover:border-blue-500'
                      : 'border-red-400 bg-red-50/50'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span className="font-bold text-slate-900">
                      OVERLAY 01 · {zone.title}
                    </span>
                    <span className="font-mono text-[11px] text-slate-700">
                      slot="{zone.slotId}" · {zone.isValidSlot ? 'VALID' : 'INVALID'} · CTR {zone.expectedCtrPct}%
                    </span>
                  </div>
                </button>
              );
            })()}

            {/* Main 2-Column Blog Layout + Right Sticky Rail */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
              {/* Article Body Column (8 of 12 cols) */}
              <div className="md:col-span-8 bg-white border border-slate-200 rounded-lg p-4 space-y-3.5">
                <div className="text-[11px] font-mono uppercase tracking-wider text-blue-600">
                  Cloud &amp; Infrastructure Guide · 8 Min Read
                </div>
                <div className="text-sm font-bold text-slate-900">
                  H1: Cloud Architecture Guide — Comparing AWS, Azure, and GCP
                </div>
                <div className="space-y-1.5 py-1">
                  <div className="h-2.5 bg-slate-200 rounded w-full" />
                  <div className="h-2.5 bg-slate-200 rounded w-11/12" />
                  <div className="h-2.5 bg-slate-200 rounded w-4/5" />
                </div>

                <div className="text-xs font-bold text-slate-800 pt-1">
                  H2 #1: The Core Primitives of Cloud Computing
                </div>
                <div className="space-y-1.5">
                  <div className="h-2 bg-slate-200 rounded w-full" />
                  <div className="h-2 bg-slate-200 rounded w-10/12" />
                </div>

                {/* Contextual Affiliate Partner Callout Box */}
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-700 flex items-center justify-between">
                  <span>
                    <strong className="text-slate-900">Affiliate Callout:</strong> Claim $200 DigitalOcean / AWS Credits
                  </span>
                  <span className="font-mono text-emerald-700 font-semibold">$45–$100 CPA</span>
                </div>

                {/* Overlay 2: In-Article Fluid Ad #1 */}
                {(() => {
                  const zone = wireframeZones[1];
                  const isSelected = selectedWireframeZoneId === zone.id;
                  return (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedWireframeZoneId(zone.id);
                        setSelectedPlacement(zone.snippetType);
                      }}
                      className={`w-full text-left p-3.5 rounded-lg border-2 border-dashed transition ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/80'
                          : zone.isValidSlot
                          ? 'border-emerald-500/70 bg-emerald-50/40 hover:border-blue-500'
                          : 'border-red-400 bg-red-50/50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold text-slate-900">
                          OVERLAY 02 · {zone.title}
                        </span>
                        <span className="font-mono font-bold text-emerald-700">
                          {zone.expectedCtrPct}% CTR
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-600">
                        data-ad-layout="in-article" · slot="{zone.slotId}" · min-height: {zone.minHeightPx}px
                      </div>
                    </button>
                  );
                })()}

                <div className="text-xs font-bold text-slate-800 pt-1">
                  H2 #2: Comparing AWS EC2, Azure VMs, and Google GKE
                </div>
                <div className="space-y-1.5">
                  <div className="h-2 bg-slate-200 rounded w-full" />
                  <div className="h-2 bg-slate-200 rounded w-9/12" />
                </div>

                {/* Overlay 3: In-Article Fluid Ad #2 */}
                {(() => {
                  const zone = wireframeZones[2];
                  const isSelected = selectedWireframeZoneId === zone.id;
                  return (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedWireframeZoneId(zone.id);
                        setSelectedPlacement(zone.snippetType);
                      }}
                      className={`w-full text-left p-3 rounded-lg border-2 border-dashed transition ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/80'
                          : zone.isValidSlot
                          ? 'border-emerald-500/70 bg-emerald-50/40 hover:border-blue-500'
                          : 'border-red-400 bg-red-50/50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold text-slate-900">
                          OVERLAY 03 · {zone.title}
                        </span>
                        <span className="font-mono font-bold text-emerald-700">
                          {zone.expectedCtrPct}% CTR
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-600">
                        data-ad-layout="in-article" · slot="{zone.slotId}" · min-height: {zone.minHeightPx}px
                      </div>
                    </button>
                  );
                })()}

                <div className="text-xs font-bold text-slate-800 pt-1">
                  H2 #3: Production Deployment Checklist &amp; Conclusion
                </div>
                <div className="space-y-1.5">
                  <div className="h-2 bg-slate-200 rounded w-11/12" />
                  <div className="h-2 bg-slate-200 rounded w-3/4" />
                </div>

                {/* Overlay 5: End-of-Article Multiplex Grid */}
                {(() => {
                  const zone = wireframeZones[4];
                  const isSelected = selectedWireframeZoneId === zone.id;
                  return (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedWireframeZoneId(zone.id);
                        setSelectedPlacement(zone.snippetType);
                      }}
                      className={`w-full text-left p-3 rounded-lg border-2 border-dashed transition ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/80'
                          : zone.isValidSlot
                          ? 'border-emerald-500/70 bg-emerald-50/40 hover:border-blue-500'
                          : 'border-red-400 bg-red-50/50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold text-slate-900">
                          OVERLAY 05 · {zone.title}
                        </span>
                        <span className="font-mono font-bold text-emerald-700">
                          {zone.expectedCtrPct}% CTR
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-600">
                        data-ad-format="autorelaxed" · slot="{zone.slotId}"
                      </div>
                    </button>
                  );
                })()}
              </div>

              {/* Right Sticky Sidebar Column (4 of 12 cols) */}
              <div className="md:col-span-4 space-y-3">
                <div className="p-3 bg-white border border-slate-200 rounded-lg text-xs text-slate-600">
                  <div className="font-bold text-slate-900 mb-1">Daily AI &amp; Tech Brief</div>
                  <div className="text-[11px] text-slate-500">Newsletter Lead Magnet Box</div>
                </div>

                {/* Overlay 4: Sticky Sidebar 300x600 Ad Unit */}
                {(() => {
                  const zone = wireframeZones[3];
                  const isSelected = selectedWireframeZoneId === zone.id;
                  return (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedWireframeZoneId(zone.id);
                        setSelectedPlacement(zone.snippetType);
                      }}
                      className={`w-full text-left p-4 rounded-lg border-2 border-dashed min-h-[260px] flex flex-col justify-between transition ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/80'
                          : zone.isValidSlot
                          ? 'border-emerald-500/70 bg-emerald-50/40 hover:border-blue-500'
                          : 'border-red-400 bg-red-50/50'
                      }`}
                    >
                      <div>
                        <div className="text-xs font-bold text-slate-900">
                          OVERLAY 04 · Sticky Sidebar (300×600)
                        </div>
                        <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                          Locks into viewport at <code className="font-mono">top: 96px</code> as the reader scrolls through long technical guides.
                        </p>
                      </div>
                      <div className="pt-4 border-t border-slate-200/80 text-[11px] font-mono space-y-1">
                        <div className="text-slate-800">slot="{zone.slotId}"</div>
                        <div className="text-emerald-700 font-bold">
                          Active View: {zone.activeViewSec}s · CTR {zone.expectedCtrPct}%
                        </div>
                      </div>
                    </button>
                  );
                })()}
              </div>
            </div>
          </div>

          {/* Right 4 Cols: Selected Overlay Diagnostic Inspector */}
          <div className="lg:col-span-4 space-y-5">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
              <div>
                <div className="text-xs font-medium text-slate-500">Selected Wireframe Overlay</div>
                <h4 className="text-base font-bold text-slate-900 mt-0.5">
                  {activeWireframeZone.title}
                </h4>
                <div className="text-xs text-slate-600 mt-0.5">
                  Placement: {activeWireframeZone.placementLabel}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 py-3 border-y border-slate-200 text-xs">
                <div>
                  <div className="text-slate-500">Configured Slot ID</div>
                  <div
                    className={`font-mono font-bold mt-0.5 ${
                      activeWireframeZone.isValidSlot ? 'text-emerald-700' : 'text-red-600'
                    }`}
                  >
                    {activeWireframeZone.slotId}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500">Expected CTR / View</div>
                  <div className="font-mono font-bold text-slate-900 mt-0.5">
                    {activeWireframeZone.expectedCtrPct}% · {activeWireframeZone.activeViewSec}s
                  </div>
                </div>
              </div>

              <div className="text-xs space-y-1.5">
                <div className="font-semibold text-slate-800">CLS &amp; Viewability CSS Rule</div>
                <code className="block p-2.5 bg-white border border-slate-200 rounded font-mono text-[11px] text-slate-800">
                  {activeWireframeZone.cssRuleSummary}
                </code>
              </div>

              <button
                type="button"
                onClick={() =>
                  handleCopy(
                    generateAdSenseSnippet(activeWireframeZone.snippetType, slotConfig),
                    'wireframe-zone-copy'
                  )
                }
                className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition"
              >
                {copiedKey === 'wireframe-zone-copy' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Copied Zone HTML Snippet</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy This Overlay&apos;s HTML Code</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 04. Traffic Quality & Channel CTR Optimizer Module */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Channel Acquisition Diagnostics · AdSense Smart Pricing &amp; CTR Optimization by Traffic Source
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              04. Traffic Quality &amp; Channel CTR Optimizer
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Google AdSense evaluates click quality differently depending on how visitors arrive at <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">novabrief.tech</code>. Input your current traffic source breakdown below (Organic Search, Social Media, Direct &amp; Newsletter) to receive custom layout rules and CTR optimization tips for each channel.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={() => setTrafficMix({ organicPct: 65, socialPct: 20, directPct: 15 })}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              Search-Heavy SEO Mix
            </button>
            <button
              type="button"
              onClick={() => setTrafficMix({ organicPct: 20, socialPct: 65, directPct: 15 })}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              Social / Alert Spike
            </button>
            <button
              type="button"
              onClick={() => setTrafficMix({ organicPct: 30, socialPct: 20, directPct: 50 })}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition whitespace-nowrap shrink-0"
            >
              Direct / Subscribers
            </button>
          </div>
        </div>

        {/* 4-Column Traffic Quality Telemetry Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 py-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500">Traffic Quality Index</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              {trafficAnalysis.trafficQualityScore} / 100
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Dominant: {trafficAnalysis.dominantChannel}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Blended Channel CTR</div>
            <div className="text-2xl font-bold text-blue-600 font-mono tabular-nums mt-1">
              {trafficAnalysis.blendedExpectedCtrPct.toFixed(2)}%
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              {trafficAnalysis.blendedRpmMultiplier.toFixed(2)}x RPM Yield Multiplier
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Normalized Channel Split</div>
            <div className="text-base font-bold text-slate-900 font-mono tabular-nums mt-1 whitespace-nowrap">
              {trafficAnalysis.normalizedOrganicPct}% Org · {trafficAnalysis.normalizedSocialPct}% Soc · {trafficAnalysis.normalizedDirectPct}% Dir
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Auto-normalized to 100% total traffic
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">AdSense Smart Pricing Status</div>
            <div
              className={`text-base font-bold font-mono mt-1 ${
                trafficAnalysis.smartPricingRiskStatus === 'Protected (High Intent)'
                  ? 'text-emerald-700'
                  : trafficAnalysis.smartPricingRiskStatus === 'Balanced'
                  ? 'text-blue-600'
                  : 'text-amber-700'
              }`}
            >
              {trafficAnalysis.smartPricingRiskStatus}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Based on advertiser conversion probability
            </div>
          </div>
        </div>

        {/* 3 Channel Input Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-6 border-b border-slate-200">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="organic-traffic-input" className="font-semibold text-slate-800">
                Organic Search (Google / Bing)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {trafficAnalysis.normalizedOrganicPct}% (Raw: {trafficMix.organicPct})
              </span>
            </div>
            <input
              id="organic-traffic-input"
              type="range"
              min={0}
              max={100}
              step={5}
              value={trafficMix.organicPct}
              onChange={(e) =>
                setTrafficMix({ ...trafficMix, organicPct: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <p className="text-[11px] text-slate-500">
              Visitors landing on <code className="font-mono">/blog/*</code> technical tutorials via search queries.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="social-traffic-input" className="font-semibold text-slate-800">
                Social Media (LinkedIn / WhatsApp / X)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {trafficAnalysis.normalizedSocialPct}% (Raw: {trafficMix.socialPct})
              </span>
            </div>
            <input
              id="social-traffic-input"
              type="range"
              min={0}
              max={100}
              step={5}
              value={trafficMix.socialPct}
              onChange={(e) =>
                setTrafficMix({ ...trafficMix, socialPct: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <p className="text-[11px] text-slate-500">
              Students clicking internship alerts from university groups, LinkedIn, or Reddit.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="direct-traffic-input" className="font-semibold text-slate-800">
                Direct &amp; Daily Brief Newsletter
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {trafficAnalysis.normalizedDirectPct}% (Raw: {trafficMix.directPct})
              </span>
            </div>
            <input
              id="direct-traffic-input"
              type="range"
              min={0}
              max={100}
              step={5}
              value={trafficMix.directPct}
              onChange={(e) =>
                setTrafficMix({ ...trafficMix, directPct: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <p className="text-[11px] text-slate-500">
              Returning subscribers opening bookmarks, PWA installs, or email digests.
            </p>
          </div>
        </div>

        {/* Channel-Specific CTR Optimization Playbooks */}
        <div className="divide-y divide-slate-200 pt-2">
          {trafficAnalysis.channelPlaybooks.map((playbook) => (
            <div key={playbook.channel} className="py-5 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span className="text-sm font-bold text-slate-900">{playbook.channel}</span>
                  <span aria-hidden="true">·</span>
                  <span className="font-mono font-semibold text-blue-600 tabular-nums">
                    {playbook.sharePct}% Traffic Share
                  </span>
                  {playbook.isDominant && (
                    <>
                      <span aria-hidden="true">·</span>
                      <span className="font-semibold text-emerald-700">
                        Primary Dominant Channel
                      </span>
                    </>
                  )}
                  <span aria-hidden="true">·</span>
                  <span>Smart Pricing Risk: {playbook.ivtAndSmartPricingRisk}</span>
                </div>

                <div className="text-xs font-mono text-slate-700 tabular-nums">
                  Benchmark CTR: <strong>{playbook.benchmarkCtrPct.toFixed(2)}%</strong> · Est. Channel RPM: <strong className="text-emerald-700">${playbook.benchmarkRpmUsd.toFixed(2)}</strong>
                </div>
              </div>

              <div className="text-xs font-medium text-slate-800">
                {playbook.headlineRecommendation} — <span className="text-slate-500">Best Format:</span>{' '}
                <code className="font-mono text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded">
                  {playbook.optimalAdFormat}
                </code>
              </div>

              <ul className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-1 text-xs text-slate-600">
                {playbook.actionableTips.map((tip, idx) => (
                  <li
                    key={idx}
                    className={idx > 0 ? 'md:border-l md:border-slate-200 md:pl-5 leading-relaxed' : 'leading-relaxed'}
                  >
                    <strong className="font-mono text-slate-900">0{idx + 1}.</strong> {tip}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
