import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<strong class="text-white"></strong>', '<strong class="text-white">$1</strong>')
text = text.replace('<em class="text-slate-300"></em>', '<em class="text-slate-300">$1</em>')
text = text.replace('resultContent.innerHTML = <i class="fas fa-exclamation-circle text-red-500 mr-2"></i> ;', 'resultContent.innerHTML = `<i class="fas fa-exclamation-circle text-red-500 mr-2"></i> ${data.message}`;')
text = text.replace('resultContent.innerHTML = <i class="fas fa-exclamation-circle text-red-500 mr-2"></i> Network error. Please try again.;', 'resultContent.innerHTML = `<i class="fas fa-exclamation-circle text-red-500 mr-2"></i> Network error. Please try again.`;')

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
