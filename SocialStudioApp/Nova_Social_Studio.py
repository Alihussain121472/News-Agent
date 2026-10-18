import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import threading

class SocialStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nova Social Studio")
        self.root.geometry("900x700")
        self.root.configure(bg="#0f172a")
        try:
            self.root.iconbitmap(r"c:\Users\DELL\OneDrive\Desktop\my agent\static\favicon.ico")
        except:
            pass # Slate 900
        
        # Load API Key directly from the Nova OS env local if possible
        self.api_key = self.load_api_key()
        
        self.setup_ui()
        
    def load_api_key(self):
        try:
            env_path = r"c:\Users\DELL\OneDrive\Desktop\my agent\.env.local"
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        return line.split('=', 1)[1].strip()
        except:
            pass
        return ""
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#0f172a')
        style.configure('TLabel', background='#0f172a', foreground='#f8fafc', font=('Segoe UI', 10, 'bold'))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#38bdf8')
        style.configure('TButton', background='#2563eb', foreground='white', font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('TButton', background=[('active', '#1d4ed8')])
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = ttk.Label(main_frame, text="✨ Nova Social Studio (Desktop App)", style='Header.TLabel')
        header.pack(anchor="w", pady=(0, 20))
        
        ttk.Label(main_frame, text="Enter Topic or Article URL:").pack(anchor="w")
        
        self.topic_text = tk.Text(main_frame, height=4, font=('Segoe UI', 10), bg="#1e293b", fg="white", insertbackground="white", relief="flat")
        self.topic_text.pack(fill=tk.X, pady=(5, 15))
        
        self.generate_btn = ttk.Button(main_frame, text="Generate Posts", command=self.generate_async)
        self.generate_btn.pack(anchor="w", pady=(0, 20))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="#94a3b8")
        self.status_label.pack(anchor="w", pady=(0, 10))
        
        # Output Grid
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Twitter
        t_frame = ttk.Frame(output_frame)
        t_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(t_frame, text="X (Twitter)", foreground="#38bdf8").pack(anchor="w")
        self.tw_text = tk.Text(t_frame, font=('Segoe UI', 10), bg="#f8fafc", fg="#0f172a", relief="flat")
        self.tw_text.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(t_frame, text="Copy", command=lambda: self.copy_text(self.tw_text)).pack(fill=tk.X)
        
        # LinkedIn
        l_frame = ttk.Frame(output_frame)
        l_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(l_frame, text="LinkedIn", foreground="#60a5fa").pack(anchor="w")
        self.li_text = tk.Text(l_frame, font=('Segoe UI', 10), bg="#f8fafc", fg="#0f172a", relief="flat")
        self.li_text.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(l_frame, text="Copy", command=lambda: self.copy_text(self.li_text)).pack(fill=tk.X)
        
        # Facebook
        f_frame = ttk.Frame(output_frame)
        f_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(f_frame, text="Facebook", foreground="#818cf8").pack(anchor="w")
        self.fb_text = tk.Text(f_frame, font=('Segoe UI', 10), bg="#f8fafc", fg="#0f172a", relief="flat")
        self.fb_text.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(f_frame, text="Copy", command=lambda: self.copy_text(self.fb_text)).pack(fill=tk.X)

    def copy_text(self, text_widget):
        self.root.clipboard_clear()
        self.root.clipboard_append(text_widget.get("1.0", tk.END).strip())
        self.status_var.set("Copied to clipboard!")

    def generate_async(self):
        topic = self.topic_text.get("1.0", tk.END).strip()
        if not topic:
            return
            
        if not self.api_key:
            self.status_var.set("Error: GROQ_API_KEY not found in .env.local")
            return
            
        self.generate_btn.config(state="disabled")
        self.status_var.set("Generating AI content... Please wait.")
        self.tw_text.delete("1.0", tk.END)
        self.li_text.delete("1.0", tk.END)
        self.fb_text.delete("1.0", tk.END)
        
        thread = threading.Thread(target=self.generate_content, args=(topic,))
        thread.daemon = True
        thread.start()

    def generate_content(self, topic):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        system_prompt = """You are an expert Social Media Manager. Generate three distinct posts based on the user's topic:
1. X (Twitter): Short, punchy, engaging, max 280 chars, 1-2 hashtags.
2. LinkedIn: Professional, longer form, career/tech impact, 3-4 hashtags.
3. Facebook/Instagram: Casual, visual-friendly, engaging question, emojis.
Return EXACTLY as a JSON object with keys: "twitter", "linkedin", "facebook"."""

        try:
            models_resp = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=5)
            available_models = [m['id'] for m in models_resp.json().get('data', [])]
            model_name = 'llama-3.3-70b-versatile'
            for preferred in ['llama-3.3-70b-versatile', 'llama3-70b-8192', 'llama3-8b-8192', 'mixtral-8x7b-32768']:
                if preferred in available_models:
                    model_name = preferred
                    break
            else:
                if available_models: model_name = available_models[0]

            payload = {
                'model': model_name,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': topic}
                ],
                'temperature': 0.7,
                'max_tokens': 800,
                'response_format': {'type': 'json_object'}
            }
            
            resp = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            
            result_text = resp.json()['choices'][0]['message']['content'].strip()
            result = json.loads(result_text)
            
            self.root.after(0, self.update_ui_success, result)
            
        except Exception as e:
            self.root.after(0, self.update_ui_error, str(e))
            
    def update_ui_success(self, result):
        self.tw_text.insert(tk.END, result.get("twitter", ""))
        self.li_text.insert(tk.END, result.get("linkedin", ""))
        self.fb_text.insert(tk.END, result.get("facebook", ""))
        self.status_var.set("Generation complete!")
        self.generate_btn.config(state="normal")
        
    def update_ui_error(self, err):
        self.status_var.set(f"Error: {err}")
        self.generate_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SocialStudioApp(root)
    root.mainloop()
