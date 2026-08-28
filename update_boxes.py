import os

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# We will replace the entire programsGrid with 6 boxes containing direct Apply links
new_grid = '''      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10" id="programsGrid">
        <!-- Google Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-emerald-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(16,185,129,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <i class="fab fa-google text-emerald-400"></i>
            </div>
            <div><div class="text-sm font-bold text-white">Google</div><div class="text-xs text-emerald-400">Developer Student Clubs</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">Help Google promote its products on campus and earn certification & exclusive perks.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://developers.google.com/community/gdsc" target="_blank" class="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>

        <!-- Microsoft Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-blue-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(59,130,246,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <i class="fab fa-microsoft text-blue-400"></i>
            </div>
            <div><div class="text-sm font-bold text-white">Microsoft</div><div class="text-xs text-blue-400">Student Ambassadors</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">Microsoft's annual student programs covering AI, cloud, data engineering with certifications.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://mvp.microsoft.com/en-us/studentambassadors" target="_blank" class="bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>

        <!-- Amazon Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-orange-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(249,115,22,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center">
              <i class="fab fa-aws text-orange-400"></i>
            </div>
            <div><div class="text-sm font-bold text-white">Amazon AWS</div><div class="text-xs text-orange-400">Educate Academy</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">AWS programs for students including free cloud training, credits, and career pathways.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://aws.amazon.com/education/awseducate/" target="_blank" class="bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>

        <!-- Meta Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-indigo-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(99,102,241,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
              <i class="fab fa-meta text-indigo-400"></i>
            </div>
            <div><div class="text-sm font-bold text-white">Meta</div><div class="text-xs text-indigo-400">Meta University</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">Immersive tech and engineering internships for underrepresented students.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://www.metacareers.com/students-and-grads/" target="_blank" class="bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>

        <!-- IBM Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(6,182,212,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
              <i class="fas fa-server text-cyan-400"></i>
            </div>
            <div><div class="text-sm font-bold text-white">IBM</div><div class="text-xs text-cyan-400">SkillsBuild</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">Free learning, credentials, and mentorship in AI, cybersecurity, and cloud computing.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://skillsbuild.org/students" target="_blank" class="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>

        <!-- Apple Box -->
        <div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/30 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(148,163,184,0.15)] flex flex-col">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-slate-500/20 flex items-center justify-center">
              <i class="fab fa-apple text-slate-200"></i>
            </div>
            <div><div class="text-sm font-bold text-white">Apple</div><div class="text-xs text-slate-300">Swift Student Challenge</div></div>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed mb-4 flex-grow">Create an original app playground and win exclusive Apple WWDC awards.</p>
          <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-700/50">
            <a href="#subscribe" class="text-xs font-bold text-slate-400 hover:text-white transition">Alert Me <i class="fas fa-bell"></i></a>
            <a href="https://developer.apple.com/swift-student-challenge/" target="_blank" class="bg-slate-500/20 hover:bg-slate-500/40 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition">Apply Now <i class="fas fa-external-link-alt ml-1"></i></a>
          </div>
        </div>
      </div>'''

import re
old_grid_pattern = r'<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10" id="programsGrid">.*?</div>\s+</div>'
# Need a better regex or split approach
parts = content.split('<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10" id="programsGrid">')
if len(parts) == 2:
    after_grid = parts[1].split('<!-- Quick Student Program Alert Signup -->')
    if len(after_grid) == 2:
        content = parts[0] + new_grid + '\n\n      <!-- Quick Student Program Alert Signup -->' + after_grid[1]
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated index.html with new programs and apply links.")
