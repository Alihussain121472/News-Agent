import React, { useState, useEffect } from 'react';
import {
  AdSenseSlotConfig,
  AuditFinding,
  INITIAL_AUDIT_FINDINGS,
  PUBLISHER_ID,
  RevenueSimulationInput,
  generateAdSenseSnippet,
  calculateRevenueProjection,
  LIVE_BLOG_ARTICLES,
  generateAffiliateCalloutHtml,
} from './utils/monetizationEngine';
import { SiteAuditAndFixer } from './components/SiteAuditAndFixer';
import { AdSenseConsoleGuide } from './components/AdSenseConsoleGuide';
import { AffiliateContentStudio } from './components/AffiliateContentStudio';
import { SeoKeywordDensityTool } from './components/SeoKeywordDensityTool';
import {
  RevenueRoadmapView,
  INITIAL_SPRINT_TASKS,
  SprintTask,
} from './components/RevenueRoadmapView';
import { Download, Check } from 'lucide-react';

type ActiveTab = 'audit' | 'adsense' | 'affiliate' | 'seo' | 'roadmap';

const DEFAULT_SIM_INPUT: RevenueSimulationInput = {
  dailyPageviews: 1800,
  tier1TrafficSharePct: 45,
  pagesPerSession: 2.2,
  adImpressionsPerPage: 3,
  estimatedCtrPct: 2.8,
  averageCpcUsd: 1.35,
  affiliateClickRatePct: 4.0,
  affiliateConversionRatePct: 2.5,
  averageAffiliateCommissionUsd: 45,
  newsletterSponsorsPerMonth: 2,
  sponsorRateUsd: 75,
};

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('audit');
  const [exportedNotice, setExportedNotice] = useState<boolean>(false);

  const [findings, setFindings] = useState<AuditFinding[]>(() => {
    try {
      const saved = localStorage.getItem('novabrief_audit_findings_v1');
      return saved ? JSON.parse(saved) : INITIAL_AUDIT_FINDINGS;
    } catch {
      return INITIAL_AUDIT_FINDINGS;
    }
  });

  const [slotConfig, setSlotConfig] = useState<AdSenseSlotConfig>(() => {
    try {
      const saved = localStorage.getItem('novabrief_slot_config_v1');
      return saved
        ? JSON.parse(saved)
        : {
            publisherId: PUBLISHER_ID,
            inArticleSlotId: '4829103847',
            sidebarSlotId: '5910293846',
            inFeedSlotId: '6029384751',
            multiplexSlotId: '7192837462',
            headerLeaderboardSlotId: '8293847563',
            enableLazyLoad: true,
            minContainerHeightPx: 260,
          };
    } catch {
      return {
        publisherId: PUBLISHER_ID,
        inArticleSlotId: '4829103847',
        sidebarSlotId: '5910293846',
        inFeedSlotId: '6029384751',
        multiplexSlotId: '7192837462',
        headerLeaderboardSlotId: '8293847563',
        enableLazyLoad: true,
        minContainerHeightPx: 260,
      };
    }
  });

  const [simInput, setSimInput] = useState<RevenueSimulationInput>(() => {
    try {
      const saved = localStorage.getItem('novabrief_sim_input_v1');
      return saved ? JSON.parse(saved) : DEFAULT_SIM_INPUT;
    } catch {
      return DEFAULT_SIM_INPUT;
    }
  });

  const [sprintTasks, setSprintTasks] = useState<SprintTask[]>(() => {
    try {
      const saved = localStorage.getItem('novabrief_sprint_tasks_v1');
      return saved ? JSON.parse(saved) : INITIAL_SPRINT_TASKS;
    } catch {
      return INITIAL_SPRINT_TASKS;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('novabrief_audit_findings_v1', JSON.stringify(findings));
    } catch {
      // ignore storage errors
    }
  }, [findings]);

  useEffect(() => {
    try {
      localStorage.setItem('novabrief_slot_config_v1', JSON.stringify(slotConfig));
    } catch {
      // ignore storage errors
    }
  }, [slotConfig]);

  useEffect(() => {
    try {
      localStorage.setItem('novabrief_sim_input_v1', JSON.stringify(simInput));
    } catch {
      // ignore storage errors
    }
  }, [simInput]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  useEffect(() => {
    try {
      localStorage.setItem('novabrief_sprint_tasks_v1', JSON.stringify(sprintTasks));
    } catch {
      // ignore storage errors
    }
  }, [sprintTasks]);

  const handleToggleFindingFixed = (id: string) => {
    setFindings((prev) =>
      prev.map((f) => (f.id === id ? { ...f, fixedStatus: !f.fixedStatus } : f))
    );
  };

  const handleToggleSprintTask = (id: string) => {
    setSprintTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
  };

  const handleExportImplementationKit = () => {
    const projection = calculateRevenueProjection(simInput);
    const inArticleHtml = generateAdSenseSnippet('in-article', slotConfig);
    const sidebarHtml = generateAdSenseSnippet('sidebar-sticky', slotConfig);
    const sampleAffiliateHtml = generateAffiliateCalloutHtml(LIVE_BLOG_ARTICLES[0], 'novabrief-oct26');

    const markdownReport = `# NovaBrief.tech Monetization & AdSense Implementation Kit
Generated for: https://www.novabrief.tech/
AdSense Publisher ID: ${PUBLISHER_ID}

## 1. Critical Fix: Replace Broken data-ad-slot="auto"
### In-Article Unit (blog_post.html)
\`\`\`html
${inArticleHtml}
\`\`\`

### Sticky Sidebar Unit (news.html & blog.html)
\`\`\`html
${sidebarHtml}
\`\`\`

## 2. Sample Affiliate Callout Block (${LIVE_BLOG_ARTICLES[0].slug})
\`\`\`html
${sampleAffiliateHtml}
\`\`\`

## 3. Projected Monthly Revenue Breakdown
- Monthly Pageviews: ${projection.monthlyPageviews.toLocaleString()}
- Effective Page RPM: $${projection.effectivePageRpmUsd.toFixed(2)}
- Monthly AdSense Display Revenue: $${projection.monthlyAdSenseRevenueUsd.toFixed(2)}
- Monthly Affiliate Revenue: $${projection.monthlyAffiliateRevenueUsd.toFixed(2)}
- Monthly Direct Sponsorships: $${projection.monthlySponsorshipRevenueUsd.toFixed(2)}
- Total 30-Day Run Rate: $${projection.totalMonthlyRevenueUsd.toFixed(2)}
- Remaining 13-Day October Target: $${projection.remainingMonthRevenueUsd.toFixed(2)}
`;

    const blob = new Blob([markdownReport], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'novabrief-monetization-implementation-kit.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportedNotice(true);
    setTimeout(() => setExportedNotice(false), 2000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Strict 3-Zone Top Bar Contract */}
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200 px-4 sm:px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 md:gap-8">
          {/* Zone 1: Single text element wordmark */}
          <a
            href="#top"
            onClick={(e) => {
              e.preventDefault();
              setActiveTab('audit');
            }}
            className="text-sm sm:text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            NovaBrief Monetization Studio
          </a>

          {/* Zone 2: 5 concise single-line text navigation links */}
          <nav aria-label="Primary Navigation" className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <button
              type="button"
              onClick={() => setActiveTab('audit')}
              className={`py-1 border-b-2 transition whitespace-nowrap shrink-0 focus:outline-none ${
                activeTab === 'audit'
                  ? 'border-blue-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Audit & Code Fixer
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('adsense')}
              className={`py-1 border-b-2 transition whitespace-nowrap shrink-0 focus:outline-none ${
                activeTab === 'adsense'
                  ? 'border-blue-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              AdSense Settings
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('affiliate')}
              className={`py-1 border-b-2 transition whitespace-nowrap shrink-0 focus:outline-none ${
                activeTab === 'affiliate'
                  ? 'border-blue-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Affiliate & Content
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('seo')}
              className={`py-1 border-b-2 transition whitespace-nowrap shrink-0 focus:outline-none ${
                activeTab === 'seo'
                  ? 'border-blue-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              SEO Density Tool
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('roadmap')}
              className={`py-1 border-b-2 transition whitespace-nowrap shrink-0 focus:outline-none ${
                activeTab === 'roadmap'
                  ? 'border-blue-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Revenue & Roadmap
            </button>
          </nav>

          {/* Zone 3: 1 primary action */}
          <div className="flex items-center shrink-0">
            <button
              type="button"
              onClick={handleExportImplementationKit}
              className="inline-flex items-center gap-1.5 px-3 sm:px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition whitespace-nowrap shrink-0"
            >
              {exportedNotice ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Kit Downloaded</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Kit</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Segmented Navigation Bar (Visible on small viewports, full 5-col fit) */}
      <div className="md:hidden bg-white border-b border-slate-200 px-2.5 py-2">
        <div className="grid grid-cols-5 gap-1 bg-slate-100 p-1 rounded-lg">
          {(
            [
              { id: 'audit', label: 'Audit' },
              { id: 'adsense', label: 'AdSense' },
              { id: 'affiliate', label: 'Affiliate' },
              { id: 'seo', label: 'SEO Tool' },
              { id: 'roadmap', label: 'Roadmap' },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveTab(item.id)}
              className={`py-1.5 text-[11px] font-medium rounded-md transition text-center whitespace-nowrap ${
                activeTab === item.id
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'audit' && (
          <SiteAuditAndFixer
            findings={findings}
            onToggleFindingFixed={handleToggleFindingFixed}
            slotConfig={slotConfig}
            onUpdateSlotConfig={setSlotConfig}
          />
        )}

        {activeTab === 'adsense' && <AdSenseConsoleGuide slotConfig={slotConfig} />}

        {activeTab === 'affiliate' && <AffiliateContentStudio />}

        {activeTab === 'seo' && <SeoKeywordDensityTool />}

        {activeTab === 'roadmap' && (
          <RevenueRoadmapView
            simInput={simInput}
            onUpdateSimInput={setSimInput}
            sprintTasks={sprintTasks}
            onToggleSprintTask={handleToggleSprintTask}
            onResetSim={() => setSimInput(DEFAULT_SIM_INPUT)}
          />
        )}
      </main>

      {/* Quiet Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 px-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            Prepared for <span className="font-semibold text-slate-800">novabrief.tech</span> · Publisher Account <span className="font-mono text-slate-800">{PUBLISHER_ID}</span>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <button type="button" onClick={() => setActiveTab('audit')} className="hover:text-slate-900">
              Code Fixer
            </button>
            <span aria-hidden="true">·</span>
            <button type="button" onClick={() => setActiveTab('adsense')} className="hover:text-slate-900">
              AdSense Console Guide
            </button>
            <span aria-hidden="true">·</span>
            <button type="button" onClick={() => setActiveTab('affiliate')} className="hover:text-slate-900">
              Affiliate Widget Builder
            </button>
            <span aria-hidden="true">·</span>
            <button type="button" onClick={() => setActiveTab('seo')} className="hover:text-slate-900">
              SEO Density Tool
            </button>
            <span aria-hidden="true">·</span>
            <button type="button" onClick={() => setActiveTab('roadmap')} className="hover:text-slate-900">
              13-Day Sprint
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
