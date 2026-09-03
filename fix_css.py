import re

with open('static/css/tailwind.css', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace button primary styles
btn_old = """.ui-button--primary { background: var(--color-brand) !important; color: var(--color-bg) !important; border: 1px solid transparent !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; transition: all 0.2s ease !important; }
.ui-button--primary:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important; }
.dark .ui-button--primary { background: #ffffff !important; color: #000000 !important; }
.dark .ui-button--primary:hover { background: #f3f4f6 !important; }"""

btn_new = """.ui-button--primary { 
    background: linear-gradient(135deg, #3b82f6, #a855f7, #10b981) !important; 
    color: #ffffff !important; 
    border: 1px solid transparent !important; 
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; 
    background-size: 200% auto !important;
}
.ui-button--primary:hover { 
    background-position: right center !important;
    transform: translateY(-2px) !important; 
    box-shadow: 0 8px 25px rgba(168, 85, 247, 0.5) !important; 
}
.dark .ui-button--primary { 
    color: #ffffff !important; 
}
.dark .ui-button--primary:hover { 
    box-shadow: 0 8px 25px rgba(168, 85, 247, 0.6) !important; 
}

/* Add custom card hover effects */
.hover-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.hover-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
.dark .hover-card {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.dark .hover-card:hover {
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
}

/* Gradient text for special links */
.gradient-link {
    background: linear-gradient(135deg, #3b82f6, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    transition: all 0.3s ease;
    font-weight: 600;
}
.gradient-link:hover {
    background: linear-gradient(135deg, #a855f7, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
"""

text = text.replace(btn_old, btn_new)

with open('static/css/tailwind.css', 'w', encoding='utf-8') as f:
    f.write(text)
