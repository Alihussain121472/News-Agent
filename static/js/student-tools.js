/* Student-only tools. Private data stays on the server, not in localStorage. */
(function () {
  'use strict';

  const byId = id => document.getElementById(id);
  const statuses = {
    saved: 'Saved', preparing: 'Preparing', submitted: 'Submitted',
    interview: 'Interview', offer: 'Offer', closed: 'Closed'
  };
  const checklistKeys = ['eligibility', 'cv', 'statement', 'documents'];
  const state = {
    csrf: '', applications: [], tasks: [], plannerLoaded: false,
    plannerRead: null, programRead: null, programData: null, programPage: 1,
    programFilters: null, version: 0, locks: new Set(), tracking: new Set()
  };
  // The initial GETs are sequenced so two first reads cannot create competing
  // CSRF tokens in the same cookie session when a student switches tabs quickly.
  let readQueue = Promise.resolve();

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function button(text, action, className) {
    const node = element('button', className || 'st-button st-small', text);
    node.type = 'button';
    node.addEventListener('click', action);
    return node;
  }

  function validId(value) {
    return Number.isInteger(value) && value > 0 && value <= 2147483647;
  }

  function safeLink(value) {
    if (typeof value !== 'string' || !value || value.length > 2000 || /[\s\\\u0000-\u001f\u007f-\u009f]/u.test(value)) return '';
    try {
      const url = new URL(value);
      if (!['http:', 'https:'].includes(url.protocol) || !url.hostname || url.username || url.password) return '';
      return url.href;
    } catch (_) {
      return '';
    }
  }

  function providerLink(value) {
    const href = safeLink(value);
    if (!href) return null;
    const link = element('a', 'st-button st-small', 'Visit provider ↗');
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.setAttribute('aria-label', 'Visit provider website (opens in a new tab)');
    return link;
  }

  function notice(id, message, isError, retry) {
    const box = byId(id);
    box.replaceChildren();
    box.hidden = !message;
    box.classList.toggle('st-error', Boolean(isError));
    if (!message) return;
    box.append(element('span', '', message));
    if (retry) box.append(button('Refresh and retry', retry, 'st-button st-small st-retry'));
  }

  function formError(id, message) {
    const box = byId(id);
    box.textContent = message || '';
    box.hidden = !message;
  }

  function emptyState(title, description, actionLabel, action) {
    const box = element('div', 'st-empty');
    box.append(element('h4', '', title), element('p', '', description));
    if (action) box.append(button(actionLabel, action));
    return box;
  }

  async function fetchResponse(path, options) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 20000);
    const writing = options && options.method && options.method !== 'GET';
    try {
      const response = await fetch(path, {
        credentials: 'same-origin', cache: 'no-store',
        ...options, signal: controller.signal
      });
      if (response.redirected) throw new Error('Please sign in again, then reopen your planner.');
      if (!response.ok) {
        let data;
        try { data = await response.json(); } catch (_) { data = {}; }
        const fallback = response.status === 401 ? 'Please sign in again to use your private planner.' :
          'The request could not be completed. Please try again.';
        throw new Error(typeof data.message === 'string' ? data.message.slice(0, 500) : fallback);
      }
      return response;
    } catch (error) {
      if (error.name === 'AbortError' || error instanceof TypeError) {
        throw new Error(writing ?
          'The connection was interrupted. Your change may have reached the server. Refresh your planner before trying again.' :
          'We could not load your data. Check your connection and retry.');
      }
      throw error;
    } finally {
      window.clearTimeout(timer);
    }
  }

  async function jsonRequest(path, options) {
    const response = await fetchResponse(path, options);
    let data;
    try { data = await response.json(); } catch (_) {
      throw new Error('The server returned an unexpected response. Refresh your planner to check the latest saved information.');
    }
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      throw new Error('The server returned an unexpected response. Please refresh and retry.');
    }
    if (typeof data.csrf_token === 'string') state.csrf = data.csrf_token;
    return data;
  }

  function readJSON(path) {
    const next = readQueue.then(() => jsonRequest(path));
    readQueue = next.catch(() => undefined);
    return next;
  }

  async function writeJSON(path, method, data) {
    if (!state.csrf) await readJSON('/api/user/planner');
    const result = await jsonRequest(path, {
      method,
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': state.csrf },
      ...(data !== undefined ? { body: JSON.stringify(data) } : {})
    });
    if (result.status !== 'success' || (method !== 'DELETE' && (!result.item || !validId(result.item.id)))) {
      throw new Error('Your change could not be confirmed. Refresh your planner before trying again.');
    }
    state.version += 1;
    return result;
  }

  // Parse a calendar date at local noon, never as UTC midnight. The numeric
  // date-only comparison below is insensitive to daylight-saving transitions.
  function calendarDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(year, month - 1, day, 12);
    if (year < 2000 || year > 2100 || date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
    return date;
  }

  function daysUntil(value) {
    const date = calendarDate(value);
    if (!date) return null;
    const today = new Date();
    return Math.round((Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) -
      Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000);
  }

  function dateBadge(value, actionable, label) {
    const date = calendarDate(value);
    if (!date) return element('span', 'st-tag', label === 'Due' ? 'No due date' : 'Deadline not confirmed');
    const days = daysUntil(value);
    let hint = '';
    let className = 'st-tag';
    if (actionable) {
      if (days < 0) { hint = ' · Overdue'; className += ' st-overdue'; }
      else if (days === 0) { hint = ' · Today'; className += ' st-urgent'; }
      else if (days === 1) { hint = ' · Tomorrow'; className += ' st-urgent'; }
      else if (days <= 7) { hint = ` · In ${days} days`; className += ' st-urgent'; }
    }
    const formatted = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    return element('span', className, `${label || 'Deadline'} ${formatted}${hint}`);
  }

  function sortItems() {
    state.applications.sort((a, b) => (a.deadline || '9999').localeCompare(b.deadline || '9999') || b.id - a.id);
    state.tasks.sort((a, b) => Number(a.completed) - Number(b.completed) ||
      (a.due_date || '9999').localeCompare(b.due_date || '9999') || b.id - a.id);
  }

  function remember(kind, item) {
    const collection = kind === 'application' ? state.applications : state.tasks;
    const index = collection.findIndex(existing => existing.id === item.id);
    if (index === -1) collection.push(item);
    else collection[index] = item;
    sortItems();
    if (state.plannerLoaded) renderPlanner();
  }

  function renderSummary() {
    const activeDeadlines = state.applications.filter(item => ['saved', 'preparing'].includes(item.status));
    const upcoming = activeDeadlines.filter(item => {
      const days = daysUntil(item.deadline);
      return days !== null && days >= 0 && days <= 7;
    }).length;
    const stats = [
      [state.applications.length, 'Applications tracked'],
      [upcoming, 'Application deadlines · next 7 days'],
      [state.tasks.filter(item => !item.completed).length, 'Unfinished study tasks']
    ];
    byId('plannerSummary').replaceChildren(...stats.map(([count, label]) => {
      const card = element('div', 'st-stat');
      card.append(element('strong', '', count), element('span', '', label));
      return card;
    }));
  }

  function renderApplications() {
    const filter = byId('applicationStatusFilter').value;
    const items = state.applications.filter(item => !filter || item.status === filter);
    const list = byId('plannerApplications');
    list.replaceChildren();
    if (!items.length) {
      list.append(emptyState(filter ? 'No applications with this status' : 'Keep your next opportunity on track',
        filter ? 'Choose a different status to see your other applications.' :
          'Add an application yourself, or find a program and choose Track application. Your notes and checklist will stay here.',
        filter ? 'Show all applications' : 'Explore programs', () => {
          if (filter) { byId('applicationStatusFilter').value = ''; renderApplications(); }
          else window.switchTab('programs');
        }));
      return;
    }
    items.forEach(item => {
      const card = element('article', 'st-application');
      const top = element('div', 'st-application-top');
      const heading = element('div');
      heading.append(element('h4', '', item.title));
      if (item.company) heading.append(element('p', 'st-organization', item.company));
      const statusLabel = element('label', 'st-status', 'Status');
      const select = element('select');
      select.setAttribute('aria-label', `Status for ${item.title}`);
      Object.entries(statuses).forEach(([value, text]) => {
        const option = element('option', '', text);
        option.value = value;
        option.selected = value === item.status;
        select.append(option);
      });
      select.disabled = state.locks.has(`application-${item.id}`);
      select.addEventListener('change', () => updateQuick('application', item, { status: select.value }, select));
      statusLabel.append(select);
      top.append(heading, statusLabel);
      const tags = element('div', 'st-tags');
      tags.append(dateBadge(item.deadline, ['saved', 'preparing'].includes(item.status)));
      const checked = new Set(Array.isArray(item.checklist) ? item.checklist.filter(key => checklistKeys.includes(key)) : []);
      const preparation = element('p', 'st-checklist-summary', `${checked.size} of 4 preparation steps complete`);
      const progress = element('div', 'st-progress');
      progress.setAttribute('aria-hidden', 'true');
      const fill = element('span');
      fill.style.width = `${checked.size * 25}%`;
      progress.append(fill);
      card.append(top, tags, preparation, progress);
      if (item.notes) card.append(element('p', 'st-note-preview', String(item.notes).slice(0, 240) + (item.notes.length > 240 ? '…' : '')));
      const actions = element('div', 'st-actions');
      actions.append(button('Edit details & checklist', () => openApplication(item)));
      const link = providerLink(item.registration_url);
      if (link) actions.append(link);
      actions.append(button('Remove', () => removeItem('application', item), 'st-button st-small st-danger'));
      actions.querySelectorAll('button').forEach(control => { control.disabled = state.locks.has(`application-${item.id}`); });
      card.append(actions);
      list.append(card);
    });
  }

  function renderTasks() {
    const showCompleted = byId('showCompletedTasks').checked;
    const items = state.tasks.filter(item => showCompleted || !item.completed);
    const list = byId('plannerTasks');
    list.replaceChildren();
    if (!items.length) {
      const hasCompleted = state.tasks.some(item => item.completed);
      list.append(emptyState(hasCompleted && !showCompleted ? 'All tasks complete' : 'Plan one useful step',
        hasCompleted && !showCompleted ? 'Show completed tasks to review your work, or add your next goal.' :
          'Create a study task, give it a due date if needed, and check it off when you finish.',
        'Add study task', () => openTask()));
      return;
    }
    items.forEach(item => {
      const row = element('div', `st-task${item.completed ? ' st-complete' : ''}`);
      const check = element('input');
      check.type = 'checkbox';
      check.id = `study-task-${item.id}`;
      check.checked = Boolean(item.completed);
      check.disabled = state.locks.has(`task-${item.id}`);
      check.addEventListener('change', () => updateQuick('task', item, { completed: check.checked }, check));
      const content = element('div', 'st-task-content');
      const label = element('label', '', item.title);
      label.htmlFor = check.id;
      content.append(label, dateBadge(item.due_date, !item.completed, 'Due'));
      const actions = element('div', 'st-task-buttons');
      const edit = button('✎', () => openTask(item), 'st-icon-button');
      edit.setAttribute('aria-label', `Edit task: ${item.title}`);
      edit.title = 'Edit task';
      const remove = button('×', () => removeItem('task', item), 'st-icon-button');
      remove.setAttribute('aria-label', `Remove task: ${item.title}`);
      remove.title = 'Remove task';
      edit.disabled = remove.disabled = check.disabled;
      actions.append(edit, remove);
      row.append(check, content, actions);
      list.append(row);
    });
  }

  function renderPlanner() {
    renderSummary();
    renderApplications();
    renderTasks();
  }

  function loadPlanner() {
    if (state.plannerRead) return state.plannerRead;
    const version = state.version;
    byId('plannerApplications').setAttribute('aria-busy', 'true');
    byId('plannerTasks').setAttribute('aria-busy', 'true');
    byId('plannerRefresh').disabled = true;
    notice('plannerNotice', state.plannerLoaded ? 'Refreshing your planner…' : 'Loading your private planner…');
    if (!state.plannerLoaded) {
      byId('plannerApplications').replaceChildren(emptyState('Loading applications', 'Your saved records will appear here.'));
      byId('plannerTasks').replaceChildren(emptyState('Loading study tasks', 'Getting your latest tasks.'));
    }
    let repeat = false;
    const request = readJSON('/api/user/planner').then(data => {
      if (!Array.isArray(data.applications) || !Array.isArray(data.tasks)) throw new Error('Your planner returned an unexpected response. Please retry.');
      if (state.version !== version) { repeat = true; return; }
      state.applications = data.applications.filter(item => item && validId(item.id));
      state.tasks = data.tasks.filter(item => item && validId(item.id));
      state.plannerLoaded = true;
      sortItems();
      renderPlanner();
      notice('plannerNotice', '');
    }).catch(error => {
      notice('plannerNotice', error.message, true, loadPlanner);
      if (!state.plannerLoaded) {
        byId('plannerApplications').replaceChildren(emptyState('Applications unavailable', 'Your saved data could not be loaded. Use Refresh to retry.'));
        byId('plannerTasks').replaceChildren(emptyState('Tasks unavailable', 'Your saved data could not be loaded. Use Refresh to retry.'));
      }
    }).finally(() => {
      state.plannerRead = null;
      byId('plannerRefresh').disabled = false;
      byId('plannerApplications').setAttribute('aria-busy', 'false');
      byId('plannerTasks').setAttribute('aria-busy', 'false');
      if (repeat) loadPlanner();
    });
    state.plannerRead = request;
    return request;
  }

  function lockForm(form, busy) {
    form.dataset.busy = busy ? 'true' : 'false';
    form.setAttribute('aria-busy', String(busy));
    form.querySelectorAll('input, select, textarea, button').forEach(control => { control.disabled = busy; });
    const submit = form.querySelector('[type="submit"]');
    if (busy) { submit.dataset.label = submit.textContent; submit.textContent = 'Saving…'; }
    else if (submit.dataset.label) submit.textContent = submit.dataset.label;
  }

  function openApplication(item) {
    if (item && state.locks.has(`application-${item.id}`)) return;
    const form = byId('applicationForm');
    form.reset();
    lockForm(form, false);
    formError('applicationFormError', '');
    form.elements.namedItem('id').value = item ? item.id : '';
    ['title', 'company', 'registration_url', 'deadline', 'notes'].forEach(name => {
      form.elements.namedItem(name).value = item && item[name] ? item[name] : '';
    });
    form.elements.namedItem('registration_url').setCustomValidity('');
    form.elements.namedItem('status').value = item ? item.status : 'saved';
    form.querySelectorAll('[name="checklist"]').forEach(check => {
      check.checked = Boolean(item && Array.isArray(item.checklist) && item.checklist.includes(check.value));
    });
    byId('applicationDialogTitle').textContent = item ? 'Edit application' : 'Add application';
    byId('applicationDialog').showModal();
    form.elements.namedItem('title').focus();
  }

  function openTask(item) {
    if (item && state.locks.has(`task-${item.id}`)) return;
    const form = byId('taskForm');
    form.reset();
    lockForm(form, false);
    formError('taskFormError', '');
    form.elements.namedItem('id').value = item ? item.id : '';
    form.elements.namedItem('title').value = item ? item.title : '';
    form.elements.namedItem('due_date').value = item && item.due_date ? item.due_date : '';
    form.elements.namedItem('completed').checked = Boolean(item && item.completed);
    byId('taskDialogTitle').textContent = item ? 'Edit study task' : 'Add study task';
    byId('taskDialog').showModal();
    form.elements.namedItem('title').focus();
  }

  async function saveForm(event, kind) {
    event.preventDefault();
    const form = event.currentTarget;
    if (form.dataset.busy === 'true') return;
    const field = name => form.elements.namedItem(name);
    if (kind === 'application') {
      const link = field('registration_url').value.trim();
      field('registration_url').setCustomValidity(link && !safeLink(link) ? 'Use a complete http:// or https:// website link without login details.' : '');
    }
    if (!form.reportValidity()) return;
    const id = Number(field('id').value);
    const lock = `${kind}-${id || 'new'}`;
    if (state.locks.has(lock)) return;
    const data = { title: field('title').value.trim() };
    if (kind === 'application') {
      ['company', 'registration_url', 'notes', 'status'].forEach(name => { data[name] = field(name).value.trim(); });
      data.deadline = field('deadline').value || null;
      data.checklist = Array.from(form.querySelectorAll('[name="checklist"]:checked'), check => check.value);
    } else {
      data.due_date = field('due_date').value || null;
      data.completed = field('completed').checked;
    }
    formError(`${kind}FormError`, '');
    state.locks.add(lock);
    lockForm(form, true);
    try {
      const collection = kind === 'application' ? 'applications' : 'tasks';
      const result = await writeJSON(`/api/user/planner/${collection}${id ? '/' + id : ''}`, id ? 'PATCH' : 'POST', data);
      state.locks.delete(lock);
      remember(kind, result.item);
      byId(`${kind}Dialog`).close();
      notice('plannerNotice', kind === 'application' ? 'Application saved. Tracking does not submit an application to the provider.' : 'Study task saved.');
      if (!state.plannerLoaded) loadPlanner();
    } catch (error) {
      formError(`${kind}FormError`, error.message);
    } finally {
      state.locks.delete(lock);
      lockForm(form, false);
    }
  }

  async function updateQuick(kind, item, data, control) {
    const lock = `${kind}-${item.id}`;
    if (state.locks.has(lock)) return;
    state.locks.add(lock);
    control.disabled = true;
    try {
      const collection = kind === 'application' ? 'applications' : 'tasks';
      const result = await writeJSON(`/api/user/planner/${collection}/${item.id}`, 'PATCH', data);
      state.locks.delete(lock);
      remember(kind, result.item);
      notice('plannerNotice', kind === 'application' ? 'Application status updated.' : (result.item.completed ? 'Study task marked complete.' : 'Study task reopened.'));
    } catch (error) {
      if (kind === 'application') control.value = item.status;
      else control.checked = Boolean(item.completed);
      notice('plannerNotice', error.message, true, loadPlanner);
    } finally {
      state.locks.delete(lock);
      control.disabled = false;
    }
  }

  async function removeItem(kind, item) {
    const lock = `${kind}-${item.id}`;
    if (state.locks.has(lock)) return;
    const message = `Remove “${item.title}” from your planner?` + (kind === 'application' ? ' This only removes your private record; it does not withdraw an application with the provider.' : ' This removes this study task.');
    if (!window.confirm(message)) return;
    state.locks.add(lock);
    renderPlanner();
    try {
      const collection = kind === 'application' ? 'applications' : 'tasks';
      await writeJSON(`/api/user/planner/${collection}/${item.id}`, 'DELETE');
      state[collection] = state[collection].filter(existing => existing.id !== item.id);
      if (kind === 'application' && state.programData) {
        state.programData.items.forEach(program => {
          if (program.application_id === item.id) program.application_id = null;
        });
        renderPrograms();
      }
      notice('plannerNotice', kind === 'application' ? 'Application record removed from your planner.' : 'Study task removed.');
    } catch (error) {
      notice('plannerNotice', error.message, true, loadPlanner);
    } finally {
      state.locks.delete(lock);
      renderPlanner();
    }
  }

  function selectedFilters() {
    const form = byId('opportunityFilters');
    return Object.fromEntries(['q', 'category', 'company', 'within', 'sort'].map(name => [name, form.elements.namedItem(name).value.trim()]));
  }

  function fillFilter(name, values, placeholder) {
    const select = byId('opportunityFilters').elements.namedItem(name);
    const selected = state.programFilters[name];
    const options = Array.isArray(values) ? values.filter(value => typeof value === 'string') : [];
    select.replaceChildren();
    const first = element('option', '', placeholder);
    first.value = '';
    first.defaultSelected = true;
    select.append(first);
    if (selected && !options.includes(selected)) options.unshift(selected);
    options.forEach(value => {
      const option = element('option', '', value);
      option.value = value;
      select.append(option);
    });
    select.value = selected;
  }

  function programBusy(busy) {
    byId('programsList').setAttribute('aria-busy', String(busy));
    byId('opportunityFilters').querySelectorAll('button').forEach(control => { control.disabled = busy; });
    byId('opportunityPrev').disabled = busy || state.programPage <= 1;
    const pages = state.programData ? Math.max(1, Math.ceil(state.programData.total / state.programData.page_size)) : 1;
    byId('opportunityNext').disabled = busy || state.programPage >= pages;
  }

  function renderPrograms() {
    const data = state.programData;
    if (!data) return;
    const list = byId('programsList');
    list.replaceChildren();
    if (!data.items.length) list.append(emptyState('No matching opportunities right now',
      'Try a broader keyword or clear your filters. You can also track a program you found elsewhere in My Planner.',
      'Clear filters', resetFilters));
    data.items.forEach(program => {
      const card = element('article', 'st-opportunity');
      const tags = element('div', 'st-tags');
      tags.append(element('span', 'st-tag', program.category || 'Student program'));
      tags.append(dateBadge(program.deadline, true));
      card.append(tags, element('h3', '', program.title || 'Student program'));
      if (program.company) card.append(element('p', 'st-organization', program.company));
      const description = String(program.description || 'Check the provider website for the program details, eligibility and latest deadline.');
      card.append(element('p', 'st-description', description.slice(0, 400) + (description.length > 400 ? '…' : '')));
      if (description.length > 400) {
        const details = element('details');
        details.append(element('summary', '', 'Read full description'), element('p', 'st-description', description));
        card.append(details);
      }
      const actions = element('div', 'st-actions');
      const link = providerLink(program.registration_url);
      if (link) actions.append(link);
      else card.append(element('p', 'st-footnote', 'No verified provider link is available in this record. Confirm the source before sharing any personal information.'));
      if (validId(program.id)) {
        const tracked = validId(program.application_id);
        const track = button(state.tracking.has(program.id) ? 'Saving…' : tracked ? 'Open in My Planner' : 'Track application',
          () => tracked ? window.switchTab('planner') : trackProgram(program), 'st-button st-small st-primary');
        track.dataset.programId = String(program.id);
        track.disabled = state.tracking.has(program.id);
        actions.append(track);
      }
      card.append(actions);
      list.append(card);
    });
    const start = data.total ? (data.page - 1) * data.page_size + 1 : 0;
    const end = Math.min(data.page * data.page_size, data.total);
    byId('opportunityCount').textContent = data.total ? `${start}–${end} of ${data.total} active opportunities` : 'No matching active opportunities';
    const pages = Math.max(1, Math.ceil(data.total / data.page_size));
    byId('opportunityPage').textContent = `Page ${data.page} of ${pages}`;
    byId('opportunityPagination').hidden = pages <= 1;
    programBusy(Boolean(state.programRead));
  }

  function loadPrograms(page) {
    if (state.programRead) return state.programRead;
    if (!state.programFilters) state.programFilters = selectedFilters();
    state.programPage = Number.isInteger(page) && page > 0 ? page : state.programPage;
    const params = new URLSearchParams(state.programFilters);
    params.set('page', String(state.programPage));
    programBusy(true);
    byId('opportunityCount').textContent = 'Loading opportunities…';
    notice('opportunityNotice', '');
    if (!state.programData) byId('programsList').replaceChildren(emptyState('Loading opportunities', 'Finding the latest active programs.'));
    const request = readJSON('/api/user/opportunities?' + params).then(async data => {
      if (!Array.isArray(data.items) || !Number.isInteger(data.total) || !Number.isInteger(data.page_size) || data.page_size <= 0) {
        throw new Error('The program list returned an unexpected response. Please retry.');
      }
      const lastPage = Math.max(1, Math.ceil(data.total / data.page_size));
      if (state.programPage > lastPage) {
        params.set('page', String(lastPage));
        data = await readJSON('/api/user/opportunities?' + params);
      }
      state.programData = data;
      state.programPage = data.page;
      fillFilter('category', data.categories, 'All categories');
      fillFilter('company', data.companies, 'All organizations');
      renderPrograms();
    }).catch(error => {
      byId('opportunityCount').textContent = state.programData ? 'Could not refresh · previously loaded results shown' : 'Opportunities unavailable';
      notice('opportunityNotice', error.message, true, () => loadPrograms());
      if (!state.programData) byId('programsList').replaceChildren(emptyState('Programs could not be loaded', 'Your connection or the service may be temporarily unavailable. Use Refresh and retry above.'));
    }).finally(() => {
      state.programRead = null;
      programBusy(false);
    });
    state.programRead = request;
    return request;
  }

  function resetFilters() {
    const form = byId('opportunityFilters');
    ['q', 'category', 'company', 'within'].forEach(name => { form.elements.namedItem(name).value = ''; });
    form.elements.namedItem('sort').value = 'deadline';
    state.programFilters = selectedFilters();
    loadPrograms(1);
  }

  async function trackProgram(program) {
    if (!validId(program.id) || state.tracking.has(program.id)) return;
    state.tracking.add(program.id);
    renderPrograms();
    try {
      const result = await writeJSON('/api/user/planner/applications', 'POST', { program_id: program.id });
      program.application_id = result.item.id;
      // The current page can have refreshed while the write was in flight.
      if (state.programData) state.programData.items.forEach(item => {
        if (item.id === program.id) item.application_id = result.item.id;
      });
      remember('application', result.item);
      notice('opportunityNotice', 'Added to My Planner. This saves your preparation record; it does not apply to the program.');
    } catch (error) {
      notice('opportunityNotice', error.message, true, () => loadPrograms());
    } finally {
      state.tracking.delete(program.id);
      renderPrograms();
      const control = byId('programsList').querySelector(`[data-program-id="${program.id}"]`);
      if (control && !byId('tab-programs').classList.contains('hidden')) control.focus();
    }
  }

  async function downloadCalendar() {
    const control = byId('plannerCalendar');
    if (control.disabled) return;
    control.disabled = true;
    try {
      const response = await fetchResponse('/api/user/planner/calendar.ics');
      const content = await response.text();
      if (!content.startsWith('BEGIN:VCALENDAR') || !response.headers.get('Content-Type')?.includes('text/calendar')) {
        throw new Error('The calendar file could not be prepared. Please refresh and try again.');
      }
      const url = URL.createObjectURL(new Blob([content], { type: 'text/calendar;charset=utf-8' }));
      const link = element('a');
      link.href = url;
      link.download = 'novabrief-student-planner.ics';
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 10000);
      notice('plannerNotice', content.includes('BEGIN:VEVENT') ?
        'Your calendar file is ready. Import it into your calendar. Future planner edits do not sync automatically.' :
        'Your calendar file has no upcoming events yet. Add dates to saved or preparing applications or unfinished tasks, then download again.');
    } catch (error) {
      notice('plannerNotice', error.message, true, downloadCalendar);
    } finally {
      control.disabled = false;
    }
  }

  function initialize() {
    byId('plannerAddApplication').addEventListener('click', () => openApplication());
    byId('plannerAddTask').addEventListener('click', () => openTask());
    byId('plannerRefresh').addEventListener('click', loadPlanner);
    byId('plannerCalendar').addEventListener('click', downloadCalendar);
    byId('applicationStatusFilter').addEventListener('change', renderApplications);
    byId('showCompletedTasks').addEventListener('change', renderTasks);
    byId('applicationForm').addEventListener('submit', event => saveForm(event, 'application'));
    byId('taskForm').addEventListener('submit', event => saveForm(event, 'task'));
    byId('applicationForm').elements.namedItem('registration_url').addEventListener('input', event => event.target.setCustomValidity(''));
    document.querySelectorAll('[data-close-dialog]').forEach(control => {
      control.addEventListener('click', () => byId(control.dataset.closeDialog).close());
    });
    ['applicationDialog', 'taskDialog'].forEach(id => {
      byId(id).addEventListener('cancel', event => {
        if (byId(id).querySelector('form').dataset.busy === 'true') event.preventDefault();
      });
    });
    byId('opportunityFilters').addEventListener('submit', event => {
      event.preventDefault();
      if (state.programRead) return;
      state.programFilters = selectedFilters();
      loadPrograms(1);
    });
    byId('opportunityFilters').addEventListener('reset', event => {
      event.preventDefault();
      if (!state.programRead) resetFilters();
    });
    byId('opportunityPrev').addEventListener('click', () => loadPrograms(state.programPage - 1));
    byId('opportunityNext').addEventListener('click', () => loadPrograms(state.programPage + 1));
  }

  function renderOverviewPrograms(programs) {
    const list = byId('overviewPrograms');
    list.classList.add('student-tools');
    list.replaceChildren();
    if (!programs.length) {
      list.append(emptyState('No active opportunities yet', 'You can still add an opportunity you found elsewhere to your private planner.',
        'Open My Planner', () => window.switchTab('planner')));
      return;
    }
    programs.forEach(program => {
      const card = element('article', 'st-application');
      card.append(element('h4', '', program.title || 'Student program'));
      if (program.company) card.append(element('p', 'st-organization', program.company));
      card.append(dateBadge(program.deadline, true));
      const actions = element('div', 'st-actions');
      const link = providerLink(program.registration_url);
      if (link) actions.append(link);
      actions.append(button('Explore & track', () => window.switchTab('programs')));
      card.append(actions);
      list.append(card);
    });
  }

  window.StudentTools = Object.freeze({ loadPrograms, loadPlanner, renderOverviewPrograms });
  initialize();
}());
