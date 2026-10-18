import React from 'react';
import {
  RevenueSimulationInput,
  calculateRevenueProjection,
} from '../utils/monetizationEngine';
import { CheckSquare, Square, RotateCcw } from 'lucide-react';

export interface SprintTask {
  id: string;
  dayRange: string;
  phase: string;
  title: string;
  actionSteps: string;
  expectedImpact: string;
  completed: boolean;
}

export const INITIAL_SPRINT_TASKS: SprintTask[] = [
  {
    id: 'sprint-day-1',
    dayRange: 'Day 1 (Today, Oct 18)',
    phase: 'Emergency AdSense Fix',
    title: 'Replace data-ad-slot="auto" & Add Missing <meta> Tag on /news',
    actionSteps:
      'In AdSense > Ads > By ad unit, create 5 units (In-Article, Sticky Sidebar, In-Feed, Multiplex, Leaderboard). Replace data-ad-slot="auto" in blog_post.html, blog.html, and news.html with the real 10-digit IDs.',
    expectedImpact: 'Fixes HTTP 400 ad slot failure immediately',
    completed: false,
  },
  {
    id: 'sprint-day-2',
    dayRange: 'Day 2 (Oct 19)',
    phase: 'AdSense Onboarding & CMP',
    title: 'Complete AdSense /onboarding Steps & Publish TCF v2.2 Consent Banner',
    actionSteps:
      'Enable Auto Ads (Anchor + Vignettes at 10-min cap, Ad Load 65%), exclude <nav>, and publish the European GDPR TCF v2.2 message in AdSense > Privacy & messaging.',
    expectedImpact: '+40% RPM & full UK/EU ad monetization',
    completed: false,
  },
  {
    id: 'sprint-day-3-4',
    dayRange: 'Days 3–4 (Oct 20–21)',
    phase: 'Fast-Payout Affiliates',
    title: 'Join Instant-Approval Tech Affiliate Programs & Add /go/ Redirects',
    actionSteps:
      'Register for DigitalOcean ($200 Free Credit referral), Hostinger Affiliate (60% VPS commission), Coursera (via Impact), Educative.io, and Namecheap. Inject the Affiliate Callout HTML into all 18 existing blog posts.',
    expectedImpact: '$25–$85 commission per student/dev conversion',
    completed: false,
  },
  {
    id: 'sprint-day-5-6',
    dayRange: 'Days 5–6 (Oct 22–23)',
    phase: 'Engagement & Retention Loop',
    title: 'Stop /news External Bounce & Launch "Internship Deadline Tracker" Lead Magnet',
    actionSteps:
      'Currently /news links straight out to external sites ("Read Original Source"). Open an internal AI Summary & Analysis drawer/page first with an In-Article ad + "Download 2026 Tech Internship Calendar" email capture.',
    expectedImpact: 'Increases Pages/Session from 1.2 to 2.6 (+115% ad impressions)',
    completed: false,
  },
  {
    id: 'sprint-day-7-9',
    dayRange: 'Days 7–9 (Oct 24–26)',
    phase: 'High-CPC Content Sprint',
    title: 'Publish 3 High-CPC Buyer-Intent Comparison Guides ($16–$24 CPC)',
    actionSteps:
      'Publish the AWS/GCP/Azure Student Credits Guide, Best PostgreSQL/Vector DBs Guide, and Best Linux VPS for Docker Guide with 3-column comparison tables above the fold.',
    expectedImpact: '3x–5x higher AdSense CPC than general news',
    completed: false,
  },
  {
    id: 'sprint-day-10-13',
    dayRange: 'Days 10–13 (Oct 27–31)',
    phase: 'Distribution & Direct Cashflow',
    title: 'Distribute Internship Deadlines to CS Subreddits/LinkedIn & Offer $75 Newsletter Slot',
    actionSteps:
      'Share your Google/Microsoft/NASA internship alerts on LinkedIn, r/csMajors, and university Discord servers. Pitch 3 indie AI dev-tool founders a $75 "Featured Tool of the Week" slot in the Nova Brief newsletter & homepage.',
    expectedImpact: 'Immediate traffic spike + $75–$225 direct cash before Oct 31',
    completed: false,
  },
];

