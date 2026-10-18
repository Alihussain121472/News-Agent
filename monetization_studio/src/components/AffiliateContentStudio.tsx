import React, { useState } from 'react';
import {
  LIVE_BLOG_ARTICLES,
  BlogArticleMonetizationMap,
  generateAffiliateCalloutHtml,
} from '../utils/monetizationEngine';
import { Copy, Check, Search, ExternalLink } from 'lucide-react';

interface HighCpcArticleIdea {
  title: string;
  targetSlug: string;
  searchIntent: string;
  estimatedCpcUsd: number;
  affiliatePairing: string;
  whyItRanksFast: string;
}

const HIGH_CPC_CONTENT_CALENDAR: HighCpcArticleIdea[] = [
  {
    title: 'AWS vs Google Cloud vs Azure Free Student Credits (2026 Step-by-Step Verification Guide)',
    targetSlug: '/blog/cloud-student-credits-aws-gcp-azure-2026',
    searchIntent: 'Transactional / Commercial Investigation',
    estimatedCpcUsd: 21.40,
    affiliatePairing: 'DigitalOcean ($200 Credit -> $25 CPA) + Hostinger VPS (60% RevShare) + Coursera Cloud Tracks',
    whyItRanksFast: 'Directly matches your existing cloud architecture authority and student audience; enterprise cloud advertisers bid $18–$28 per click.',
  },
  {
    title: '7 Best AI Coding Assistants & IDE Copilots for Software Engineering Interns (Tested)',
    targetSlug: '/blog/best-ai-coding-assistants-interns-2026',
    searchIntent: 'Commercial Comparison',
    estimatedCpcUsd: 16.80,
    affiliatePairing: 'JetBrains Student / Cursor / DataCamp AI Track / Educative.io',
    whyItRanksFast: 'High social shareability on LinkedIn/Reddit and massive B2B SaaS display ad demand.',
  },
  {
    title: 'How to Pass the Google Summer of Code (GSoC) & MLH Fellowship Proposal Review',
    targetSlug: '/blog/gsoc-mlh-fellowship-proposal-template-guide',
    searchIntent: 'High-Volume Student Career Intent',
    estimatedCpcUsd: 9.80,
    affiliatePairing: 'Educative.io System Design + Coursera Open Source Linux Specialization + Paid Resume/Proposal Template ($9)',
    whyItRanksFast: 'Drives massive organic referral traffic from university WhatsApp/Discord groups, feeding both AdSense impressions and email subscribers.',
  },
  {
    title: 'Best Managed PostgreSQL & Vector Databases for AI Agents (Supabase vs Neon vs AWS RDS)',
    targetSlug: '/blog/best-postgresql-vector-databases-ai-agents',
    searchIntent: 'B2B Infrastructure Comparison',
    estimatedCpcUsd: 24.10,
    affiliatePairing: 'DigitalOcean Managed DB + Aiven + Supabase Partner Program',
    whyItRanksFast: 'Links directly from your existing /blog/production-database-design-postgresql-guide and /blog/autonomous-ai-agents-architecture-guide.',
  },
  {
    title: 'Top 10 Cybersecurity Certifications That Guarantee SOC Analyst Interviews in 2026',
    targetSlug: '/blog/top-cybersecurity-certifications-soc-analyst-2026',
    searchIntent: 'Career & Education Buyer Intent',
    estimatedCpcUsd: 18.50,
    affiliatePairing: 'Coursera Google Cybersecurity Certificate (45% Commission) + NordVPN Lab Bundle + TryHackMe',
    whyItRanksFast: 'Online universities and bootcamp advertisers bid aggressively ($15+ CPC) on cybersecurity certification keywords.',
  },
  {
    title: 'Best Linux KVM VPS Hosting for Student Docker & Self-Hosted n8n Automation Workflows',
    targetSlug: '/blog/best-linux-vps-hosting-docker-n8n-students',
    searchIntent: 'Direct Buyer Intent',
    estimatedCpcUsd: 19.30,
    affiliatePairing: 'Hostinger KVM VPS ($35–$85 payout per sale) + DigitalOcean + Namecheap',
    whyItRanksFast: 'Directly monetizes readers of your existing /blog/docker-containerization-guide-students and /blog/student-automation-tools-2026.',
  },
];

