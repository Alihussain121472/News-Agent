import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateAdSlotId,
  generateAdSenseSnippet,
  calculateRevenueProjection,
  generateAffiliateCalloutHtml,
  analyzeSeoKeywordDensity,
  generateMasterThemeJsPatch,
  analyzeTrafficQuality,
  getArticleWireframeZones,
  generateGitPushTerminalScript,
  patchNovaBriefProjectFile,
  PUBLISHER_ID,
  LIVE_BLOG_ARTICLES,
  SAMPLE_ARTICLE_PRESETS,
} from './monetizationEngine.ts';

test('validateAdSlotId rejects "auto" and non-10-digit IDs, accepts 10-digit numeric IDs', () => {
  const autoCheck = validateAdSlotId('auto');
  assert.equal(autoCheck.valid, false);
  assert.ok(autoCheck.reason.includes('CRITICAL BUG'));

  const shortCheck = validateAdSlotId('12345');
  assert.equal(shortCheck.valid, false);

  const validCheck = validateAdSlotId('4829103847');
  assert.equal(validCheck.valid, true);
});

test('generateAdSenseSnippet embeds publisher ID ca-pub-1036052096443002 and valid numeric slot ID', () => {
  const snippet = generateAdSenseSnippet('in-article', {
    publisherId: PUBLISHER_ID,
    inArticleSlotId: '4829103847',
    sidebarSlotId: '5910293847',
    inFeedSlotId: '6029384756',
    multiplexSlotId: '7192837465',
    headerLeaderboardSlotId: '8293847561',
    enableLazyLoad: true,
    minContainerHeightPx: 280,
  });

  assert.ok(snippet.includes('data-ad-client="ca-pub-1036052096443002"'));
  assert.ok(snippet.includes('data-ad-slot="4829103847"'));
  assert.ok(!snippet.includes('data-ad-slot="auto"'));
  assert.ok(snippet.includes('min-height: 280px'));
});

test('calculateRevenueProjection computes monthly and 13-day remaining revenue accurately', () => {
  const result = calculateRevenueProjection({
    dailyPageviews: 1500,
    tier1TrafficSharePct: 50,
    pagesPerSession: 2.2,
    adImpressionsPerPage: 3,
    estimatedCtrPct: 2.4,
    averageCpcUsd: 1.25,
    affiliateClickRatePct: 3.5,
    affiliateConversionRatePct: 2.5,
    averageAffiliateCommissionUsd: 35,
    newsletterSponsorsPerMonth: 2,
    sponsorRateUsd: 75,
  });

  assert.equal(result.monthlyPageviews, 45000);
  assert.equal(result.monthlyAdImpressions, 135000);
  assert.ok(result.monthlyAdSenseRevenueUsd > 0);
  assert.ok(result.monthlyAffiliateRevenueUsd > 0);
  assert.equal(result.monthlySponsorshipRevenueUsd, 150);
  assert.equal(
    result.totalMonthlyRevenueUsd,
    Number(
      (
        result.monthlyAdSenseRevenueUsd +
        result.monthlyAffiliateRevenueUsd +
        result.monthlySponsorshipRevenueUsd
      ).toFixed(2)
    )
  );
  assert.ok(result.remainingMonthRevenueUsd > 0);
});

test('generateAffiliateCalloutHtml produces sponsored nofollow partner HTML block', () => {
  const html = generateAffiliateCalloutHtml(LIVE_BLOG_ARTICLES[0], 'novabrief-oct26');
  assert.ok(html.includes('rel="sponsored nofollow noopener"'));
  assert.ok(html.includes('novabrief-oct26'));
  assert.ok(html.includes(LIVE_BLOG_ARTICLES[0].slug));
});

test('analyzeSeoKeywordDensity calculates primary keyword density and increases eCPM when high-CPM phrases are injected', () => {
  const preset = SAMPLE_ARTICLE_PRESETS[0];
  const initialAnalysis = analyzeSeoKeywordDensity(preset.content, preset.primaryKeyword);

  assert.ok(initialAnalysis.wordCount > 100);
  assert.equal(initialAnalysis.primaryKeywordCount, 3);
  assert.ok(initialAnalysis.primaryKeywordDensityPct > 0);
  assert.ok(initialAnalysis.missingHighCpmSuggestions.length > 0);

  const firstSuggestion = initialAnalysis.missingHighCpmSuggestions[0];
  const enrichedContent = `${preset.content}\n\n${firstSuggestion.injectionSentence}`;
  const updatedAnalysis = analyzeSeoKeywordDensity(enrichedContent, preset.primaryKeyword);

  assert.equal(updatedAnalysis.detectedHighCpmKeywords.length, initialAnalysis.detectedHighCpmKeywords.length + 1);
  assert.ok(updatedAnalysis.estimatedContextualCpmUsd > initialAnalysis.estimatedContextualCpmUsd);
});

