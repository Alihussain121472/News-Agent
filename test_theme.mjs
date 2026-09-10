import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('./static/js/theme.js', import.meta.url), 'utf8');
function environment(saved, blocked = false) {
  const values = new Map(saved === undefined ? [] : [['color-theme', saved]]);
  const classes = new Set();
  const root = {
    dataset: {}, style: {}, classList: {
      contains: value => classes.has(value),
      toggle(value, enabled) { if (enabled) classes.add(value); else classes.delete(value); }
    }
  };
  const label = { textContent: '' };
  const button = { attributes: {}, querySelector: () => label,
    setAttribute(key, value) { this.attributes[key] = value; } };
  const events = {};
  const meta = {};
  const document = { documentElement: root,
    querySelectorAll: () => [button], querySelector: () => meta,
    addEventListener: (name, fn) => { events[name] = fn; } };
  const window = {
    addEventListener: (name, fn) => { events[name] = fn; },
    matchMedia() { throw new Error('OS theme must not select the default.'); }
  };
  const localStorage = {
    getItem(key) { if (blocked) throw new Error('Storage blocked'); return values.get(key) ?? null; },
    setItem(key, value) { if (blocked) throw new Error('Storage blocked'); values.set(key, value); }
  };
  vm.runInNewContext(source, { document, window, localStorage });
  return { root, window, events, button, label, values, meta };
}

test('First visit uses light mode even if the device prefers dark', () => {
  const app = environment();
  assert.equal(app.root.dataset.theme, 'light');
  assert.equal(app.root.style.colorScheme, 'light');
  assert.equal(app.values.has('color-theme'), false);
  assert.equal(app.button.attributes['aria-label'], 'Switch to dark mode');
});
test('An explicit dark selection is restored before rendering', () => {
  const app = environment('dark');
  assert.equal(app.root.classList.contains('dark'), true);
  assert.equal(app.root.style.colorScheme, 'dark');
  assert.equal(app.button.attributes['aria-pressed'], 'true');
  assert.equal(app.label.textContent, 'Light mode');
});
test('Unknown stored values and stored light use light mode', () => {
  for (const value of ['light', 'system', '', 'DARK']) {
    assert.equal(environment(value).root.dataset.theme, 'light');
  }
});
test('Toggle persists a selection and updates accessible labels', () => {
  const app = environment();
  app.window.NovaTheme.toggle();
  assert.equal(app.values.get('color-theme'), 'dark');
  assert.equal(app.meta.content, '#080f1c');
  app.window.NovaTheme.toggle();
  assert.equal(app.values.get('color-theme'), 'light');
  assert.equal(app.button.attributes['aria-pressed'], 'false');
  assert.equal(app.meta.content, '#f5f7fb');
});
test('The theme switch still works when browser storage is blocked', () => {
  const app = environment(undefined, true);
  assert.equal(app.root.dataset.theme, 'light');
  app.window.toggleTheme();
  assert.equal(app.root.dataset.theme, 'dark');
});
test('Theme changes sync across tabs; clearing preference restores light', () => {
  const app = environment();
  app.values.set('color-theme', 'dark');
  app.events.storage({ key: 'color-theme' });
  assert.equal(app.root.dataset.theme, 'dark');
  app.values.clear();
  app.events.storage({ key: null });
  assert.equal(app.root.dataset.theme, 'light');
});
test('Clicking a toggle icon runs a single toggle; unrelated clicks do not', () => {
  const app = environment();
  app.events.click({ target: { closest: () => app.button } });
  assert.equal(app.root.dataset.theme, 'dark');
  app.events.click({ target: { closest: () => null } });
  assert.equal(app.root.dataset.theme, 'dark');
});