export const AffiliateContentStudio: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedArticle, setSelectedArticle] = useState<BlogArticleMonetizationMap>(
    LIVE_BLOG_ARTICLES[0]
  );
  const [trackingTag, setTrackingTag] = useState<string>('novabrief-oct26');
  const [copiedHtml, setCopiedHtml] = useState<boolean>(false);

  const filteredArticles = LIVE_BLOG_ARTICLES.filter(
    (art) =>
      art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.primaryAffiliatePartner.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const generatedHtml = generateAffiliateCalloutHtml(selectedArticle, trackingTag);

  const handleCopyHtml = () => {
    navigator.clipboard.writeText(generatedHtml);
    setCopiedHtml(true);
    setTimeout(() => setCopiedHtml(false), 1800);
  };

  return (
    <div className="space-y-10">
      {/* Existing 18 Blog Posts -> Affiliate Injection Matrix */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="text-xs text-slate-500 mb-1">
              Immediate Revenue Extraction · Monetizing Your Existing Indexed Sitemap URLs
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Affiliate & High-CPC Content Engine for novabrief.tech
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Your sitemap already has 18 comprehensive guides on Cloud, PostgreSQL, Docker, Cybersecurity, and Certifications—but they currently have <strong>0 affiliate links</strong>. Click any live article below to generate its tailored partner callout box.
            </p>
          </div>

          <div className="relative w-full lg:w-72 shrink-0">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your live blog guides..."
              aria-label="Search live blog guides"
              className="w-full pl-9 pr-3.5 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
          {/* Left: Live URLs List */}
          <div className="lg:col-span-6 space-y-3">
            <div className="text-xs font-semibold text-slate-600 mb-2">
              Select a Live NovaBrief Blog URL ({filteredArticles.length} matched)
            </div>
            <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
              {filteredArticles.map((art) => {
                const isSelected = selectedArticle.slug === art.slug;
                return (
                  <button
                    key={art.slug}
                    type="button"
                    onClick={() => setSelectedArticle(art)}
                    className={`w-full text-left p-4 rounded-xl border transition ${
                      isSelected
                        ? 'bg-blue-50/50 border-blue-600'
                        : 'bg-white border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
                      <span className="font-mono truncate">/blog/{art.slug}</span>
                      <span className="font-mono font-semibold text-emerald-700 shrink-0 tabular-nums">
                        ${art.estimatedCpcUsd.toFixed(2)} Avg CPC
                      </span>
                    </div>
                    <div className="text-sm font-bold text-slate-900 mt-1">
                      {art.title}
                    </div>
                    <div className="text-xs text-slate-600 mt-1">
                      Partner Match: <strong className="text-slate-800">{art.primaryAffiliatePartner}</strong>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right: Live Preview + Drop-in HTML Generator */}
          <div className="lg:col-span-6 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-xs text-slate-500">Selected Live Article</div>
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-blue-600 hover:underline"
                >
                  <span>{selectedArticle.url}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div>
                <label htmlFor="tracking-subid" className="block text-[11px] text-slate-500 mb-0.5">
                  Affiliate Tracking Sub-ID
                </label>
                <input
                  id="tracking-subid"
                  type="text"
                  value={trackingTag}
                  onChange={(e) => setTrackingTag(e.target.value)}
                  className="px-2.5 py-1 text-xs font-mono bg-white border border-slate-300 rounded-md"
                />
              </div>
            </div>

            {/* Rendered Visual Preview of the Callout */}
            <div className="p-5 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-xs text-slate-500">
                <span>Editor's Pick · Verified Tool & Certification Partner</span>
                <span>Disclosure: Partner link supports Nova Brief</span>
              </div>
              <h4 className="text-base font-bold text-slate-900 mb-1.5">
                {selectedArticle.primaryAffiliatePartner}
              </h4>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                {selectedArticle.ctaHookText}
              </p>
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200">
                <div className="text-xs text-slate-500">
                  Est. AdSense CPC: <strong className="font-mono text-slate-900 tabular-nums">${selectedArticle.estimatedCpcUsd.toFixed(2)}</strong> · {selectedArticle.commissionStructure}
                </div>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg">
                  Access Official Student & Engineer Offer &rarr;
                </span>
              </div>
            </div>

            {/* HTML Snippet to Copy */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700">
                  Drop-In HTML Block (Paste after 1st H2 in <code className="font-mono">/blog/{selectedArticle.slug}</code>)
                </span>
                <button
                  type="button"
                  onClick={handleCopyHtml}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition whitespace-nowrap shrink-0"
                >
                  {copiedHtml ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied Affiliate HTML</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Affiliate HTML</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed">
                <code>{generatedHtml}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* High-CPC & Affiliate Content Calendar */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8">
        <div className="mb-6">
          <div className="text-xs text-slate-500 mb-1">
            High-CPC Keyword Strategy · Maximizing Both Display Ad eCPM & Affiliate Conversions
          </div>
          <h3 className="text-xl font-bold text-slate-900">
            6 High-CPC Pillar Articles to Publish Next on novabrief.tech
          </h3>
          <p className="text-sm text-slate-600 mt-1">
            General tech news earns $1.50–$3.00 RPM. Commercial cloud, database, VPS, and accredited certification guides attract enterprise B2B advertisers bidding $14–$24 per click while converting at 3.5%+ on affiliate offers.
          </p>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600">
                <th className="py-3 px-4">Proposed Article Title & URL Slug</th>
                <th className="py-3 px-4">Search Intent</th>
                <th className="py-3 px-4 text-right">Est. AdSense CPC</th>
                <th className="py-3 px-4">Dual Monetization Pairing (Affiliate + Display)</th>
                <th className="py-3 px-4">Why It Ranks & Converts Fast</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-xs">
              {HIGH_CPC_CONTENT_CALENDAR.map((idea) => (
                <tr key={idea.targetSlug} className="hover:bg-slate-50">
                  <td className="py-3.5 px-4 align-top">
                    <div className="font-bold text-slate-900">{idea.title}</div>
                    <div className="font-mono text-slate-500 mt-0.5">{idea.targetSlug}</div>
                  </td>
                  <td className="py-3.5 px-4 align-top text-slate-600">
                    {idea.searchIntent}
                  </td>
                  <td className="py-3.5 px-4 align-top text-right font-mono font-bold text-emerald-700 tabular-nums whitespace-nowrap">
                    ${idea.estimatedCpcUsd.toFixed(2)}
                  </td>
                  <td className="py-3.5 px-4 align-top text-slate-700 font-medium max-w-xs">
                    {idea.affiliatePairing}
                  </td>
                  <td className="py-3.5 px-4 align-top text-slate-600 max-w-sm leading-relaxed">
                    {idea.whyItRanksFast}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
