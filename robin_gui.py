import speech_recognition as sr
import webbrowser
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
from pydub import AudioSegment
import pygame
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import math
import time

# Configuration
NEWS_API_KEY = "3d9f6cdf8cac4e79a4f1f8310ce26e25"
OPENAI_API_KEY = "<yourapikey>"  # Update this with your API key

# Initialize recognizer
recognizer = sr.Recognizer()

# Color Palette from Coolors - Blue Ocean Theme
COLORS = {
    'darkest': '#012a4a',      # Deep navy
    'darker': '#013a63',       # Dark blue
    'dark': '#01497c',         # Medium dark blue
    'medium_dark': '#014f86',  # Medium blue
    'medium': '#2a6f97',       # Medium light blue
    'medium_light': '#2c7da0', # Light medium blue
    'light': '#468faf',        # Light blue
    'lighter': '#61a5c2',      # Lighter blue
    'lightest': '#89c2d9',     # Very light blue
    'pale': '#a9d6e5',         # Pale blue
    'text_light': '#ffffff',
    'text_dark': '#012a4a',
    'text_muted': '#2a6f97'
}


class ModernButton(tk.Canvas):
    """Modern animated button widget"""
    def __init__(self, parent, text, command, width=150, height=45, 
                 bg_color=COLORS['medium'], hover_color=COLORS['medium_light'], 
                 text_color=COLORS['text_light'], **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=COLORS['pale'])
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.current_color = bg_color
        
        # Create rounded rectangle
        radius = 12
        self.rect = self.create_rectangle(
            radius, 0, width-radius, height,
            fill=bg_color, outline="", width=0
        )
        self.oval1 = self.create_oval(
            0, 0, radius*2, height,
            fill=bg_color, outline="", width=0
        )
        self.oval2 = self.create_oval(
            width-radius*2, 0, width, height,
            fill=bg_color, outline="", width=0
        )
        
        self.text_id = self.create_text(width//2, height//2, text=text,
                                       fill=text_color,
                                       font=("Segoe UI", 11, "bold"))
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Motion>", self.on_motion)
        
    def on_enter(self, event):
        self.is_hovered = True
        self.animate_color(self.hover_color)
    
    def on_leave(self, event):
        self.is_hovered = False
        self.animate_color(self.bg_color)
    
    def on_motion(self, event):
        self.config(cursor="hand2")
    
    def animate_color(self, target_color):
        """Smooth color transition"""
        self.current_color = target_color
        self.itemconfig(self.rect, fill=target_color)
        self.itemconfig(self.oval1, fill=target_color)
        self.itemconfig(self.oval2, fill=target_color)
    
    def on_click(self, event):
        if self.command:
            # Visual feedback on click
            darker = self.darken_color(self.current_color)
            self.animate_color(darker)
            self.after(100, lambda: self.animate_color(self.current_color))
            self.command()
    
    def darken_color(self, color):
        """Darken color for click effect"""
        if color == COLORS['medium']:
            return COLORS['medium_dark']
        elif color == COLORS['medium_light']:
            return COLORS['medium']
        elif color == COLORS['light']:
            return COLORS['medium_light']
        else:
            return COLORS['dark']
    
    def update_text(self, new_text):
        """Update button text"""
        self.itemconfig(self.text_id, text=new_text)
    
    def update_color(self, new_color, new_hover):
        """Update button colors"""
        self.bg_color = new_color
        self.hover_color = new_hover
        self.current_color = new_color
        self.animate_color(new_color)


