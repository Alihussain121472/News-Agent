/* Nova Brief Python hub. Answers and grades are always owned by the server. */
(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const main = $('#main');
  let data, state, view = 'practice', selectedModule = '', selectedType = 'all', current = null;
  let editor = null, draftTimer, saveChain = Promise.resolve(), dirty = false, revision = 0;
  let activeJob = null, pollTimer, timer, examContext = false, serverOffset = 0, finishing = false;
  const saveTasks = new Map();
  let quizContext = null;
  function queueSave(key, task) {
    const entry = {task}; saveTasks.set(key, entry);
    saveChain = saveChain.catch(()=>{}).then(task).then(()=>{
      if(saveTasks.get(key)===entry)saveTasks.delete(key);
    }).catch(error=>{entry.error=error;throw error;});
    saveChain.catch(()=>{});
    return saveChain;
  }
  async function waitForSaves() {
    await saveChain.catch(()=>{});
    if(saveTasks.size)throw new Error('Some answers have not saved. Use Retry save before continuing.');
  }
  async function retrySaves() {
    for(const [key,entry] of [...saveTasks])queueSave(key,entry.task).catch(()=>{});
    try{await flushDraft();await waitForSaves();notice('All changes saved.');}catch(e){notice(e.message);}
  }
  const names = {practice:'Python Practice Hub',quiz:'Quiz Center',puzzle:'Python Puzzles',exam:'Grand Test',progress:'My Progress'};
  const badge = difficulty => `<span class="badge ${difficulty.toLowerCase()}">${escape(difficulty)}</span>`;
  const moduleOf = id => data.modules.find(m => m.id === id);
  const exerciseOf = id => data.exercises.find(e => e.id === id);
  const completed = e => !!state.completed[e.id];
  const moduleProgress = id => {
    const items = data.exercises.filter(e => e.module === id);
    return {done:items.filter(completed).length,total:items.length};
  };
  function notice(message) { const n = $('#notice'); n.textContent = message; n.hidden = false; clearTimeout(n._timer); n._timer = setTimeout(() => n.hidden = true, 6500); }
  async function api(path, body) {
    const response = await fetch('/api/python/' + path, {
      method:body === undefined ? 'GET' : 'POST', credentials:'same-origin',
      headers:body === undefined ? {} : {'Content-Type':'application/json','X-CSRF-Token':data?.csrf || ''},
      body:body === undefined ? undefined : JSON.stringify(body)
    });
    let result;
    try { result = await response.json(); } catch (_) { throw new Error('The server could not respond. Please retry.'); }
    if (!response.ok) throw new Error(result.message || 'Something went wrong. Please retry.');
    return result;
  }
  async function refresh() { data = await api('bootstrap'); state = data.state; serverOffset = data.server_time * 1000 - Date.now(); }
  function show(html) { main.innerHTML = html; main.classList.remove('animate-in'); void main.offsetWidth; main.classList.add('animate-in'); }
  function heading(title, text, label = 'YOUR PYTHON JOURNEY') { return `<div class="heading-copy"><span class="eyebrow">${label}</span><h1>${title}</h1><p>${text}</p></div>`; }
  function stats() {
    const done = data.exercises.filter(completed).length;
    const mastered = data.modules.filter(m => {const p=moduleProgress(m.id);return p.done===p.total;}).length;
    const scores = state.quiz_results;
    const average = scores.length ? Math.round(100*scores.reduce((n,q)=>n+q.score/q.total,0)/scores.length)+'%' : '—';
    return `<div class="stats">${[['✓',done,'Exercises completed'],['▦',`${mastered} / 10`,'Modules completed'],['◎',average,'Average quiz score'],['↗',`${Math.round(100*done/data.exercises.length)}%`,'Overall progress']].map(([icon,n,label])=>`<div class="stat"><span class="stat-icon">${icon}</span><div><strong>${n}</strong><small>${label}</small></div></div>`).join('')}</div>`;
  }
  async function navigate(next) {
    if (activeJob && !finishing) { notice('Stop your running program before leaving the workspace.'); return; }
    try { await flushDraft(); await waitForSaves(); } catch (e) { notice(e.message); return; }
    current = null; editor = null; examContext = false; quizContext = null;
    view = next;
    $$('.sidebar [data-view], .mobile-nav [data-view]').forEach(b => b.classList.toggle('active', b.dataset.view===view));
    $('#breadcrumb').textContent = names[view];
    history.replaceState(null,'',`#${view}`);
    if (view==='practice'||view==='puzzle') renderLibrary();
    if (view==='quiz') renderQuizzes();
    if (view==='exam') renderExam();
    if (view==='progress') renderProgress();
    if(state.active_exam?.status==='active')startTimer();
  }
  function renderLibrary() {
    const puzzle = view==='puzzle';
    show(puzzle ? heading('A little stuck? That’s the point.','Find the bug, fill the gap, or untangle the logic. Ten small challenges that build a stronger mental model.','PYTHON PUZZLES') :
      `<section class="hero"><div class="hero-copy"><span class="eyebrow">LEARN IT. WRITE IT. MAKE IT YOURS.</span><h1>Small steps.<br><em>Real Python.</em></h1><p>Turn what you learn into what you can build. Your next breakthrough starts with a few lines of code.</p><div class="hero-actions"><button class="primary" id="continue">Continue learning <span aria-hidden="true">→</span></button><small>YOUR PACE. YOUR PROGRESS.</small></div></div><div class="hero-art" aria-hidden="true"><div class="code-card"><div class="code-dots"><i></i><i></i><i></i></div><span class="comment"># Every expert starts here</span><br><span class="accent">def</span> grow(skills):<br>&nbsp; <span class="accent">for</span> day <span class="accent">in</span> practice:<br>&nbsp; &nbsp; skills += 1<br>&nbsp; <span class="accent">return</span> possibilities<br><br>grow(<span class="accent">you</span>)</div><div class="code-float">✓ &nbsp; A little better, every day</div></div></section>${stats()}`);
    main.insertAdjacentHTML('beforeend', `<section><div class="section-heading"><div><h2>${puzzle?'Find your challenge':'Your learning path'}</h2><p>${puzzle?'One puzzle for every chapter.':'Follow the course, or jump into a topic that sparks your curiosity.'}</p></div><small>10 thoughtfully connected modules</small></div><div class="module-strip">${data.modules.map(m=>{const p=moduleProgress(m.id);return `<button class="module-card ${selectedModule===m.id?'selected':''}" data-module="${m.id}" aria-pressed="${selectedModule===m.id}"><span class="module-number">CHAPTER ${String(+m.id+1).padStart(2,'0')}<span>${p.done===p.total?'✓':'↗'}</span></span><strong>${escape(m.title)}</strong><small>${p.done} of ${p.total} completed</small><span class="mini-progress"><span style="width:${100*p.done/p.total}%"></span></span></button>`;}).join('')}</div></section>
      <div class="section-heading"><div><h2>${puzzle?'The puzzle collection':'Put your knowledge to work'}</h2><p id="module-description">${selectedModule?escape(moduleOf(selectedModule).description):'Build confidence with every problem you solve.'}</p></div><button class="text-button" id="all-topics">All topics ↗</button></div>
      ${puzzle?'':`<div class="mode-tabs" aria-label="Exercise type">${[['all','All exercises'],['project','Mini projects'],['unfinished','To work on'],['completed','Completed']].map(([id,label])=>`<button data-type="${id}" class="${selectedType===id?'selected':''}" aria-pressed="${selectedType===id}">${label}</button>`).join('')}</div>`}
      <div class="filters"><label class="search"><span class="sr-only">Search exercises</span><input id="search" type="search" placeholder="Search exercises, topics, or a skill…"></label><label><span class="sr-only">Difficulty</span><select id="difficulty"><option value="">All difficulties</option><option>Beginner</option><option>Developing</option><option>Challenging</option></select></label><label><span class="sr-only">Topic</span><select id="topic"><option value="">All topics</option>${data.modules.map(m=>`<option value="${m.id}" ${selectedModule===m.id?'selected':''}>${escape(m.title)}</option>`).join('')}</select></label></div><div id="exercise-results" aria-live="polite"></div>`);
    $('#continue')?.addEventListener('click',()=>openExercise(state.last_exercise||'welcome'));
    $$('[data-module]',main).forEach(b=>b.onclick=()=>{selectedModule=selectedModule===b.dataset.module?'':b.dataset.module;renderLibrary();});
    $$('[data-type]',main).forEach(b=>b.onclick=()=>{selectedType=b.dataset.type;renderLibrary();});
    $('#all-topics').onclick=()=>{selectedModule='';renderLibrary();};
    $('#search').oninput = filterExercises;
    $('#difficulty').onchange=filterExercises;
    $('#topic').onchange=e=>{selectedModule=e.target.value;$$('[data-module]',main).forEach(b=>b.classList.toggle('selected',b.dataset.module===selectedModule));filterExercises();};
    filterExercises();
  }
  function filterExercises() {
    const q=$('#search').value.trim().toLowerCase(), diff=$('#difficulty').value;
    const items=data.exercises.filter(e=>e.mode===(view==='puzzle'?'puzzle':'practice')&&(!selectedModule||e.module===selectedModule)&&(!diff||e.difficulty===diff)&&(!q||[e.title,...e.topics,moduleOf(e.module).title].join(' ').toLowerCase().includes(q))&&(view==='puzzle'||selectedType==='all'||(selectedType==='project'&&e.project)||(selectedType==='completed'&&completed(e))||(selectedType==='unfinished'&&!completed(e))));
    $('#exercise-results').innerHTML=`<div class="exercise-list"><div class="list-header"><span></span><span>EXERCISE · ${items.length} FOUND</span><span>DIFFICULTY</span><span>FORMAT</span><span></span></div>${items.map(e=>`<div class="exercise-row"><span class="exercise-status ${completed(e)?'done':''}" aria-label="${completed(e)?'Completed':'Not completed'}">${completed(e)?'✓':'○'}</span><button class="open-exercise" data-exercise="${e.id}"><strong>${escape(e.title)}</strong><small>${escape(moduleOf(e.module).title)} · ${escape(e.topics.slice(0,3).join(' · '))}</small></button>${badge(e.difficulty)}<span class="row-type">${e.project?'Mini project':e.mode==='puzzle'?escape(e.topics[0]):'Practice'}</span><button class="arrow-button" data-exercise="${e.id}" aria-label="Open ${escape(e.title)}">→</button></div>`).join('')||'<div class="empty">No exercises match. Try another topic or search term.</div>'}</div>`;
    $$('[data-exercise]',main).forEach(b=>b.onclick=()=>openExercise(b.dataset.exercise));
  }
  function getCode(){return editor?editor.getValue():$('#code')?.value||'';}
  function setSaveLabel(message){const label=$('#save-status');if(label)label.textContent=message;}
  function changed(){dirty=true;revision++;setSaveLabel('Saving…');clearTimeout(draftTimer);draftTimer=setTimeout(()=>flushDraft().catch(e=>notice(e.message)),650);}
  function flushDraft(){
    clearTimeout(draftTimer);
    if(!current||!dirty)return saveChain;
    const id=current.id, code=getCode(), stdin=$('#stdin')?.value||'', rev=revision;
    let argv;try{argv=JSON.parse($('#argv').value);}catch(_){return Promise.reject(new Error('Command-line arguments must be a JSON array.'));}
    const exam=examContext?state.active_exam?.id:null;
    const task=async()=>{
      if(exam){await api('exam/answer',{exam,id,answer:code,stdin,argv});if(state.active_exam?.id===exam){state.active_exam.answers[id]=code;(state.active_exam.inputs??={})[id]={stdin,argv};}}
      else{await api('draft/'+id,{code,stdin,argv});state.drafts[id]={code,stdin,argv};state.last_exercise=id;}
      if(current?.id===id&&revision===rev){dirty=false;setSaveLabel('All changes saved');}
    };
    return queueSave('code:'+id,task).catch(e=>{setSaveLabel('Not saved · use Retry save');throw e;});
  }
  async function openExercise(id,inExam=false){
    if(activeJob){notice('Stop the running program first.');return;}
    try{await flushDraft();await waitForSaves();}catch(e){notice(e.message);return;}
    const e=exerciseOf(id);if(!e){notice('Exercise not found.');return;}
    current=e;examContext=inExam;dirty=false;revision++;clearInterval(timer);
    const saved=inExam?{code:state.active_exam.answers[id],...state.active_exam.inputs?.[id]}:state.drafts[id];
    show(`<div class="workspace-top"><div><button class="text-button" id="back">← ${inExam?'Back to Grand Test':view==='puzzle'?'All puzzles':'All exercises'}</button><h2>${escape(e.title)}</h2></div><div>${inExam?'<span class="exam-timer" id="countdown"></span>':'<small>One focused step forward.</small>'}</div></div><div class="mobile-workspace-tabs" role="tablist" aria-label="Workspace panels"><button class="active" data-pane="question" role="tab" aria-selected="true">Question</button><button data-pane="code" role="tab" aria-selected="false">Code</button><button data-pane="results" role="tab" aria-selected="false">Results</button></div><div class="workspace" data-pane="question"><section class="question-panel" aria-label="Problem description">${badge(e.difficulty)}<h2>${escape(e.title)}</h2><p>${escape(e.problem)}</p><div class="lesson">${escape(e.lesson)}</div><h3>Input & output</h3><p class="muted">${escape(e.io)}</p>${e.examples.map(ex=>`<div class="example"><span class="example-label">Example input</span><pre>${escape(ex.input)||'(No standard input)'}</pre><span class="example-label">Expected output</span><pre>${escape(ex.output)||'(Empty output)'}</pre></div>`).join('')}${Object.keys(e.files).length?`<h3>Exercise files</h3>${Object.entries(e.files).map(([name,content])=>`<details><summary>${escape(name)}</summary><pre>${escape(content)}</pre></details>`).join('')}`:''}${inExam?'':`<details><summary>A nudge in the right direction</summary><ol class="hint-list">${e.hints.map(h=>`<li>${escape(h)}</li>`).join('')}</ol></details><button class="text-button" id="reveal">Reveal explained solution</button><div id="solution"></div>`}<h3>Keep exploring</h3><a href="${moduleOf(e.module).notes}" target="_blank" rel="noopener">Read official chapter notes ↗</a><br><a href="${moduleOf(e.module).video}" target="_blank" rel="noopener">Watch the full course ↗</a></section><section class="editor-panel" aria-label="Python editor"><div class="editor-bar"><strong>▧ &nbsp; main.py</strong><span id="save-status" class="save-label" role="status">All changes saved</span></div><textarea id="code" aria-label="Python code editor" spellcheck="false"></textarea><div class="editor-controls"><button id="run" class="secondary">▷ Run</button><button id="stop" class="danger" disabled>□ Stop</button><button id="submit" class="primary">${inExam?'Save answer':'Submit solution'} →</button><button id="reset">↺ Reset</button></div><div class="input-area"><label for="stdin">STANDARD INPUT · ONE VALUE PER LINE</label><textarea id="stdin" rows="2" placeholder="Values for input()"></textarea><label for="argv">COMMAND-LINE ARGUMENTS · JSON ARRAY</label><input id="argv" value="${escape(JSON.stringify(e.argv))}" aria-label="Command-line arguments"></div><section class="results-panel" aria-label="Execution results" aria-live="polite"><h3>Output & tests</h3><div id="output"><p class="muted">Run your code to explore. ${inExam?'Save your answer for final grading.':'Submit when you’re ready for all test cases.'}</p><small class="muted">10 sec · 128 MiB · 16 KiB output · Ctrl/⌘ + Enter to run</small></div></section></section></div>`);
    $('#code').value=saved?.code??e.starter;
    $('#stdin').value=saved?.stdin??e.examples[0]?.input??'';
    $('#argv').value=JSON.stringify(saved?.argv??e.argv);
    $('#save-status').insertAdjacentHTML('afterend','<button class="text-button" id="retry-save">Retry save</button>');
    $('#retry-save').onclick=retrySaves;
    if(window.CodeMirror){editor=CodeMirror.fromTextArea($('#code'),{mode:'python',lineNumbers:true,indentUnit:4,tabSize:4,indentWithTabs:false,lineWrapping:true,viewportMargin:20,extraKeys:{'Ctrl-Enter':()=>run('run'),'Cmd-Enter':()=>run('run'),Tab:cm=>cm.somethingSelected()?cm.indentSelection('add'):cm.replaceSelection('    '),Esc:cm=>cm.getInputField().blur()}});editor.on('change',changed);editor.getInputField().setAttribute('aria-label','Python code editor');}
    else{$('#code').oninput=changed;$('#code').onkeydown=event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();run('run');}};}
    $('#stdin').oninput=changed;$('#argv').oninput=changed;
    $('#run').onclick=()=>run('run');$('#submit').onclick=()=>{if(inExam){changed();flushDraft().then(()=>notice('Answer saved for final grading.')).catch(e=>notice(e.message));}else run('submit');};
    $('#stop').onclick=async()=>{if(activeJob){try{await api(`jobs/${activeJob}/stop`,{});notice('Stopping your program…');}catch(e){notice(e.message);}}};
    $('#reset').onclick=()=>{if(!confirm('Replace this draft with the starter code?'))return;if(editor)editor.setValue(e.starter);else{$('#code').value=e.starter;changed();}};
    $('#back').onclick=()=>navigate(inExam?'exam':view==='puzzle'?'puzzle':'practice');
    $('#reveal')?.addEventListener('click',async()=>{if(!confirm('Reveal the reference solution and explanation? Try a hint first if you want another attempt.'))return;try{const solution=await api('solution/'+id,{});$('#solution').innerHTML=`<div class="lesson"><strong>One possible solution</strong><pre>${escape(solution.code)}</pre><p>${escape(solution.explanation)}</p></div>`;}catch(error){notice(error.message);}});
    $$('[data-pane]',main).filter(b=>b.tagName==='BUTTON').forEach(b=>b.onclick=()=>setPane(b.dataset.pane));
    if(state.active_exam?.status==='active')startTimer();
    history.replaceState(null,'',`#${inExam?'exam-code':'exercise'}/${id}`);
  }
  function setPane(pane){$('.workspace').dataset.pane=pane;$$('button[data-pane]').forEach(b=>{b.classList.toggle('active',b.dataset.pane===pane);b.setAttribute('aria-selected',b.dataset.pane===pane);});if(pane==='code')setTimeout(()=>editor?.refresh(),0);}
  function busy(value){['run','submit','reset'].forEach(id=>{if($('#'+id))$('#'+id).disabled=value;});if($('#stop'))$('#stop').disabled=!value;}
  async function run(kind){
    if(activeJob)return;
    try{
      await flushDraft();await waitForSaves();
      let argv;try{argv=JSON.parse($('#argv').value);}catch(_){throw new Error('Command-line arguments must be a JSON array, such as ["--count", "3", "hi"].');}
      busy(true);$('#output').innerHTML='<p class="muted"><span class="loader"></span> Starting Python…</p>';setPane('results');
      const job=await api('jobs',{kind,exercise:current.id,code:getCode(),stdin:$('#stdin').value,argv,exam:examContext?state.active_exam.id:null});
      sessionStorage.setItem('python-active-job',JSON.stringify({id:job.id,exercise:current.id,exam:examContext}));
      activeJob=job.id;pollJob(job.id,false);
    }catch(e){busy(false);$('#output').innerHTML=`<div class="result-banner error">${escape(e.message)}</div>`;}
  }
  async function pollJob(id,isExam){
    clearTimeout(pollTimer);
    try{
      const job=await api('jobs/'+id);
      if(job.status==='running'){pollTimer=setTimeout(()=>pollJob(id,isExam),450);return;}
      activeJob=null;busy(false);
      sessionStorage.removeItem('python-active-job');
      if(job.status==='error')throw new Error(job.message);
      if(isExam){finishing=false;await refresh();renderExam();return;}
      renderOutput(job.result||{status:job.status});
      if(job.result?.status==='passed'){notice('All tests passed. A new step in your Python journey!');await refresh();}
    }catch(e){
      activeJob=null;finishing=false;busy(false);notice(e.message);
      if(isExam){
        await refresh().catch(()=>{});
        if(!state.active_exam){renderExam();return;}
        show(heading('Your answers are safe.','Grading was interrupted. Retry to finish reviewing your saved assessment.','GRAND TEST')+`<div class="card"><p>${escape(e.message)}</p><button id="retry-grading" class="primary">Retry grading →</button></div>`);
        $('#retry-grading').onclick=()=>finishExam(true);
      }else if($('#output')){
        $('#output').innerHTML=`<div class="result-banner error">${escape(e.message)}</div><button id="retry-status">Check execution status</button>`;
        $('#retry-status').onclick=()=>{activeJob=id;busy(true);pollJob(id,isExam);};
      }
    }
  }
  function renderOutput(result){
    const messages={ok:'Run complete',passed:'All tests passed — well done!',needs_work:'Not quite yet. Use the feedback below to refine your solution.',syntax_error:'Python could not parse your code. Check the line shown below.',runtime_error:'Your program encountered an error.',timeout:'Execution limit reached. Check for an infinite loop or reduce the work.',memory_limit:'Memory limit reached (128 MiB). Try using smaller data structures.',output_limit:'Output limit reached (16 KiB). Print less data.',stopped:'Execution stopped.'};
    $('#output').innerHTML=`<div class="result-banner ${['ok','passed'].includes(result.status)?'':'error'}">${escape(messages[result.status]||result.status)}</div>${result.duration_ms!==undefined?`<small class="muted">${result.duration_ms} ms</small>`:''}${result.stdout!==undefined?`<pre>${escape(result.stdout)||'(No output)'}</pre>`:''}${result.stderr?`<pre class="danger">${escape(result.stderr)}</pre>`:''}${(result.tests||[]).map(t=>`<div class="test-row ${t.passed?'':'failed'}"><strong>${t.passed?'✓':'×'} ${escape(t.name)}</strong> <span class="muted">${escape(t.status.replaceAll('_',' '))}</span>${!t.passed&&t.expected!==undefined?`<details><summary>Compare output</summary><div>Expected</div><pre>${escape(t.expected)||'(Empty)'}</pre><div>Your output</div><pre>${escape(t.actual)||'(Empty)'}</pre>${t.stderr?`<pre class="danger">${escape(t.stderr)}</pre>`:''}</details>`:''}</div>`).join('')}`;
    if(result.status==='passed'){
      $('#output').classList.add('success-pulse');
      const next=data.exercises.find(e=>e.mode===current.mode&&e.id!==current.id&&!completed(e)&&e.module===current.module)||data.exercises.find(e=>e.mode===current.mode&&e.id!==current.id&&!completed(e));
      if(next){$('#output').insertAdjacentHTML('beforeend',`<button id="next-exercise" class="primary">Next: ${escape(next.title)} →</button>`);$('#next-exercise').onclick=()=>openExercise(next.id);}
    }
  }
  function renderQuizzes(){
    quizContext=null;
    show(heading('Quiz Center','Check your understanding, review explanations, and retry the questions you missed.','CHAPTER CHECKPOINTS')+`<div class="card-grid">${data.modules.map(m=>{
      const scores=state.quiz_results.filter(q=>q.module===m.id),latest=scores.at(-1),draft=state.quiz_drafts[m.id];
      const best=scores.length?Math.max(...scores.map(q=>Math.round(100*q.score/q.total)))+'%':'Not attempted';
      return `<section class="card"><span class="eyebrow">CHAPTER ${+m.id+1}</span><h3>${escape(m.title)}</h3><p>3 questions · Explained answers</p><small class="muted">Best score: ${best}${draft?` · ${Object.keys(draft.answers).length}/${draft.questions.length} answers saved`:''}</small><div class="quiz-actions"><button data-quiz="${m.id}" class="secondary">${draft?'Resume':'Start'} quiz →</button>${latest?`<button data-quiz-review="${m.id}">Review last attempt</button>`:''}${latest?.score<latest?.total?`<button data-quiz-missed="${m.id}">Retry missed questions</button>`:''}</div></section>`;
    }).join('')}</div>`);
    $$('[data-quiz]',main).forEach(b=>b.onclick=()=>openQuiz(b.dataset.quiz));
    $$('[data-quiz-missed]',main).forEach(b=>b.onclick=()=>openQuiz(b.dataset.quizMissed,'missed'));
    $$('[data-quiz-review]',main).forEach(b=>b.onclick=()=>reviewQuiz(state.quiz_results.filter(q=>q.module===b.dataset.quizReview).at(-1)));
  }
  function quizQuestion(q,selected,disabled=false){return `<section class="quiz-question" id="question-${q.id}" data-question="${q.id}"><span class="eyebrow">${escape(q.kind)}</span><h3>${escape(q.question)}</h3><fieldset class="options"><legend class="sr-only">${escape(q.question)}</legend>${q.options.map((option,index)=>`<label class="option"><input type="radio" name="${q.id}" value="${index}" ${selected===index?'checked':''} ${disabled?'disabled':''}><span>${escape(option)}</span></label>`).join('')}</fieldset><div class="feedback"></div></section>`;}
  async function openQuiz(module,mode='resume'){
    try{
      await waitForSaves();
      const {draft}=await api('quiz/start',{module,mode});state.quiz_drafts[module]=draft;quizContext={module,draft};
      const questions=draft.questions.map(id=>data.quizzes.find(q=>q.id===id));
      show(`<div class="quiz-sheet"><button class="text-button" id="quiz-back">← All quizzes</button>${heading(escape(moduleOf(module).title),draft.mode==='missed'?'Retry missed questions. This attempt receives its own score.':'Choose one answer for every question. Your selections save automatically.','CHAPTER CHECKPOINT')}<div class="review-toolbar"><span id="quiz-save" role="status"></span><button id="quiz-retry-save">Retry save</button></div><form id="quiz-form">${questions.map(q=>quizQuestion(q,draft.answers[q.id])).join('')}<button class="primary" type="submit">Check my answers →</button></form></div>`);
      history.replaceState(null,'',`#quiz/${module}`);
      const savedLabel=()=>{if($('#quiz-save'))$('#quiz-save').textContent=`${Object.keys(draft.answers).length} / ${questions.length} answered · All changes saved`;};savedLabel();
      $('#quiz-back').onclick=()=>navigate('quiz');$('#quiz-retry-save').onclick=retrySaves;
      $$('input[type="radio"]',main).forEach(input=>input.onchange=()=>{
        draft.answers[input.name]=+input.value;const answers={...draft.answers};$('#quiz-save').textContent='Saving…';
        queueSave('quiz:'+module,async()=>{await api('quiz/draft',{module,attempt:draft.id,answers});if(quizContext?.draft===draft)savedLabel();}).catch(e=>{if($('#quiz-save'))$('#quiz-save').textContent='Not saved · use Retry save';notice(e.message);});
      });
      $('#quiz-form').onsubmit=async event=>{
        event.preventDefault();if(questions.some(q=>draft.answers[q.id]===undefined)){notice('Answer every question before submitting.');return;}
        const button=$('button[type="submit"]');button.disabled=true;
        try{await waitForSaves();const {result}=await api('quiz',{module,attempt:draft.id,answers:draft.answers});delete state.quiz_drafts[module];state.quiz_results.push(result);reviewQuiz(result);}
        catch(e){notice(e.message);button.disabled=false;}
      };
    }catch(e){notice(e.message);}
  }
  function reviewQuiz(result){
    quizContext=null;
    show(`<div class="quiz-sheet">${heading(escape(moduleOf(result.module).title),'Review each answer and its explanation. This result is saved in your progress.','QUIZ REVIEW')}<div class="exam-summary"><div class="score-ring">${result.score}/${result.total}</div><div><h2>Checkpoint complete</h2><p>${result.score===result.total?'All answers correct.':'Use the explanations below to work through your mistakes.'}</p></div></div>${result.details.map(d=>{const q=data.quizzes.find(q=>q.id===d.id);return `${quizQuestion(q,d.selected,true)}<div class="answer-feedback"><strong>${d.correct?'✓ Correct':'Correct answer: '+escape(q.options[d.answer])}</strong><p>${escape(d.explanation)}</p></div>`;}).join('')}<div class="quiz-actions"><button id="quiz-done">Back to quizzes</button><button id="quiz-practice">Practice this topic →</button><button id="quiz-again">Take full quiz again</button>${result.score<result.total?'<button id="quiz-missed" class="primary">Retry missed questions →</button>':''}</div></div>`);
    $('#quiz-done').onclick=()=>navigate('quiz');$('#quiz-again').onclick=()=>openQuiz(result.module,'all');
    $('#quiz-missed')?.addEventListener('click',()=>openQuiz(result.module,'missed'));
    $('#quiz-practice').onclick=()=>{selectedModule=result.module;navigate('practice');};
  }
  const answered=(exam,id)=>typeof exam.answers[id]==='number'||(typeof exam.answers[id]==='string'&&!!exam.answers[id].trim());
  function examChecklist(exam){
    const ids=[...exam.quizzes,...exam.codes],flags=exam.flags||[];
    return `<section class="review-toolbar" aria-label="Assessment review"><strong>${ids.filter(id=>answered(exam,id)).length} / ${ids.length} answered · ${flags.length} flagged</strong><div class="question-jump">${ids.map((id,i)=>`<button data-jump="${id}" class="${answered(exam,id)?'answered':''}" aria-label="Question ${i+1}: ${answered(exam,id)?'answered':'unanswered'}${flags.includes(id)?', flagged for review':''}">${i+1}${flags.includes(id)?' ⚑':''}</button>`).join('')}</div><p class="muted">Select a number to revisit a question. Flag questions to review before finishing.</p><button id="exam-retry-save">Retry save</button></section>`;
  }
  function bindExamChecklist(exam){
    $$('[data-jump]',main).forEach(b=>b.onclick=()=>{const id=b.dataset.jump;if(exam.codes.includes(id))openExercise(id,true);else $('#question-'+id)?.scrollIntoView({block:'center'});});
    $('#exam-retry-save').onclick=retrySaves;
  }
  function renderExam(){
    current=null;editor=null;examContext=false;clearInterval(timer);$('#assessment-banner').hidden=!state.active_exam||state.active_exam.status!=='active';
    const exam=state.active_exam;
    if(exam){
      if(exam.status==='grading'){show(heading('Your work is being reviewed.','We’re checking each coding answer against the example and hidden tests. Your answers are saved.','GRAND TEST')+'<div class="loading-state"><span class="loader"></span><p>Grading your assessment…</p></div>');activeJob=exam.job;finishing=true;pollJob(exam.job,true);return;}
      show(`<div class="workspace-top"><div>${heading('Your Grand Test','20 questions covering all ten chapters.','ASSESSMENT IN PROGRESS')}</div><span id="countdown" class="exam-timer"></span></div><div id="exam-checklist">${examChecklist(exam)}</div><p class="muted">Each question contributes equally; coding questions receive partial credit for passed tests. Missing answers score zero.</p><h2>Part 1 · Knowledge checks</h2><div class="exam-questions" style="margin:20px 0 32px">${exam.quizzes.map(id=>quizQuestion(data.quizzes.find(q=>q.id===id),exam.answers[id])).join('')}</div><h2>Part 2 · Put it into code</h2><div class="card-grid" style="margin:20px 0">${exam.codes.map(id=>{const e=exerciseOf(id);return `<div class="card" data-question="${id}"><span class="eyebrow">${escape(moduleOf(e.module).title)}</span><h3>${escape(e.title)}</h3><p>${answered(exam,id)?'Answer saved ✓':'Unanswered'}</p><button data-exam-code="${id}">Open coding problem →</button></div>`;}).join('')}</div><button class="primary" id="finish-exam">Review & finish my test →</button>`);
      const updateChecklist=()=>{if($('#exam-checklist')){$('#exam-checklist').innerHTML=examChecklist(exam);bindExamChecklist(exam);}};bindExamChecklist(exam);
      $$('input[type="radio"]',main).forEach(input=>input.onchange=()=>{
        const id=input.name,answer=+input.value;
        queueSave('exam:'+id,async()=>{await api('exam/answer',{exam:exam.id,id,answer});exam.answers[id]=answer;updateChecklist();}).catch(e=>notice(e.message));
      });
      $$('[data-question]',main).forEach(section=>{const id=section.dataset.question;section.insertAdjacentHTML('beforeend',`<label class="review-flag"><input type="checkbox" data-flag="${id}" ${(exam.flags||[]).includes(id)?'checked':''}> Flag for review</label>`);});
      $$('[data-flag]',main).forEach(input=>input.onchange=()=>{
        const id=input.dataset.flag,flagged=input.checked;
        queueSave('flag:'+id,async()=>{await api('exam/flag',{exam:exam.id,id,flagged});exam.flags=(exam.flags||[]).filter(f=>f!==id);if(flagged)exam.flags.push(id);updateChecklist();}).catch(e=>notice(e.message));
      });
      $$('[data-exam-code]',main).forEach(b=>b.onclick=()=>openExercise(b.dataset.examCode,true));
      $('#finish-exam').onclick=()=>finishExam(false);startTimer();return;
    }
    const latest=state.exams.at(-1);
    show(heading('Bring it all together.','A comprehensive checkpoint across the full course. Find your strengths, see what needs another look, and leave with a clear next step.','THE GRAND TEST')+(latest?examReport(latest):'')+`<div class="exam-intro"><section class="card"><span class="eyebrow">YOUR PERSONAL CHECKPOINT</span><h2>Ready to challenge yourself?</h2><p>Ten knowledge questions and ten coding problems, covering every chapter. Examples and hidden edge cases check your code. Different valid approaches are welcome.</p><div class="exam-meta"><div><strong>20</strong>questions</div><div><strong>10</strong>topics</div><div><strong>90 min</strong>timed option</div></div><div class="exam-actions"><button class="primary" id="start-timed">Start timed test →</button><button id="start-untimed">Go at my pace</button></div></section><section class="card"><span class="eyebrow">HOW IT WORKS</span><h3>A fair view of your progress</h3><p>Every question has equal weight. Coding problems earn partial credit for passed cases.</p><p>Your answers and remaining time survive a refresh. In timed mode, the clock continues while you are away.</p><p>Solutions and quiz explanations unlock after finishing. This is a learning assessment using the practice question bank, not a proctored certification.</p></section></div>`);
    for(const [id,timed] of [['start-timed',true],['start-untimed',false]])$('#'+id).onclick=async()=>{try{const r=await api('exam/start',{timed});state.active_exam=r.exam;serverOffset=r.server_time*1000-Date.now();renderExam();}catch(e){notice(e.message);}};
  }
  function startTimer(){
    clearInterval(timer);
    const tick=()=>{
      const exam=state.active_exam,banner=$('#assessment-banner');
      if(!exam||exam.status!=='active'){if(banner)banner.hidden=true;clearInterval(timer);return;}
      const remaining=exam.deadline?Math.max(0,Math.ceil(exam.deadline-(Date.now()+serverOffset)/1000)):null;
      const label=remaining===null?'Untimed test in progress':`${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,'0')} remaining`;
      if($('#countdown'))$('#countdown').textContent=label;
      if(banner){banner.hidden=false;$('#assessment-clock').textContent=label;$('#assessment-save').textContent=saveTasks.size?'Answers saving or needing retry':'Answers saved';}
      if(remaining===0&&!finishing){clearInterval(timer);dirty=false;clearTimeout(draftTimer);notice('Time is up. Grading the answers saved before the deadline.');finishExam(true);}
    };tick();timer=setInterval(tick,1000);
  }
  async function finishExam(automatic){
    if(finishing)return;
    try{
      if(!automatic){await flushDraft();await waitForSaves();const exam=state.active_exam,ids=[...exam.quizzes,...exam.codes];const missing=ids.filter(id=>!answered(exam,id)).length;if(!confirm(`Finish this assessment? ${missing} unanswered question(s) receive zero points. ${(exam.flags||[]).length} question(s) are flagged for review.`))return;}
      finishing=true;
      if(activeJob){await api('jobs/'+activeJob+'/stop',{});notice('Stopping the running program before final grading…');finishing=false;setTimeout(()=>finishExam(true),800);return;}
      await saveChain.catch(()=>{});
      const job=await api('exam/finish',{});state.active_exam.status='grading';state.active_exam.job=job.id;current=null;dirty=false;quizContext=null;saveTasks.clear();$('#assessment-banner').hidden=true;renderExam();
    }catch(e){finishing=false;notice(e.message);}
  }
  function examReport(result){return `<section class="exam-summary"><div class="score-ring">${result.score}%</div><div><span class="eyebrow">ASSESSMENT COMPLETE</span><h2>${result.score>=80?'Look how far you’ve come.':'A clear path to your next breakthrough.'}</h2><p class="muted">${result.earned.toFixed(1)} of ${result.total} points · ${result.timed?'Timed':'Untimed'} · ${new Date(result.finished*1000).toLocaleDateString()}</p><p>${result.revise.length?'Revisit: '+escape(result.revise.join(', ')):'Strong work across every topic.'}</p></div></section><details><summary>See topic scores and explained answers</summary><div class="progress-grid">${Object.entries(result.topics).map(([id,t])=>`<div><div class="progress-line"><span>${escape(t.title)}</span><strong>${t.earned.toFixed(1)} / ${t.total}</strong></div><div class="mini-progress"><span style="width:${100*t.earned/t.total}%"></span></div></div>`).join('')}</div>${result.items.map(item=>{const q=data.quizzes.find(q=>q.id===item.id),e=exerciseOf(item.id);return `<div class="test-row"><strong>${item.earned===1?'✓':'○'} ${escape(q?.question||e?.title)}</strong>${q?`<p>Answer: ${escape(q.options[item.answer])}</p><p>${escape(item.explanation)}</p>`:`<p>${item.earned.toFixed(2)} / 1 point · ${(item.tests||[]).map(t=>`${escape(t.name)}: ${t.passed?'passed':escape(t.status.replaceAll('_',' '))}`).join(' · ')}</p>`}</div>`;}).join('')}</details>`;}
  function renderProgress(){
    show(heading('Your effort adds up.','Every solved problem is a skill you can use. Pick up where you left off, or revisit a chapter.','MY PROGRESS')+stats()+`<button class="primary" id="progress-continue">Continue learning →</button><div class="section-heading"><h2>Chapter by chapter</h2></div><div class="progress-grid">${data.modules.map(m=>{const p=moduleProgress(m.id);return `<section class="card"><span class="eyebrow">CHAPTER ${+m.id+1}</span><h3>${escape(m.title)}</h3><div class="progress-line"><span>${p.done} of ${p.total} exercises completed</span><strong>${Math.round(100*p.done/p.total)}%</strong></div><div class="mini-progress"><span style="width:${100*p.done/p.total}%"></span></div><button data-revise="${m.id}" class="text-button">${p.done===p.total?'Revisit':'Keep learning'} →</button></section>`;}).join('')}</div><div class="section-heading"><h2>Quiz history</h2></div><div class="card">${state.quiz_results.length?`<table class="history"><thead><tr><th>Chapter</th><th>Score</th><th>Date</th></tr></thead><tbody>${state.quiz_results.slice().reverse().map(q=>`<tr><td>${escape(moduleOf(q.module).title)}</td><td>${q.score} / ${q.total}</td><td>${new Date(q.at*1000).toLocaleDateString()}</td></tr>`).join('')}</tbody></table>`:'<p>No quizzes yet. Your first checkpoint is waiting in Quiz Center.</p>'}</div><div class="section-heading"><h2>Grand Test results</h2></div>${state.exams.slice().reverse().map(examReport).join('')||'<div class="card"><p class="muted">Complete a Grand Test to see topic scores and revision suggestions here.</p></div>'}<div class="section-heading"><h2>Recent submissions</h2></div><div class="card">${state.submissions.length?`<table class="history"><thead><tr><th>Exercise</th><th>Result</th><th>Date</th></tr></thead><tbody>${state.submissions.slice(-20).reverse().map((s,index)=>`<tr><td><button class="text-button" data-history="${state.submissions.length-1-index}">${escape(exerciseOf(s.exercise)?.title||s.exercise)}</button></td><td>${Math.round(100*s.result.score)}%</td><td>${new Date(s.at*1000).toLocaleDateString()}</td></tr>`).join('')}</tbody></table><div id="history-code"></div>`:'<p class="muted">Submit a solution to start your history.</p>'}</div>`);
    $('#progress-continue').onclick=()=>openExercise(state.last_exercise);
    $$('[data-revise]',main).forEach(b=>b.onclick=()=>{selectedModule=b.dataset.revise;navigate('practice');});
    $$('[data-history]',main).forEach(b=>b.onclick=()=>{const s=state.submissions[+b.dataset.history];$('#history-code').innerHTML=`<details open><summary>Submitted code · ${escape(exerciseOf(s.exercise)?.title)}</summary><pre>${escape(s.code)}</pre></details>`;});
  }
  $$('[data-view]').forEach(b=>b.onclick=()=>navigate(b.dataset.view));
  $('#resume-exam').onclick=()=>navigate('exam');
  $('#retry-pending').onclick=retrySaves;
  $('#runtime-info').onclick=()=>$('#info-dialog').showModal();
  window.addEventListener('beforeunload',event=>{if(dirty||saveTasks.size){event.preventDefault();event.returnValue='';}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&dirty)flushDraft().catch(()=>{});});
  async function boot(){
    try{await refresh();const hash=location.hash.slice(1).split('/');if(hash[0]==='exercise'&&exerciseOf(hash[1])){view=exerciseOf(hash[1]).mode==='puzzle'?'puzzle':'practice';await openExercise(hash[1]);}else if(hash[0]==='exam-code'&&state.active_exam?.codes.includes(hash[1]))await openExercise(hash[1],true);else if(hash[0]==='quiz'&&data.modules.some(m=>m.id===hash[1])){view='quiz';await openQuiz(hash[1]);}else await navigate(names[hash[0]]?hash[0]:'practice');if(state.active_exam?.status==='active')startTimer();const job=JSON.parse(sessionStorage.getItem('python-active-job')||'null');if(job&&current?.id===job.exercise){activeJob=job.id;busy(true);setPane('results');pollJob(job.id,false);}if(!data.runtime_ready)notice('Python execution needs server setup. Learning content and saved progress are available.');}
    catch(e){show(`<div class="loading-state"><h2>We couldn’t open your learning space.</h2><p>${escape(e.message)}</p><button id="retry" class="primary">Try again</button><p><a href="/user/login">Sign in to your account</a></p></div>`);$('#retry').onclick=boot;}
  }
  boot();
})();
