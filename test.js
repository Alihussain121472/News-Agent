
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'] },
          animation: { 'float': 'float 3s ease-in-out infinite', 'pulse-slow': 'pulse 3s ease-in-out infinite' }
        }
      }
    }
  

           (adsbygoogle = window.adsbygoogle || []).push({});
      

// Mobile menu
document.getElementById('mobileMenuBtn').addEventListener('click',()=>{
  document.getElementById('mobileMenu').classList.toggle('hidden');
});

// FAQ
function toggleFaq(btn){
  const ans = btn.nextElementSibling;
  const icon = btn.querySelector('i');
  const isOpen = !ans.classList.contains('hidden');
  document.querySelectorAll('.faq-ans').forEach(a=>a.classList.add('hidden'));
  document.querySelectorAll('.faq-btn i').forEach(i=>{i.classList.remove('fa-minus','rotate-45');i.classList.add('fa-plus');});
  if(!isOpen){ ans.classList.remove('hidden'); icon.classList.remove('fa-plus'); icon.classList.add('fa-minus'); }
}

// Load stats
fetch('/api/statistics').then(r=>r.json()).then(d=>{
  animateNum('heroSubscribers', d.active_users||0);
  animateNum('heroArticles', d.total_articles||0);
}).catch(()=>{});

function animateNum(id, target){
  const el = document.getElementById(id); if(!el) return;
  let c=0; const step=Math.ceil(target/30);
  const t=setInterval(()=>{ c=Math.min(c+step,target); el.textContent=c.toLocaleString(); if(c>=target) clearInterval(t); },40);
}

// Subscribe
document.getElementById('subscribeForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const btn = e.target.querySelector('button[type=submit]');
  const msg = document.getElementById('subscribeMessage');
  btn.disabled=true; btn.innerHTML='<i class="fas fa-spinner fa-spin mr-2"></i>Subscribing...';
  try{
    const r = await fetch('/api/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name:document.getElementById('subName').value.trim(), email:document.getElementById('subEmail').value.trim()})});
    const d = await r.json();
    msg.className='rounded-xl p-4 text-sm font-semibold mt-3 '+(r.ok&&d.status!=='error'?'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30':'bg-red-500/20 text-red-300 border border-red-500/30');
    msg.innerHTML = (d.message||'Subscribed successfully!') + (d.redirect ? `<div class="mt-3"><a href="${d.redirect}" class="inline-block bg-gradient-to-r from-blue-600 to-emerald-500 hover:from-blue-500 hover:to-emerald-400 text-white font-bold px-5 py-2.5 rounded-xl text-xs shadow-lg transition">Open My Dashboard â†’</a></div>` : '');
    msg.classList.remove('hidden');
    if(r.ok&&d.status!=='error') e.target.reset();
  }catch(err){
    msg.className='rounded-xl p-4 text-sm font-semibold mt-2 bg-red-500/20 text-red-300 border border-red-500/30';
    msg.textContent='Something went wrong. Please try again.'; msg.classList.remove('hidden');
  }finally{ btn.disabled=false; btn.innerHTML='Subscribe <i class="fas fa-arrow-right ml-1"></i>'; }
});

// Program Alert quick join
const pForm = document.getElementById('programAlertForm');
if (pForm) {
  pForm.addEventListener('submit', async function(e){
    e.preventDefault();
    const btn = this.querySelector('button[type=submit]');
    const msg = document.getElementById('progAlertMsg');
    const email = document.getElementById('progAlertEmail').value.trim();
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Joining...';
    try {
      const r = await fetch('/api/programs/join-alert', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, program_title: 'All Student Opportunities (Google, MSFT, AWS, NASA)'})
      });
      const d = await r.json();
      msg.className = 'mt-3 rounded-xl p-3 text-xs font-semibold text-center ' + (r.ok ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30');
      msg.innerHTML = (d.message || 'Joined successfully!') + (d.redirect ? `<div class="mt-2"><a href="${d.redirect}" class="inline-block bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-4 py-1.5 rounded-lg text-xs transition">Open Student Dashboard â†’</a></div>` : '');
      msg.classList.remove('hidden');
      if (r.ok) this.reset();
    } catch(err) {
      msg.className = 'mt-3 rounded-xl p-3 text-xs font-semibold text-center bg-red-500/20 text-red-300 border border-red-500/30';
      msg.textContent = 'Unexpected error. Please try again.';
      msg.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span>Join Alerts</span><i class="fas fa-paper-plane text-xs ml-2"></i>';
    }
  });
}

// Contact
async function handleContact(e){
  e.preventDefault();
  const btn=e.target.querySelector('button[type=submit]'); const msg=document.getElementById('contactMsg');
  btn.disabled=true; btn.textContent='Sending...';
  try{
    const r=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name:document.getElementById('cName').value,email:document.getElementById('cEmail').value,
        subject:document.getElementById('cSubject').value,message:document.getElementById('cMessage').value})});
    const d=await r.json();
    msg.className='rounded-xl p-3 text-sm font-semibold text-center '+(r.ok?'bg-emerald-500/20 text-emerald-300':'bg-red-500/20 text-red-300');
    msg.textContent=d.message; msg.classList.remove('hidden');
    if(r.ok) e.target.reset();
  }catch(err){
    msg.className='rounded-xl p-3 text-sm font-semibold text-center bg-red-500/20 text-red-300';
    msg.textContent='Failed to send. Try again.'; msg.classList.remove('hidden');
  }finally{ btn.disabled=false; btn.textContent='Send Message'; }
}