class PulsingIndicator(tk.Canvas):
    """Animated pulsing status indicator"""
    def __init__(self, parent, size=40, color=COLORS['light']):
        super().__init__(parent, width=size, height=size, 
                        highlightthickness=0, bg=COLORS['pale'])
        self.size = size
        self.color = color
        self.center = size // 2
        self.pulse_radius = 0
        self.pulse_direction = 1
        self.circle = self.create_oval(
            self.center - 10, self.center - 10,
            self.center + 10, self.center + 10,
            fill=color, outline="", width=2
        )
        self.animate()
    
    def animate(self):
        """Continuous pulse animation"""
        if self.pulse_radius > 15 or self.pulse_radius < 0:
            self.pulse_direction *= -1
        
        self.pulse_radius += self.pulse_direction * 0.6
        opacity = max(0.2, 1 - (self.pulse_radius / 15))
        
        # Create pulse effect
        if hasattr(self, 'pulse_circle'):
            self.delete(self.pulse_circle)
        
        if self.pulse_radius > 0:
            self.pulse_circle = self.create_oval(
                self.center - 10 - self.pulse_radius,
                self.center - 10 - self.pulse_radius,
                self.center + 10 + self.pulse_radius,
                self.center + 10 + self.pulse_radius,
                fill=self.color, outline="", stipple="gray50"
            )
        
        self.after(25, self.animate)
    
    def set_color(self, color):
        """Change indicator color"""
        self.color = color
        self.itemconfig(self.circle, fill=color)


class RobinGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robin - Voice Assistant")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS['pale'])
        self.root.resizable(True, True)
        
        # Center window
        self.center_window()
        
        # Variables
        self.listening = False
        self.processing = False
        self.speaking = False
        self.conversation_history = []
        
        # Create UI
        self.create_widgets()
        
        # Initialize audio
        pygame.mixer.init()
        
        # Start listening thread
        self.start_listening_thread()
        
        # Welcome animation
        self.root.after(500, self.welcome_animation)
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """Create all GUI widgets with modern website-like design"""
        # Main container
        main_container = tk.Frame(self.root, bg=COLORS['pale'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header Section - Website style
        header_frame = tk.Frame(main_container, bg=COLORS['pale'], height=120)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Header content container
        header_content = tk.Frame(header_frame, bg=COLORS['pale'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Logo and Title Section
        title_section = tk.Frame(header_content, bg=COLORS['pale'])
        title_section.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo emoji
        logo_label = tk.Label(
            title_section,
            text="🦇",
            font=("Segoe UI", 40),
            bg=COLORS['pale'],
            fg=COLORS['darkest']
        )
        logo_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Title
        title_container = tk.Frame(title_section, bg=COLORS['pale'])
        title_container.pack(side=tk.LEFT)
        
        title_label = tk.Label(
            title_container,
            text="ROBIN",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS['pale'],
            fg=COLORS['darkest']
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(
            title_container,
            text="Your Intelligent Voice Assistant",
            font=("Segoe UI", 12),
            bg=COLORS['pale'],
            fg=COLORS['medium']
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Control Buttons in Header (Right side)
        controls_header = tk.Frame(header_content, bg=COLORS['pale'])
        controls_header.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status indicator in header
        status_header_frame = tk.Frame(controls_header, bg=COLORS['pale'])
        status_header_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        self.status_indicator = PulsingIndicator(status_header_frame, size=45, color=COLORS['light'])
        self.status_indicator.pack()
        
        # Status text
        self.status_label = tk.Label(
            controls_header,
            text="● Ready",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS['pale'],
            fg=COLORS['medium']
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.status_text = tk.Label(
            controls_header,
            text="Say 'robin' to activate",
            font=("Segoe UI", 11),
            bg=COLORS['pale'],
            fg=COLORS['text_muted']
        )
        self.status_text.pack(side=tk.LEFT, padx=(0, 20))
        
        # Main Control Buttons - Always visible
        self.listen_btn = ModernButton(
            controls_header,
            "🎤 Start Listening",
            self.toggle_listening,
            width=160,
            height=45,
            bg_color=COLORS['medium'],
            hover_color=COLORS['medium_light']
        )
        self.listen_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.listen_btn_text = "🎤 Start Listening"
        
        stop_btn = ModernButton(
            controls_header,
            "⏹ Stop",
            self.stop_assistant,
            width=100,
            height=45,
            bg_color=COLORS['dark'],
            hover_color=COLORS['medium_dark']
        )
        stop_btn.pack(side=tk.LEFT)
        
        # Main Content Area - Two Column Layout
        content_frame = tk.Frame(main_container, bg=COLORS['pale'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))
        
        # Left Column - Conversation Area (70%)
        left_column = tk.Frame(content_frame, bg=COLORS['pale'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Conversation Card
        conv_card = tk.Frame(left_column, bg=COLORS['text_light'], relief=tk.FLAT)
        conv_card.pack(fill=tk.BOTH, expand=True)
        
        # Card header
        conv_header = tk.Frame(conv_card, bg=COLORS['text_light'], height=60)
        conv_header.pack(fill=tk.X, padx=25, pady=(25, 0))
        conv_header.pack_propagate(False)
        
        conv_title = tk.Label(
            conv_header,
            text="💬 Conversation",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS['text_light'],
            fg=COLORS['darkest'],
            anchor=tk.W
        )
        conv_title.pack(side=tk.LEFT)
        
        clear_btn_header = ModernButton(
            conv_header,
            "🗑 Clear",
            self.clear_history,
            width=100,
            height=35,
            bg_color=COLORS['lightest'],
            hover_color=COLORS['lighter'],
            text_color=COLORS['darkest']
        )
        clear_btn_header.pack(side=tk.RIGHT)
        
        # Conversation text area
        text_container = tk.Frame(conv_card, bg=COLORS['text_light'])
        text_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(15, 25))
        
        self.conversation_text = scrolledtext.ScrolledText(
            text_container,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=COLORS['pale'],
            fg=COLORS['darkest'],
            insertbackground=COLORS['medium'],
            selectbackground=COLORS['medium'],
            selectforeground=COLORS['text_light'],
            relief=tk.FLAT,
            padx=20,
            pady=20,
            borderwidth=0,
            highlightthickness=0
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        self.conversation_text.config(state=tk.DISABLED)
        
        # Configure text tags
        self.conversation_text.tag_config("user", foreground=COLORS['medium'], 
                                         font=("Segoe UI", 11, "bold"))
        self.conversation_text.tag_config("assistant", foreground=COLORS['light'], 
                                         font=("Segoe UI", 11, "bold"))
        self.conversation_text.tag_config("message", foreground=COLORS['text_muted'])
        self.conversation_text.tag_config("timestamp", foreground=COLORS['lighter'], 
                                         font=("Segoe UI", 9))
        
        # Input Section at bottom of left column
        input_card = tk.Frame(left_column, bg=COLORS['text_light'], relief=tk.FLAT)
        input_card.pack(fill=tk.X, pady=(15, 0))
        
        input_container = tk.Frame(input_card, bg=COLORS['text_light'])
        input_container.pack(fill=tk.X, padx=25, pady=20)
        
        input_label = tk.Label(
            input_container,
            text="Type your command:",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['text_light'],
            fg=COLORS['darkest'],
            anchor=tk.W
        )
        input_label.pack(fill=tk.X, pady=(0, 10))
        
        input_frame = tk.Frame(input_container, bg=COLORS['text_light'])
        input_frame.pack(fill=tk.X)
        
        self.command_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            bg=COLORS['pale'],
            fg=COLORS['darkest'],
            insertbackground=COLORS['medium'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=2,
            highlightbackground=COLORS['lightest'],
            highlightcolor=COLORS['medium']
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=12)
        self.command_entry.bind("<Return>", lambda e: self.process_text_command())
        self.command_entry.bind("<FocusIn>", lambda e: self.command_entry.config(
            highlightbackground=COLORS['medium']))
        self.command_entry.bind("<FocusOut>", lambda e: self.command_entry.config(
            highlightbackground=COLORS['lightest']))
        
        send_btn = ModernButton(
            input_frame,
            "Send",
            self.process_text_command,
            width=120,
            height=45,
            bg_color=COLORS['medium'],
            hover_color=COLORS['medium_light']
        )
        send_btn.pack(side=tk.LEFT)
        
        # Right Column - Quick Actions & Info (30%)
        right_column = tk.Frame(content_frame, bg=COLORS['pale'], width=300)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        right_column.pack_propagate(False)
        
        # Quick Actions Card
        actions_card = tk.Frame(right_column, bg=COLORS['text_light'], relief=tk.FLAT)
        actions_card.pack(fill=tk.BOTH, expand=True)
        
        actions_header = tk.Frame(actions_card, bg=COLORS['text_light'], height=60)
        actions_header.pack(fill=tk.X, padx=25, pady=(25, 0))
        actions_header.pack_propagate(False)
        
        actions_title = tk.Label(
            actions_header,
            text="⚡ Quick Actions",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS['text_light'],
            fg=COLORS['darkest'],
            anchor=tk.W
        )
        actions_title.pack(side=tk.LEFT)
        
        actions_content = tk.Frame(actions_card, bg=COLORS['text_light'])
        actions_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Quick action buttons
        quick_actions = [
            ("🌐 Open Google", lambda: self.process_command("open google")),
            ("📺 Open YouTube", lambda: self.process_command("open youtube")),
            ("📰 Get News", lambda: self.process_command("news")),
            ("🎵 List Songs", lambda: self.process_command("list songs")),
        ]
        
        for action_text, action_cmd in quick_actions:
            action_btn = ModernButton(
                actions_content,
                action_text,
                action_cmd,
                width=250,
                height=50,
                bg_color=COLORS['lightest'],
                hover_color=COLORS['lighter'],
                text_color=COLORS['darkest']
            )
            action_btn.pack(fill=tk.X, pady=8)
        
        # Info Card
        info_card = tk.Frame(right_column, bg=COLORS['text_light'], relief=tk.FLAT)
        info_card.pack(fill=tk.X, pady=(15, 0))
        
        info_header = tk.Frame(info_card, bg=COLORS['text_light'], height=50)
        info_header.pack(fill=tk.X, padx=25, pady=(20, 0))
        info_header.pack_propagate(False)
        
        info_title = tk.Label(
            info_header,
            text="ℹ️ Information",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS['text_light'],
            fg=COLORS['darkest'],
            anchor=tk.W
        )
        info_title.pack(side=tk.LEFT)
        
        info_content = tk.Frame(info_card, bg=COLORS['text_light'])
        info_content.pack(fill=tk.X, padx=25, pady=(10, 20))
        
        info_text = tk.Label(
            info_content,
            text="Say 'robin' to activate voice mode.\n\nUse quick actions for common tasks.\n\nType commands in the input field or use voice commands.",
            font=("Segoe UI", 10),
            bg=COLORS['text_light'],
            fg=COLORS['text_muted'],
            justify=tk.LEFT,
            anchor=tk.W
        )
        info_text.pack(fill=tk.X, pady=10)
        
        # Add welcome message
        self.add_to_conversation("Robin", "Initializing... Ready to assist you, Vishrut! 🦇")
        
    def welcome_animation(self):
        """Welcome animation effect"""
        self.update_status("Ready", COLORS['light'], "Say 'robin' to activate")
        
    def update_status(self, status, color, text):
        """Update status indicator with animation"""
        self.status_label.config(text=f"● {status}", fg=color)
        self.status_text.config(text=text)
        self.status_indicator.set_color(color)
        self.root.update()
        
    def add_to_conversation(self, speaker, message):
        """Add message to conversation area with smooth animation"""
        self.conversation_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if speaker == "You":
            tag = "user"
            prefix = f"[{timestamp}] You: "
        else:
            tag = "assistant"
            prefix = f"[{timestamp}] Robin: "
        
        # Insert with tags
        self.conversation_text.insert(tk.END, prefix, tag)
        self.conversation_text.insert(tk.END, f"{message}\n\n", "message")
        
        self.conversation_text.see(tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        
        # Smooth scroll animation
        self.animate_scroll()
        
    def animate_scroll(self):
        """Smooth scroll animation"""
        current = self.conversation_text.yview()[1]
        target = 1.0
        steps = 10
        for i in range(steps + 1):
            pos = current + (target - current) * (i / steps)
            self.root.after(i * 5, lambda p=pos: self.conversation_text.yview_moveto(p))
        
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_history = []
        self.add_to_conversation("Robin", "History cleared. Ready to assist! 🦇")
        
    def toggle_listening(self):
        """Toggle continuous listening mode"""
        self.listening = not self.listening
        if self.listening:
            self.listen_btn_text = "⏸ Stop Listening"
            self.listen_btn.update_text(self.listen_btn_text)
            self.listen_btn.update_color(COLORS['dark'], COLORS['medium_dark'])
            self.update_status("Listening", COLORS['medium'], "Listening for wake word 'robin'...")
        else:
            self.listen_btn_text = "🎤 Start Listening"
            self.listen_btn.update_text(self.listen_btn_text)
            self.listen_btn.update_color(COLORS['medium'], COLORS['medium_light'])
            self.update_status("Ready", COLORS['light'], "Say 'robin' to activate")
            
    def stop_assistant(self):
        """Stop the assistant"""
        self.listening = False
        self.listen_btn_text = "🎤 Start Listening"
        self.listen_btn.update_text(self.listen_btn_text)
        self.listen_btn.update_color(COLORS['medium'], COLORS['medium_light'])
        self.update_status("Stopped", COLORS['dark'], "Assistant stopped")
        self.speak("Goodbye Vishrut!", update_ui=False)
        self.add_to_conversation("Robin", "Goodbye Vishrut! 🦇")
        
    def speak(self, text, update_ui=True):
        """Text to speech with UI updates"""
        if update_ui:
            self.update_status("Speaking", COLORS['medium'], f"Speaking: {text[:50]}...")
            self.speaking = True
            
        try:
            # Generate TTS MP3
            tts = gTTS(text)
            tts.save("temp.mp3")
            
            # Load and speed up using pydub
            sound = AudioSegment.from_file("temp.mp3")
            faster_sound = sound.speedup(playback_speed=1.3)
            
            # Save the faster audio
            faster_sound.export("fast_temp.mp3", format="mp3")
            
            # Play the faster audio
            pygame.mixer.music.load("fast_temp.mp3")
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                self.root.update()
            
            # Cleanup
            pygame.mixer.music.unload()
            os.remove("temp.mp3")
            os.remove("fast_temp.mp3")
            
        except Exception as e:
            print(f"Error in speak: {e}")
        finally:
            if update_ui:
                self.speaking = False
                if self.listening:
                    self.update_status("Listening", COLORS['medium'], "Listening for wake word 'robin'...")
                else:
                    self.update_status("Ready", COLORS['light'], "Say 'robin' to activate")
    
    def ai_process(self, command):
        """Process command with OpenAI"""
        try:
            if OPENAI_API_KEY == "<yourapikey>":
                return "Please configure your OpenAI API key in the code."
                
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a virtual assistant named robin skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
                    {"role": "user", "content": command}
                ]
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error processing AI request: {str(e)}"
    
    def process_command(self, command):
        """Process user command"""
        if not command or command.strip() == "":
            return
            
        self.add_to_conversation("You", command)
        self.update_status("Processing", COLORS['medium'], f"Processing: {command[:50]}...")
        self.processing = True
        
        try:
            command_lower = command.lower()
            
            # Website navigation
            if "open google" in command_lower:
                webbrowser.open("https://google.com")
                response = "Opening Google..."
                
            elif "open facebook" in command_lower:
                webbrowser.open("https://facebook.com")
                response = "Opening Facebook..."
                
            elif "open youtube" in command_lower:
                webbrowser.open("https://youtube.com")
                response = "Opening YouTube..."
                
            elif "open linkedin" in command_lower:
                webbrowser.open("https://linkedin.com")
                response = "Opening LinkedIn..."
                
            # Music playback
            elif command_lower.startswith("play"):
                try:
                    parts = command_lower.split(" ", 1)
                    song = parts[1] if len(parts) > 1 else ""
                    if song and song in musicLibrary.music:
                        link = musicLibrary.music[song]
                        webbrowser.open(link)
                        response = f"Playing {song}... 🎵"
                    elif song:
                        # Try to find similar song names
                        available = list(musicLibrary.music.keys())
                        similar = [s for s in available if song.lower() in s.lower() or s.lower() in song.lower()]
                        if similar:
                            response = f"Song '{song}' not found. Did you mean: {', '.join(similar[:3])}?"
                        else:
                            response = f"Song '{song}' not found. Available songs: {', '.join(available[:10])}..."
                    else:
                        response = "Please specify a song name. Example: 'play blue eyes'"
                except Exception as e:
                    response = f"Error playing music: {str(e)}"
            
            # List available songs
            elif "list songs" in command_lower or "available songs" in command_lower or "songs" in command_lower:
                available = list(musicLibrary.music.keys())
                response = f"Available songs ({len(available)}): {', '.join(available[:15])}"
                if len(available) > 15:
                    response += f" and {len(available) - 15} more..."
            
            # Apology
            elif "mistake" in command_lower:
                response = "I am sorry, I will make it up to you"
                
            # News
            elif "news" in command_lower:
                try:
                    r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}")
                    if r.status_code == 200:
                        data = r.json()
                        articles = data.get('articles', [])[:5]  # Limit to 5 articles
                        headlines = [article['title'] for article in articles if article.get('title')]
                        response = "Here are the top headlines:\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
                    else:
                        response = "Could not fetch news at this time."
                except Exception as e:
                    response = f"Error fetching news: {str(e)}"
            
            # Stop command
            elif command_lower == "stop":
                self.stop_assistant()
                return
                
            # AI fallback
            else:
                response = self.ai_process(command)
            
            # Display and speak response
            self.add_to_conversation("Robin", response)
            self.speak(response)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.add_to_conversation("Robin", error_msg)
            self.update_status("Error", COLORS['dark'], error_msg)
        finally:
            self.processing = False
    
    def process_text_command(self):
        """Process command from text input"""
        command = self.command_entry.get().strip()
        if command:
            self.command_entry.delete(0, tk.END)
            threading.Thread(target=self.process_command, args=(command,), daemon=True).start()
    
    def listen_for_wake_word(self):
        """Listen for wake word in a separate thread"""
        r = sr.Recognizer()
        
        while True:
            if self.listening:
                try:
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source, duration=0.5)
                        audio = r.listen(source, timeout=1, phrase_time_limit=1)
                    
                    word = r.recognize_google(audio).lower()
                    
                    if word == "robin":
                        self.root.after(0, self.activate_assistant)
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    if self.listening:
                        print(f"Error in wake word detection: {e}")
                    continue
            else:
                import time
                time.sleep(0.5)
    
    def activate_assistant(self):
        """Activate assistant after wake word"""
        self.update_status("Active", COLORS['medium'], "Listening for your command...")
        self.speak("Hi Vishrut! How can I assist you?", update_ui=False)
        self.add_to_conversation("Robin", "Hi Vishrut! How can I assist you? 🦇")
        
        # Listen for command
        threading.Thread(target=self.listen_for_command, daemon=True).start()
    
    def listen_for_command(self):
        """Listen for user command"""
        r = sr.Recognizer()
        
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                self.root.after(0, lambda: self.update_status("Listening", COLORS['medium'], "Listening for command..."))
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
            
            command = r.recognize_google(audio)
            self.root.after(0, lambda: self.process_command(command))
            
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.update_status("Ready", COLORS['light'], "Timeout. Say 'robin' to activate"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.update_status("Ready", COLORS['light'], "Could not understand. Say 'robin' to activate"))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status("Error", COLORS['dark'], error_msg))
    
    def start_listening_thread(self):
        """Start the wake word listening thread"""
        thread = threading.Thread(target=self.listen_for_wake_word, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = RobinGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