test('generateMasterThemeJsPatch preserves NovaTheme and repairs data-ad-slot="auto"', () => {
  const script = generateMasterThemeJsPatch({
    publisherId: PUBLISHER_ID,
    inArticleSlotId: '4829103847',
    sidebarSlotId: '5910293846',
    inFeedSlotId: '6029384751',
    multiplexSlotId: '7192837462',
    headerLeaderboardSlotId: '8293847563',
    enableLazyLoad: true,
    minContainerHeightPx: 260,
  });

  assert.ok(script.includes('window.NovaTheme'));
  assert.ok(script.includes('ca-pub-1036052096443002'));
  assert.ok(script.includes('4829103847'));
  assert.ok(script.includes('data-overlays'));
});

test('analyzeTrafficQuality normalizes channel shares and computes higher CTR/Quality for Organic-heavy vs Social-heavy mix', () => {
  const organicHeavy = analyzeTrafficQuality({ organicPct: 70, socialPct: 15, directPct: 15 });
  const socialHeavy = analyzeTrafficQuality({ organicPct: 15, socialPct: 70, directPct: 15 });

  assert.equal(
    organicHeavy.normalizedOrganicPct +
      organicHeavy.normalizedSocialPct +
      organicHeavy.normalizedDirectPct,
    100
  );
  assert.equal(organicHeavy.dominantChannel, 'Organic Search');
  assert.equal(socialHeavy.dominantChannel, 'Social Media');
  assert.ok(organicHeavy.trafficQualityScore > socialHeavy.trafficQualityScore);
  assert.ok(organicHeavy.blendedExpectedCtrPct > socialHeavy.blendedExpectedCtrPct);
  assert.equal(organicHeavy.channelPlaybooks.length, 3);
});

test('getArticleWireframeZones and generateGitPushTerminalScript reflect current slotConfig', () => {
  const config = {
    publisherId: PUBLISHER_ID,
    inArticleSlotId: '4829103847',
    sidebarSlotId: 'auto',
    inFeedSlotId: '6029384751',
    multiplexSlotId: '7192837462',
    headerLeaderboardSlotId: '8293847563',
    enableLazyLoad: true,
    minContainerHeightPx: 260,
  };
  const zones = getArticleWireframeZones(config);
  assert.equal(zones.length, 5);
  assert.equal(zones.find((z) => z.id === 'in-article-1')?.isValidSlot, true);
  assert.equal(zones.find((z) => z.id === 'sidebar-sticky')?.isValidSlot, false);

  const gitPushCmd = generateGitPushTerminalScript(config);
  assert.ok(gitPushCmd.includes('git push origin render-role-dashboards'));
  assert.ok(gitPushCmd.includes('static/js/theme.js'));
});

test('patchNovaBriefProjectFile replaces data-ad-slot="auto" and injects Multiplex in blog_post.html', () => {
  const config = {
    publisherId: PUBLISHER_ID,
    inArticleSlotId: '4829103847',
    sidebarSlotId: '5910293846',
    inFeedSlotId: '6029384751',
    multiplexSlotId: '7192837462',
    headerLeaderboardSlotId: '8293847563',
    enableLazyLoad: true,
    minContainerHeightPx: 260,
  };

  const sampleBlogPostHtml = `<html><head><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1036052096443002" crossorigin="anonymous"></script></head><body><article class="article-body"><ins class="adsbygoogle" style="display:block; text-align:center;" data-ad-layout="in-article" data-ad-format="fluid" data-ad-client="ca-pub-1036052096443002" data-ad-slot="auto"></ins></article></body></html>`;
  const patched = patchNovaBriefProjectFile('blog_post.html', sampleBlogPostHtml, config);

  assert.equal(patched.wasModified, true);
  assert.ok(!patched.patchedContent.includes('data-ad-slot="auto"'));
  assert.ok(patched.patchedContent.includes('data-ad-slot="4829103847"'));
  assert.ok(patched.patchedContent.includes('data-ad-slot="7192837462"'));
  assert.ok(patched.patchedContent.includes('data-overlays="bottom"'));
});