interface RevenueRoadmapViewProps {
  simInput: RevenueSimulationInput;
  onUpdateSimInput: (next: RevenueSimulationInput) => void;
  sprintTasks: SprintTask[];
  onToggleSprintTask: (id: string) => void;
  onResetSim: () => void;
}

export const RevenueRoadmapView: React.FC<RevenueRoadmapViewProps> = ({
  simInput,
  onUpdateSimInput,
  sprintTasks,
  onToggleSprintTask,
  onResetSim,
}) => {
  const projection = calculateRevenueProjection(simInput);
  const completedSprintCount = sprintTasks.filter((t) => t.completed).length;

  return (
    <div className="space-y-10">
      {/* Interactive Revenue & RPM Simulator */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Financial Modeling · Display Ads + Affiliate Conversions + Direct Sponsorships
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              NovaBrief Revenue & RPM Simulator (October Target)
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              Adjust traffic, Tier-1 geo share, AdSense CTR, and affiliate conversion parameters to see your projected 30-day run rate and remaining 13-day October earnings.
            </p>
          </div>
          <button
            type="button"
            onClick={onResetSim}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition self-start whitespace-nowrap shrink-0"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Default Benchmarks</span>
          </button>
        </div>

        {/* Top KPI Output Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 py-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500">Projected 30-Day Total</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              ${projection.totalMonthlyRevenueUsd.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              {projection.monthlyPageviews.toLocaleString()} monthly views
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Remaining 13 Days (Oct 18–31)</div>
            <div className="text-2xl font-bold text-emerald-700 font-mono tabular-nums mt-1">
              ${projection.remainingMonthRevenueUsd.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Immediate month-end target
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">AdSense Display Earnings</div>
            <div className="text-2xl font-bold text-blue-600 font-mono tabular-nums mt-1">
              ${projection.monthlyAdSenseRevenueUsd.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              Effective RPM: ${projection.effectivePageRpmUsd.toFixed(2)}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Affiliate Commissions</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              ${projection.monthlyAffiliateRevenueUsd.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              {projection.monthlyAffiliateConversions} sales ({projection.monthlyAffiliateClicks} clicks)
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Newsletter / Direct Sponsors</div>
            <div className="text-2xl font-bold text-slate-900 font-mono tabular-nums mt-1">
              ${projection.monthlySponsorshipRevenueUsd.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono tabular-nums">
              {simInput.newsletterSponsorsPerMonth} sponsors @ ${simInput.sponsorRateUsd}
            </div>
          </div>
        </div>

        {/* Sliders & Parameter Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-6">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="daily-views" className="font-semibold text-slate-700">
                Daily Pageviews
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {simInput.dailyPageviews.toLocaleString()} / day
              </span>
            </div>
            <input
              id="daily-views"
              type="range"
              min={200}
              max={10000}
              step={100}
              value={simInput.dailyPageviews}
              onChange={(e) =>
                onUpdateSimInput({ ...simInput, dailyPageviews: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Increase via internship alert shares + internal /news summaries
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="tier1-share" className="font-semibold text-slate-700">
                Tier-1 Traffic Share (US/UK/CA/EU)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {simInput.tier1TrafficSharePct}%
              </span>
            </div>
            <input
              id="tier1-share"
              type="range"
              min={10}
              max={90}
              step={5}
              value={simInput.tier1TrafficSharePct}
              onChange={(e) =>
                onUpdateSimInput({ ...simInput, tier1TrafficSharePct: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Enabling TCF v2.2 CMP unlocks full CPC on UK/EU readers
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="ads-per-page" className="font-semibold text-slate-700">
                Viewable Ad Units per Page
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {simInput.adImpressionsPerPage} units
              </span>
            </div>
            <input
              id="ads-per-page"
              type="range"
              min={1}
              max={5}
              step={1}
              value={simInput.adImpressionsPerPage}
              onChange={(e) =>
                onUpdateSimInput({ ...simInput, adImpressionsPerPage: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Recommended: 3–4 (Leaderboard + 2 In-Article + Sticky Sidebar)
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="ad-ctr" className="font-semibold text-slate-700">
                AdSense Click-Through Rate (CTR)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                {simInput.estimatedCtrPct.toFixed(1)}%
              </span>
            </div>
            <input
              id="ad-ctr"
              type="range"
              min={0.5}
              max={6.0}
              step={0.1}
              value={simInput.estimatedCtrPct}
              onChange={(e) =>
                onUpdateSimInput({ ...simInput, estimatedCtrPct: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Placing In-Article Unit #1 below H2 #1 lifts CTR from 0.4% to ~2.8%
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="avg-cpc" className="font-semibold text-slate-700">
                Base Tech/Cloud CPC (USD)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                ${simInput.averageCpcUsd.toFixed(2)}
              </span>
            </div>
            <input
              id="avg-cpc"
              type="range"
              min={0.3}
              max={4.5}
              step={0.1}
              value={simInput.averageCpcUsd}
              onChange={(e) =>
                onUpdateSimInput({ ...simInput, averageCpcUsd: Number(e.target.value) })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Cloud, PostgreSQL, and Cybersecurity guides average $1.20–$3.10 net CPC
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label htmlFor="affiliate-cpa" className="font-semibold text-slate-700">
                Avg Affiliate Commission (CPA)
              </label>
              <span className="font-mono font-bold text-slate-900 tabular-nums">
                ${simInput.averageAffiliateCommissionUsd}
              </span>
            </div>
            <input
              id="affiliate-cpa"
              type="range"
              min={15}
              max={100}
              step={5}
              value={simInput.averageAffiliateCommissionUsd}
              onChange={(e) =>
                onUpdateSimInput({
                  ...simInput,
                  averageAffiliateCommissionUsd: Number(e.target.value),
                })
              }
              className="w-full accent-blue-600"
            />
            <div className="text-[11px] text-slate-500">
              Coursera Plus ($45), Hostinger VPS ($55), DigitalOcean ($25)
            </div>
          </div>
        </div>
      </section>

      {/* 13-Day End-of-Month Execution Roadmap */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Actionable Execution Plan · October 18 – October 31, 2026 (13 Days Remaining)
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              End-of-Month Cashflow & Implementation Sprint
            </h3>
            <p className="text-sm text-slate-600 mt-0.5">
              Note on Payout Timing: Google AdSense finalizes October earnings on November 2 and pays out on November 21 once you cross the $100 threshold. To generate <strong>realized revenue before October 31</strong>, combine your AdSense fix with instant-commission affiliates and a direct "Featured AI Tool" newsletter slot.
            </p>
          </div>
          <div className="text-xs font-mono font-semibold text-slate-800 shrink-0 tabular-nums">
            {completedSprintCount} / {sprintTasks.length} Milestones Completed
          </div>
        </div>

        <div className="divide-y divide-slate-200">
          {sprintTasks.map((task) => (
            <div
              key={task.id}
              onClick={() => onToggleSprintTask(task.id)}
              className="py-5 flex items-start gap-4 cursor-pointer hover:bg-slate-50/70 px-2 rounded-lg transition"
            >
              <button
                type="button"
                aria-label={`Mark ${task.title} complete`}
                className="mt-0.5 text-slate-500 hover:text-blue-600 shrink-0"
              >
                {task.completed ? (
                  <CheckSquare className="w-5 h-5 text-emerald-600" />
                ) : (
                  <Square className="w-5 h-5 text-slate-400" />
                )}
              </button>
              <div className="flex-1 space-y-1">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                  <span>
                    <strong className="font-mono text-slate-800">{task.dayRange}</strong> · {task.phase}
                  </span>
                  <span className="font-mono font-semibold text-emerald-700">
                    {task.expectedImpact}
                  </span>
                </div>
                <h4
                  className={`text-base font-bold ${
                    task.completed ? 'line-through text-slate-400' : 'text-slate-900'
                  }`}
                >
                  {task.title}
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {task.actionSteps}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
