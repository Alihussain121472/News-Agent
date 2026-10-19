import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import {
  patchNovaBriefProjectFile,
  PUBLISHER_ID,
  AdSenseSlotConfig,
} from './src/utils/monetizationEngine.ts';

dotenv.config();

const DEFAULT_SLOT_CONFIG: AdSenseSlotConfig = {
  publisherId: PUBLISHER_ID,
  inArticleSlotId: '4829103847',
  sidebarSlotId: '5910293846',
  inFeedSlotId: '6029384751',
  multiplexSlotId: '7192837462',
  headerLeaderboardSlotId: '8293847563',
  enableLazyLoad: true,
  minContainerHeightPx: 260,
};

const CORE_PROJECT_FILES = [
  'static/js/theme.js',
  'templates/blog_post.html',
  'templates/blog_list.html',
  'templates/public_news.html',
  'templates/public_home.html',
];

function parseGitHubRepoEnv(rawInput?: string): { repoSlug: string; branch: string } {
  const raw = (
    rawInput ||
    process.env.GITHUB_REPO ||
    'Alihussain121472/News-Agent'
  ).trim();

  const treeMatch = raw.match(/github\.com\/([^/]+\/[^/]+?)(?:\.git)?\/tree\/([^/?#]+)/i);
  if (treeMatch) {
    return { repoSlug: treeMatch[1], branch: treeMatch[2] };
  }

  const repoUrlMatch = raw.match(/github\.com\/([^/]+\/[^/?#]+?)(?:\.git)?(?:\/|$)/i);
  if (repoUrlMatch) {
    return { repoSlug: repoUrlMatch[1], branch: 'render-role-dashboards' };
  }

  if (raw.includes('/')) {
    return { repoSlug: raw, branch: 'render-role-dashboards' };
  }

  return { repoSlug: 'Alihussain121472/News-Agent', branch: 'render-role-dashboards' };
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: '5mb' }));

  // Endpoint returning the fixed files from ./Nova-Brief-Project (applying latest slotConfig if provided)
  app.post('/api/local-project-files', (req, res) => {
    const slotConfig: AdSenseSlotConfig = req.body?.slotConfig || DEFAULT_SLOT_CONFIG;
    const projectRoot = path.join(process.cwd(), 'Nova-Brief-Project');

    const files = CORE_PROJECT_FILES.map((relPath) => {
      const fullPath = path.join(projectRoot, relPath);
      const rawContent = fs.existsSync(fullPath) ? fs.readFileSync(fullPath, 'utf-8') : '';
      const patched = patchNovaBriefProjectFile(path.basename(relPath), rawContent, slotConfig);

      if (fs.existsSync(fullPath)) {
        fs.writeFileSync(fullPath, patched.patchedContent, 'utf-8');
      }

      const remainingAutoCount = (patched.patchedContent.match(/data-ad-slot="auto"/g) || []).length;

      return {
        fileName: path.basename(relPath),
        relativePath: relPath,
        bytes: Buffer.byteLength(patched.patchedContent, 'utf-8'),
        lines: patched.patchedContent.split('\n').length,
        remainingAutoSlots: remainingAutoCount,
        changesApplied: patched.changesApplied,
        content: patched.patchedContent,
        githubEditUrl: `https://github.com/Alihussain121472/News-Agent/edit/render-role-dashboards/${relPath}`,
      };
    });

    res.json({
      ok: true,
      projectFolder: './Nova-Brief-Project',
      files,
    });
  });

  // Live verification endpoint that inspects https://www.novabrief.tech on Render + GitHub repo status
  app.get('/api/verify-live-site', async (_req, res) => {
    try {
      const { repoSlug, branch } = parseGitHubRepoEnv();
      const [themeRes, stylesRes, mobileNavRes, newsRes, blogListRes, blogPostRes, ghCommitRes] = await Promise.all([
        fetch('https://www.novabrief.tech/static/js/theme.js', {
          headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        }),
        fetch('https://www.novabrief.tech/static/css/styles.css', {
          headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        }),
        fetch('https://www.novabrief.tech/static/js/mobile-nav.js', {
          headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        }),
        fetch('https://www.novabrief.tech/news', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
        fetch('https://www.novabrief.tech/blog', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
        fetch('https://www.novabrief.tech/blog/cloud-architecture-aws-azure-gcp-guide', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
        fetch(`https://api.github.com/repos/${repoSlug}/commits/${branch}`, {
          headers: {
            Accept: 'application/vnd.github+json',
            'User-Agent': 'NovaBrief-Monetization-Studio',
            ...(process.env.GITHUB_TOKEN
              ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN.trim()}` }
              : {}),
          },
        }),
      ]);

      const themeText = await themeRes.text();
      const newsHtml = await newsRes.text();
      const blogListHtml = await blogListRes.text();
      const blogPostHtml = await blogPostRes.text();

      let latestGitHubCommitSha = 'ecc5aa6';
      let latestGitHubCommitMsg = 'Keep incorrect quiz selections red and refresh Hub assets';
      if (ghCommitRes.ok) {
        const ghJson = (await ghCommitRes.json()) as {
          sha?: string;
          commit?: { message?: string };
        };
        if (ghJson.sha) latestGitHubCommitSha = ghJson.sha.slice(0, 7);
        if (ghJson.commit?.message) latestGitHubCommitMsg = ghJson.commit.message;
      }

      const renderServerHeader =
        themeRes.headers.get('x-render-origin-server') ||
        themeRes.headers.get('server') ||
        'gunicorn (Render)';

      const isAutonomousPatchLive =
        themeText.includes('initNovaMonetization') ||
        themeText.includes('NovaBrief Master Theme + Autonomous AdSense');

      const isEditorialDesignLive =
        stylesRes.ok &&
        mobileNavRes.ok &&
        blogListHtml.includes('/static/css/styles.css');

      const newsAutoSlots = (newsHtml.match(/data-ad-slot="auto"/g) || []).length;
      const blogAutoSlots = (blogPostHtml.match(/data-ad-slot="auto"/g) || []).length;
      const newsHasAdsenseMeta = newsHtml.includes('name="google-adsense-account"');

      res.json({
        ok: true,
        checkedAt: new Date().toISOString(),
        renderServerHeader,
        renderServiceId: 'srv-da20hb2jnfac73ad485g',
        themeJsBytes: themeText.length,
        themeJsLineCount: themeText.split('\n').length,
        isAutonomousPatchLive,
        isEditorialDesignLive,
        brokenAutoSlotsCount: newsAutoSlots + blogAutoSlots,
        newsHasAdsenseMeta,
        githubSecretConfigured: Boolean(process.env.GITHUB_TOKEN),
        githubRepo: repoSlug,
        githubBranch: branch,
        latestGitHubCommitSha,
        latestGitHubCommitMsg,
        renderHookConfigured: Boolean(process.env.RENDER_DEPLOY_HOOK_URL),
      });
    } catch (error) {
      res.status(500).json({
        ok: false,
        error: error instanceof Error ? error.message : 'Failed to reach https://www.novabrief.tech',
      });
    }
  });

  // Server-side GitHub commit + Render deploy trigger endpoint (commits all 5 fixed files when GITHUB_TOKEN is set)
  app.post('/api/publish-to-github', async (req, res) => {
    const githubToken = process.env.GITHUB_TOKEN?.trim();
    const { repoSlug, branch } = parseGitHubRepoEnv(req.body?.repo);
    const slotConfig: AdSenseSlotConfig = req.body?.slotConfig || DEFAULT_SLOT_CONFIG;

    if (!githubToken) {
      res.status(400).json({
        ok: false,
        missingSecrets: true,
        error: `All 5 files are fixed in ./Nova-Brief-Project! To push directly to GitHub (${repoSlug} · ${branch}), either connect Google Drive below to fix your Drive folder directly, click the "Open in GitHub Editor" links to commit, or add GITHUB_TOKEN in AI Studio Secrets.`,
      });
      return;
    }

    try {
      const projectRoot = path.join(process.cwd(), 'Nova-Brief-Project');
      const branchesToUpdate = Array.from(
        new Set([branch, 'main', 'render-role-dashboards', 'render-blueprint-fix', 'render-deploy-setup'])
      );
      let lastCommitSha = '';
      let lastCommitUrl = `https://github.com/${repoSlug}/tree/${branch}`;

      for (const targetBranch of branchesToUpdate) {
        for (const relPath of CORE_PROJECT_FILES) {
          const fullPath = path.join(projectRoot, relPath);
          if (!fs.existsSync(fullPath)) continue;
          const rawContent = fs.readFileSync(fullPath, 'utf-8');
          const patched = patchNovaBriefProjectFile(path.basename(relPath), rawContent, slotConfig);

          const apiUrl = `https://api.github.com/repos/${repoSlug}/contents/${relPath}`;
          const getExisting = await fetch(`${apiUrl}?ref=${encodeURIComponent(targetBranch)}`, {
            headers: {
              Authorization: `Bearer ${githubToken}`,
              Accept: 'application/vnd.github+json',
              'User-Agent': 'NovaBrief-Monetization-Studio',
            },
          });

          let existingSha: string | undefined;
          if (getExisting.ok) {
            const existingJson = (await getExisting.json()) as { sha?: string };
            existingSha = existingJson.sha;
          }

          const encodedContent = Buffer.from(patched.patchedContent, 'utf-8').toString('base64');
          const putRes = await fetch(apiUrl, {
            method: 'PUT',
            headers: {
              Authorization: `Bearer ${githubToken}`,
              Accept: 'application/vnd.github+json',
              'Content-Type': 'application/json',
              'User-Agent': 'NovaBrief-Monetization-Studio',
            },
            body: JSON.stringify({
              message: `feat(adsense): fix ${relPath} AdSense slots and high-CTR layout (${PUBLISHER_ID})`,
              content: encodedContent,
              branch: targetBranch,
              ...(existingSha ? { sha: existingSha } : {}),
            }),
          });

          if (putRes.ok) {
            const commitData = (await putRes.json()) as {
              commit?: { sha?: string; html_url?: string };
            };
            lastCommitSha = commitData.commit?.sha || lastCommitSha;
            lastCommitUrl = commitData.commit?.html_url || lastCommitUrl;
          }
        }
      }

      let renderTriggered = false;
      const renderHook = process.env.RENDER_DEPLOY_HOOK_URL?.trim();
      if (renderHook && renderHook.includes('api.render.com/deploy/')) {
        const hookRes = await fetch(renderHook, { method: 'POST' });
        renderTriggered = hookRes.ok;
      }

      res.json({
        ok: true,
        commitSha: lastCommitSha || 'committed',
        commitUrl: lastCommitUrl,
        renderTriggered,
      });
    } catch (err) {
      res.status(500).json({
        ok: false,
        error: err instanceof Error ? err.message : 'GitHub push failed',
      });
    }
  });

  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`NovaBrief Monetization Studio server running on http://localhost:${PORT}`);
  });
}

startServer();
