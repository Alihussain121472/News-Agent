# NovaBrief Design System & Developer Style Guide

Welcome to the **NovaBrief Design System**. This guide provides all engineers and contributors with the architectural standards, design tokens, component classes, and accessibility rules required to maintain visual consistency across all public, member, and student interfaces.

---

## Table of Contents
1. [Core Principles](#1-core-principles)
2. [File Architecture](#2-file-architecture)
3. [Design Tokens & CSS Variables](#3-design-tokens--css-variables)
   - [Surface & Backgrounds](#surface--backgrounds)
   - [Text & Typography](#text--typography)
   - [Borders & Dividers](#borders--dividers)
   - [Brand & Semantic Colors](#brand--semantic-colors)
   - [Elevation & Shadows](#elevation--shadows)
4. [Standardized Component Patterns](#4-standardized-component-patterns)
   - [Navigation Action Buttons (`.btn-nav-action`)](#navigation-action-buttons-btn-nav-action)
   - [Status Pills & Badges (`.btn-pill-*`)](#status-pills--badges-btn-pill-)
   - [Profile Chip (`.nova-profile-chip`)](#profile-chip-nova-profile-chip)
   - [Alert & Feedback Banners (`.alert-feedback`)](#alert--feedback-banners-alert-feedback)
5. [Light & Dark Mode Parity Guidelines](#5-light--dark-mode-parity-guidelines)
6. [WCAG 2.2 Accessibility Standards](#6-wcag-22-accessibility-standards)
7. [Asset Pipeline & Workflow](#7-asset-pipeline--workflow)

---

## 1. Core Principles

- **Single Source of Truth**: All colors and themes originate from `static/css/variables.css`. Never introduce arbitrary hex codes or ad-hoc translucent Tailwind classes (`text-red-400`, `bg-emerald-500/10`) without guaranteed contrast.
- **Accessibility by Default**: Every foreground-to-background combination must satisfy **WCAG 2.2 Level AA** (minimum 4.5:1 for body copy; 3:1 for large headings and interactive boundary states).
- **Dark Mode Parity**: Every screen, modal, dropdown, and component must look intentional and polished in both Light (`:root`) and Dark (`html.dark`) modes.
- **Predictable State Transitions**: Interactive elements share standardized hover, focus-visible, and active states.

---

## 2. File Architecture

```text
static/css/
├── variables.css          # Core design tokens, CSS variables, and utility classes
├── variables.min.css      # Generated minified production bundle
├── website-theme.css      # Legacy theme mapping, layout rules, and card overrides
├── website-theme.min.css  # Generated minified production bundle
└── tailwind.css           # Utility styling layer
```

- **Inclusion Order** (in `templates/theme_head.html`):
  1. `variables.min.css` (declares all tokens on `:root` and `html.dark`)
  2. `tailwind.css`
  3. `website-theme.min.css` (inherits and maps tokens)

---

## 3. Design Tokens & CSS Variables

### Surface & Backgrounds

| Variable | Light Mode | Dark Mode | Usage |
| :--- | :--- | :--- | :--- |
| `--color-bg-base` | `#f8fafc` (slate-50) | `#080f1c` (navy-950) | Full page canvas backdrop |
| `--color-bg-surface` | `#ffffff` (white) | `#111c2f` (navy-900) | Cards, panels, headers, topbar |
| `--color-bg-elevated` | `#ffffff` | `#19283d` (navy-850) | Modals, dropdown menus, popovers |
| `--color-bg-subtle` | `#f1f5f9` (slate-100) | `#19283d` | Hover states, tab backgrounds |
| `--color-bg-muted` | `#e2e8f0` (slate-200) | `#24344d` | Inactive tracks, disabled inputs |
| `--color-bg-overlay` | `rgba(15, 23, 42, 0.6)` | `rgba(0, 0, 0, 0.75)` | Backdrop modals and dialogs |

### Text & Typography

| Variable | Light Mode | Dark Mode | Contrast Ratio |
| :--- | :--- | :--- | :--- |
| `--color-text-primary` | `#0f172a` (slate-900) | `#f8fafc` (slate-50) | > 14:1 (AAA) |
| `--color-text-secondary` | `#334155` (slate-700) | `#cbd5e1` (slate-300) | > 7:1 (AAA) |
| `--color-text-muted` | `#526176` (slate-600) | `#94a3b8` (slate-400) | > 4.5:1 (AA) |
| `--color-text-subtle` | `#64748b` (slate-500) | `#64748b` (slate-500) | Supplementary metadata |
| `--color-text-inverse` | `#ffffff` | `#0f172a` | Contrasting badges |

### Borders & Dividers

| Variable | Light Mode | Dark Mode | Usage |
| :--- | :--- | :--- | :--- |
| `--color-border-subtle` | `#e2e8f0` | `#1e293b` | Card dividers, section borders |
| `--color-border-default` | `#cbd5e1` | `#334155` | Button borders, input borders |
| `--color-border-strong` | `#94a3b8` | `#475569` | Active/hover borders |
| `--color-border-focus` | `#1d4ed8` | `#60a5fa` | Keyboard focus ring outlines |

### Brand & Semantic Colors

#### Primary / Brand (Blue)
- `--color-primary`: `#1d4ed8` (Light) / `#3b82f6` (Dark)
- `--color-primary-hover`: `#1e40af` (Light) / `#60a5fa` (Dark)
- `--color-primary-subtle`: `#eff6ff` (Light) / `#172554` (Dark)
- `--color-primary-text`: `#1e40af` (Light, 7.8:1) / `#bfdbfe` (Dark, 8.2:1)
- `--color-primary-border`: `#bfdbfe` (Light) / `#1e40af` (Dark)

#### Success (Emerald / Mint)
- `--color-success`: `#059669` (Light) / `#10b981` (Dark)
- `--color-success-hover`: `#047857` (Light) / `#34d399` (Dark)
- `--color-success-subtle`: `#ecfdf5` (Light) / `#064e3b` (Dark)
- `--color-success-text`: `#065f46` (Light, 8.5:1) / `#a7f3d0` (Dark, 8.4:1)
- `--color-success-border`: `#a7f3d0` (Light) / `#047857` (Dark)

#### Danger / Destructive (Red)
- `--color-danger`: `#b91c1c` (Light) / `#ef4444` (Dark)
- `--color-danger-hover`: `#991b1b` (Light) / `#f87171` (Dark)
- `--color-danger-subtle`: `#fef2f2` (Light) / `#450a0a` (Dark)
- `--color-danger-text`: `#991b1b` (Light, 7.8:1) / `#fca5a5` (Dark, 7.9:1)
- `--color-danger-border`: `#fecaca` (Light) / `#991b1b` (Dark)

#### Warning (Amber)
- `--color-warning`: `#d97706` (Light) / `#f59e0b` (Dark)
- `--color-warning-subtle`: `#fffbeb` (Light) / `#451a03` (Dark)
- `--color-warning-text`: `#92400e` (Light, 7.1:1) / `#fde68a` (Dark, 8.1:1)
- `--color-warning-border`: `#fde68a` (Light) / `#b45309` (Dark)

### Elevation & Shadows

- `--shadow-sm`: `0 1px 2px 0 rgb(15 23 42 / 0.05)`
- `--shadow-md`: `0 4px 6px -1px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.04)`
- `--shadow-lg`: `0 10px 15px -3px rgb(15 23 42 / 0.1), 0 4px 6px -4px rgb(15 23 42 / 0.05)`
- `--radius-sm`: `0.375rem` (6px)
- `--radius-md`: `0.5rem` (8px)
- `--radius-lg`: `0.75rem` (12px)
- `--radius-full`: `9999px`

---

## 4. Standardized Component Patterns

### Navigation Action Buttons (`.btn-nav-action`)
Use for topbar and header utility links (e.g., Home, Refresh, Site, Theme Switcher).
```html
<!-- Home / Site link -->
<a href="/" class="btn-nav-action px-3 py-1.5 rounded-lg text-xs font-medium transition" aria-label="Return to Homepage">
  <i class="fas fa-home mr-1" aria-hidden="true"></i>Home
</a>

<!-- Icon-only action (e.g., Theme Switcher) -->
<button data-theme-toggle aria-label="Switch theme mode" class="btn-nav-action p-2 rounded-lg text-xs transition">
  <i class="fas fa-moon dark:hidden" aria-hidden="true"></i>
  <i class="fas fa-sun hidden dark:inline" aria-hidden="true"></i>
</button>
```

### Status Pills & Badges (`.btn-pill-*`)
Use for interactive pills, category badges, or destructive actions.

```html
<!-- Success / Python Hub Pill -->
<a href="/user/python" class="btn-pill-success px-3 py-1.5 rounded-lg text-xs font-semibold" aria-label="Open Python Practice Hub">
  <i class="fab fa-python mr-1" aria-hidden="true"></i>Python Hub
</a>

<!-- Danger / Logout Button -->
<button type="button" onclick="handleLogout()" class="btn-pill-danger px-3 py-1.5 rounded-lg text-xs font-semibold transition" aria-label="Log out of your account">
  <i class="fas fa-sign-out-alt mr-1" aria-hidden="true"></i>Logout
</button>

<!-- Primary / Informational Pill -->
<span class="btn-pill-primary px-2.5 py-1 rounded-full text-xs font-semibold">
  Verified Program
</span>
```

### Profile Chip (`.nova-profile-chip`)
Used in topbar headers to display user identity with guaranteed contrast in all themes.

```html
<div class="nova-profile-chip" aria-label="Your account">
  <div class="nova-profile-avatar" id="headerAvatar" aria-hidden="true">{{ user_initial or '?' }}</div>
  <div class="nova-profile-copy">
    <div class="nova-profile-name" id="headerName">{{ display_name or user_name or 'My account' }}</div>
    <div class="nova-profile-email" id="headerEmail">{{ user_email }}</div>
  </div>
</div>
```

### Alert & Feedback Banners (`.alert-feedback`)
Use for system notifications, form error messages, or submission confirmations.

```html
<div class="alert-feedback alert-success" role="alert">
  <i class="fas fa-check-circle mr-1.5" aria-hidden="true"></i> Profile updated successfully.
</div>

<div class="alert-feedback alert-danger" role="alert">
  <i class="fas fa-exclamation-triangle mr-1.5" aria-hidden="true"></i> Invalid email or password.
</div>
```

---

## 5. Light & Dark Mode Parity Guidelines

1. **Avoid hardcoded hex colors in templates**:
   * ❌ `<div style="background-color: #1e293b; color: #fff;">`
   * ✅ `<div class="bg-white dark:bg-slate-900 border border-neutral-200 dark:border-slate-800">` or `var(--color-bg-surface)`
2. **Never use low-contrast translucent tints for text**:
   * ❌ `class="text-red-400 bg-red-500/20"` (fails 4.5:1 ratio on light surfaces)
   * ✅ `class="btn-pill-danger"` (automatically evaluates to `#991b1b` on `#fef2f2` in light mode, and `#fca5a5` on `#450a0a` in dark mode)
3. **Always check theme toggle pairing**:
   * Ensure both `.fa-moon` (hidden in dark) and `.fa-sun` (hidden in light) are enclosed with `aria-hidden="true"` and an informative `aria-label` on the parent button.

---

## 6. WCAG 2.2 Accessibility Standards

- **Contrast Ratios**:
  - Normal text (< 18pt or < 14pt bold): minimum **4.5:1**
  - Large text (>= 18pt or >= 14pt bold): minimum **3.0:1**
  - UI components and graphical objects: minimum **3.0:1**
- **Focus Rings**:
  - Always preserve `:focus-visible` styling (`outline: 2px solid var(--color-border-focus); outline-offset: 2px;`). Never remove focus rings without providing an accessible alternative.
- **Icons as Actions**:
  - Any button or link with only an icon or abbreviated text must provide an explicit `aria-label`.

---

## 7. Asset Pipeline & Workflow

When modifying or adding new styles:

1. **Add Tokens**: If adding a new color or token, define it in both `:root` and `html.dark` inside `static/css/variables.css`.
2. **Minify Assets**: Run the minification script before committing:
   ```bash
   python scripts/minify_assets.py
   ```
   *Note: Render's `build.sh` also automatically executes this during deployment builds.*
3. **Run Automated Tests**: Verify that existing application routes and templates render cleanly:
   ```bash
   python -m unittest discover tests
   ```
4. **Deploy**: Push changes to `main` and `render-blueprint-fix`.