// User session persistence & Navbar sync (keeps user name & email visible for lifetime until logout)
async function syncUserNavbar(){
  const guestBox = document.getElementById('navGuestPortion');
  const userBox = document.getElementById('navUserPortion');
  const mobileGuest = document.getElementById('mobileGuestPortion');
  const mobileUser = document.getElementById('mobileUserPortion');
  
  let user = null;
  const srvEmail = "{{ user_email or '' }}";
  const srvName = "{{ user_name or '' }}";

  if (srvEmail && srvEmail !== 'None') {
    user = { email: srvEmail, name: srvName || srvEmail.split('@')[0] };
    localStorage.setItem('nova_user_email', srvEmail);
    if (srvName && srvName !== 'None') localStorage.setItem('nova_user_name', srvName);
    localStorage.setItem('nova_logged_in', 'true');
  } else {
    const localEmail = localStorage.getItem('nova_user_email');
    const localName = localStorage.getItem('nova_user_name');
    if (localEmail && localStorage.getItem('nova_logged_in') === 'true') {
      user = { email: localEmail, name: localName || localEmail.split('@')[0] };
    }
  }

  // Verify in background with API
  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    if (data.authenticated || data.logged_in) {
      user = { email: data.email, name: data.name };
      localStorage.setItem('nova_user_email', data.email);
      localStorage.setItem('nova_user_name', data.name);
      localStorage.setItem('nova_logged_in', 'true');
    } else if (res.status === 401 && !srvEmail) {
      user = null;
      localStorage.removeItem('nova_logged_in');
    }
  } catch(e){}

  if (user && user.email) {
    const initial = (user.name || user.email).charAt(0).toUpperCase();
    const displayName = user.name || user.email.split('@')[0];
    if (document.getElementById('navAvatar')) document.getElementById('navAvatar').textContent = initial;
    if (document.getElementById('navUserName')) document.getElementById('navUserName').textContent = displayName;
    if (document.getElementById('navUserEmail')) document.getElementById('navUserEmail').textContent = user.email;
    if (document.getElementById('mobileAvatar')) document.getElementById('mobileAvatar').textContent = initial;
    if (document.getElementById('mobileUserName')) document.getElementById('mobileUserName').textContent = displayName;
    if (document.getElementById('mobileUserEmail')) document.getElementById('mobileUserEmail').textContent = user.email;

    if (guestBox) guestBox.classList.add('hidden');
    if (userBox) { userBox.classList.remove('hidden'); userBox.classList.add('flex'); }
    if (mobileGuest) mobileGuest.classList.add('hidden');
    if (mobileUser) mobileUser.classList.remove('hidden');
  } else {
    if (guestBox) guestBox.classList.remove('hidden');
    if (userBox) { userBox.classList.add('hidden'); userBox.classList.remove('flex'); }
    if (mobileGuest) mobileGuest.classList.remove('hidden');
    if (mobileUser) mobileUser.classList.add('hidden');
  }
}

async function handleUserLogout(){
  try {
    await fetch('/api/auth/logout', {method: 'POST'});
  } catch(e){}
  localStorage.removeItem('nova_user_email');
  localStorage.removeItem('nova_user_name');
  localStorage.removeItem('nova_logged_in');
  window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', syncUserNavbar);


        function toggleBot() {
            const win = document.getElementById('novaBotWindow');
            win.classList.toggle('hidden');
        }

                function appendMessage(text, isUser=false) {
            const container = document.getElementById('botMessages');
            const msgDiv = document.createElement('div');
            if (isUser) {
                msgDiv.className = 'flex gap-2 max-w-[85%] self-end flex-row-reverse';
                msgDiv.innerHTML = '<div class="bg-blue-600 p-2.5 rounded-2xl rounded-tr-sm text-white shadow-sm">' + text + '</div>';
            } else {
                msgDiv.className = 'flex gap-2 max-w-[85%]';
                msgDiv.innerHTML = '<div class="w-6 h-6 bg-blue-100 rounded-full flex-shrink-0 flex items-center justify-center text-blue-600"><i class="fas fa-robot text-[10px]"></i></div><div class="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-sm text-slate-700 shadow-sm">' + text + '</div>';
            }
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }

        async function sendBotMessage() {
            const input = document.getElementById('botInput');
            const text = input.value.trim();
            if(!text) return;
            
            input.value = '';
            appendMessage(text, true);

            // Simple AI Logic
            const lower = text.toLowerCase();
            setTimeout(async () => {
                if (lower.includes('cost') || lower.includes('price') || lower.includes('free')) {
                    appendMessage("Nova Brief is 100% free for students! We monetize via Google AdSense so you never have to pay.");
                } else if (lower.includes('subscribe') || lower.includes('join') || lower.includes('register')) {
                    appendMessage("You can subscribe by entering your email at the top of the page. You'll get instant welcome emails and daily tech alerts!");
                } else if (lower.includes('program') || lower.includes('internship')) {
                    appendMessage("We scan programs from Google, Apple, Meta, and IBM. When you subscribe, you get direct 1-click registration links.");
                } else {
                    // Send to admin inbox
                    appendMessage("That's a great question! I'm forwarding your message directly to our human Admin team right now. They will review it in the Nova OS Inbox!");
                    try {
                        await fetch('/api/contact', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                name: 'Chatbot User',
                                email: 'chatbot@novabrief.local',
                                subject: 'Chatbot Inquiry',
                                message: text
                            })
                        });
                    } catch(e) {}
                }
            }, 800);
        }
    

