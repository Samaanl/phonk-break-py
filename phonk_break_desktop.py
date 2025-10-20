#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
🎵 PHONK BREAK - Desktop Edition
═══════════════════════════════════════════════════════════════
A Python script that delivers random phonk moments with vintage
vibes directly to your desktop - works ANYWHERE, not just browser!

Features:
- Full-screen overlay with VHS aesthetic
- Random phonk track selection
- Customizable intervals
- Runs in background
- System-wide (affects entire screen)
- Cross-platform (Windows, Mac, Linux)
═══════════════════════════════════════════════════════════════
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pygame
import numpy as np
import random
import time
import threading
import os
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 🎛️ Configuration
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'PHONK_DURATION_MIN': 6,  # Minimum seconds for phonk moment
    'PHONK_DURATION_MAX': 10,  # Maximum seconds for phonk moment
    'BASE_INTERVAL': 45,  # seconds between breaks
    'INTERVAL_VARIANCE': 10,  # ±seconds randomness
    'VOLUME': 0.7,  # 70% volume
    'FADE_IN_DURATION': 0.15,  # seconds (super fast!)
    'FADE_OUT_DURATION': 1.2,  # seconds
    'BEAT_REACTION_INTENSITY': 0.3,  # How much overlay reacts to beats
    'BEAT_DETECTION_THRESHOLD': 0.6,  # Audio level threshold for beat detection
    'SHAKE_INTENSITY': 5,  # Base shake amount (pixels)
    'BEAT_SHAKE_MULTIPLIER': 3,  # How much more shake on beat
}

# ═══════════════════════════════════════════════════════════════
# 🌐 Global State
# ═══════════════════════════════════════════════════════════════

class PhonkBreakState:
    def __init__(self):
        self.phonk_mode_active = False
        self.is_phonk_moment_active = False
        self.overlay_window = None
        self.audio_tracks = []
        self.current_thread = None
        self.stop_event = threading.Event()
        self.beat_reaction_active = False
        self.current_opacity = 0.85
        self.sticker_image = None
        
state = PhonkBreakState()

# ═══════════════════════════════════════════════════════════════
# 🎵 Audio System
# ═══════════════════════════════════════════════════════════════

def initialize_audio():
    """Initialize pygame mixer for audio playback"""
    try:
        pygame.mixer.init()
        print("✅ Audio system initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize audio: {e}")
        return False

def load_audio_tracks():
    """Load all phonk MP3 files from audio directory"""
    audio_dir = Path(__file__).parent / 'audio'
    
    if not audio_dir.exists():
        print(f"⚠️ Audio directory not found: {audio_dir}")
        print("📁 Creating audio directory...")
        audio_dir.mkdir(exist_ok=True)
        print("🎵 Please add phonk1.mp3 through phonk5.mp3 to the 'audio' folder!")
        return []
    
    tracks = []
    for i in range(1, 6):  # phonk1.mp3 to phonk5.mp3
        track_path = audio_dir / f'phonk{i}.mp3'
        if track_path.exists():
            tracks.append(str(track_path))
            print(f"✅ Loaded: phonk{i}.mp3")
        else:
            print(f"⚠️ Missing: phonk{i}.mp3")
    
    if not tracks:
        print("❌ No audio tracks found!")
        print("🎵 Add phonk1.mp3 - phonk5.mp3 to the 'audio' folder")
    
    return tracks

def play_phonk_track(track_path):
    """Play a specific phonk track"""
    try:
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.set_volume(CONFIG['VOLUME'])
        pygame.mixer.music.play()
        print(f"🎵 Playing: {Path(track_path).name}")
        return True
    except Exception as e:
        print(f"❌ Error playing track: {e}")
        return False

def stop_audio():
    """Stop currently playing audio"""
    try:
        pygame.mixer.music.fadeout(int(CONFIG['FADE_OUT_DURATION'] * 1000))
    except:
        pass

# ═══════════════════════════════════════════════════════════════
# 🎨 Overlay Window
# ═══════════════════════════════════════════════════════════════

def load_sticker():
    """Load the sticker.png image"""
    try:
        # Try multiple paths to find sticker.png
        possible_paths = [
            Path(__file__).parent / 'sticker.png',  # Same directory as script
            Path.cwd() / 'sticker.png',  # Current working directory
            Path(__file__).resolve().parent / 'sticker.png',  # Absolute path
        ]
        
        sticker_path = None
        for path in possible_paths:
            if path.exists():
                sticker_path = path
                break
        
        if sticker_path:
            print(f"📍 Found sticker at: {sticker_path}")
            img = Image.open(sticker_path)
            # Resize to reasonable size (keep aspect ratio)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            print(f"⚠️ sticker.png not found. Searched in:")
            for path in possible_paths:
                print(f"   - {path}")
            return None
    except Exception as e:
        print(f"⚠️ Could not load sticker: {e}")
        return None

def create_overlay():
    """Create full-screen overlay with vintage aesthetic"""
    overlay = tk.Toplevel()
    
    # Full screen, always on top
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-topmost', True)
    overlay.attributes('-alpha', 0.0)  # Start invisible
    
    # Remove window decorations
    overlay.overrideredirect(True)
    
    # Black background
    overlay.configure(bg='black')
    
    # Create main container
    container = tk.Frame(overlay, bg='black')
    container.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    # Add vintage vignette overlay using canvas
    canvas = tk.Canvas(container, bg='black', highlightthickness=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)
    
    # Get screen dimensions
    width = overlay.winfo_screenwidth()
    height = overlay.winfo_screenheight()
    
    # Create radial vignette effect (darker at edges)
    center_x = width // 2
    center_y = height // 2
    max_radius = max(width, height)
    
    # Draw concentric rectangles for vignette (simpler approach)
    vignette_layers = 100
    for i in range(vignette_layers):
        progress = i / vignette_layers
        # Darker at edges (0), transparent at center (1)
        darkness = int(80 * (1 - progress))
        color = f'#{darkness:02x}{darkness:02x}{darkness:02x}'
        
        # Calculate rectangle size
        margin = int((max_radius * 0.4) * progress)
        canvas.create_rectangle(
            margin, margin, 
            width - margin, height - margin,
            outline=color, width=2, fill=''
        )
    
    # Add sticker directly on canvas (supports transparency properly)
    sticker_canvas_id = None
    if state.sticker_image:
        # Place sticker at bottom center on the canvas
        sticker_x = center_x
        sticker_y = int(height * 0.85)
        sticker_canvas_id = canvas.create_image(sticker_x, sticker_y, image=state.sticker_image, anchor='center')
    
    # Store references
    overlay.canvas = canvas
    overlay.container = container
    overlay.sticker_canvas_id = sticker_canvas_id
    overlay.sticker_base_x = center_x if state.sticker_image else 0
    overlay.sticker_base_y = int(height * 0.85) if state.sticker_image else 0
    overlay.shake_offset = 0
    
    return overlay

def get_audio_level():
    """Get current audio output level (simulated beat detection)"""
    try:
        if pygame.mixer.music.get_busy():
            # Get music position to simulate beat detection
            pos = pygame.mixer.music.get_pos()
            # Simulate beat pattern (roughly every 500ms for phonk)
            beat_cycle = pos % 500
            if beat_cycle < 50:  # Beat hit
                return 1.0
            else:
                return 0.3 + random.uniform(0, 0.2)
        return 0
    except:
        return 0

def beat_reaction_loop(overlay):
    """Aggressive fast shake animation for sticker"""
    shake_speed = 60  # Much faster shake set at 0.2
    
    while state.beat_reaction_active:
        try:
            # Fast aggressive up/down shake using sine wave
            overlay.shake_offset += shake_speed
            shake_y = int(3 * np.sin(overlay.shake_offset))  # Smaller area (3 pixels), but faster movement = more aggressive
            
            # Apply shake to sticker on canvas (no black box!)
            if overlay.sticker_canvas_id:
                try:
                    new_y = overlay.sticker_base_y + shake_y
                    overlay.canvas.coords(overlay.sticker_canvas_id, overlay.sticker_base_x, new_y)
                except:
                    pass
            
            # Smooth animation
            time.sleep(0.03)  # ~33 FPS for smoother/faster movement
            
        except Exception as e:
            print(f"⚠️ Animation error: {e}")
            break
    
    print("🛑 Animation stopped")

def fade_in_overlay(overlay):
    """Fade in the overlay super fast"""
    steps = 5
    duration = CONFIG['FADE_IN_DURATION']
    step_time = duration / steps
    
    for i in range(steps + 1):
        alpha = 0.85 * (i / steps)  # Max 85% opacity
        overlay.attributes('-alpha', alpha)
        time.sleep(step_time)
    
    state.current_opacity = 0.85

def fade_out_overlay(overlay):
    """Instant fade out - no animation, just disappear"""
    overlay.attributes('-alpha', 0.0)
    state.current_opacity = 0

# ═══════════════════════════════════════════════════════════════
# 🎬 Phonk Moment Logic
# ═══════════════════════════════════════════════════════════════

def trigger_phonk_moment():
    """Execute a single phonk moment with beat-reactive overlay"""
    if state.is_phonk_moment_active or not state.phonk_mode_active:
        return
    
    state.is_phonk_moment_active = True
    
    beat_thread = None
    
    try:
        # Select random track
        if not state.audio_tracks:
            print("⚠️ No audio tracks available")
            state.is_phonk_moment_active = False
            return
        
        track = random.choice(state.audio_tracks)
        
        # Select random duration between 3-6 seconds
        duration = random.uniform(CONFIG['PHONK_DURATION_MIN'], CONFIG['PHONK_DURATION_MAX'])
        print(f"🎬 PHONK MOMENT INCOMING! (Duration: {duration:.1f}s)")
        
        # Create overlay
        overlay = create_overlay()
        
        # Fade in (super fast)
        fade_in_overlay(overlay)
        
        # Play audio
        play_phonk_track(track)
        
        # Start beat reaction in background thread
        state.beat_reaction_active = True
        beat_thread = threading.Thread(target=beat_reaction_loop, args=(overlay,), daemon=True)
        beat_thread.start()
        
        # Wait for random phonk duration (3-6 seconds)
        time.sleep(duration)
        
        # Stop beat reaction
        state.beat_reaction_active = False
        
        # Fade out
        fade_out_overlay(overlay)
        
        # Stop audio
        stop_audio()
        
        # Destroy overlay
        overlay.destroy()
        
    except Exception as e:
        print(f"❌ Error during phonk moment: {e}")
    
    finally:
        state.beat_reaction_active = False
        state.is_phonk_moment_active = False
        print("✅ Phonk moment ended")

def phonk_loop():
    """Main loop that triggers phonk breaks at random intervals"""
    print("🎵 Phonk loop started!")
    
    while state.phonk_mode_active and not state.stop_event.is_set():
        # Calculate random interval
        variance = random.uniform(-CONFIG['INTERVAL_VARIANCE'], CONFIG['INTERVAL_VARIANCE'])
        interval = CONFIG['BASE_INTERVAL'] + variance
        
        print(f"⏰ Next phonk break in {int(interval)} seconds...")
        
        # Wait for the interval (check every second for stop event)
        for _ in range(int(interval)):
            if not state.phonk_mode_active or state.stop_event.is_set():
                print("🛑 Phonk loop stopped")
                return
            time.sleep(1)
        
        # Trigger phonk moment
        if state.phonk_mode_active and not state.stop_event.is_set():
            trigger_phonk_moment()
    
    print("🛑 Phonk loop ended")

# ═══════════════════════════════════════════════════════════════
# 🎛️ Control GUI
# ═══════════════════════════════════════════════════════════════

def create_control_window():
    """Create main control window"""
    root = tk.Tk()
    root.title("🎵 Phonk Break - Desktop Edition")
    root.geometry("400x350")
    root.configure(bg='#1a1a2e')
    
    # Style
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Arial', 12), padding=10)
    style.configure('TLabel', background='#1a1a2e', foreground='white', font=('Arial', 11))
    style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
    
    # Title
    title_frame = tk.Frame(root, bg='#1a1a2e')
    title_frame.pack(pady=20)
    
    title = ttk.Label(title_frame, text="🎵 PHONK BREAK", style='Title.TLabel')
    title.pack()
    
    subtitle = ttk.Label(title_frame, text="Desktop Edition", font=('Arial', 9, 'italic'))
    subtitle.pack()
    
    # Status
    status_frame = tk.Frame(root, bg='#2a2a4e', bd=2, relief='solid')
    status_frame.pack(pady=10, padx=20, fill='x')
    
    status_label = ttk.Label(status_frame, text="Status:", font=('Arial', 10, 'bold'))
    status_label.pack(side='left', padx=10, pady=10)
    
    status_value = ttk.Label(status_frame, text="OFF", foreground='#ff4444')
    status_value.pack(side='left', padx=10, pady=10)
    
    # Toggle button
    def toggle_phonk():
        if state.phonk_mode_active:
            # Stop phonk mode
            state.phonk_mode_active = False
            state.stop_event.set()
            toggle_btn.config(text="▶️  Start Vibing")
            status_value.config(text="OFF", foreground='#ff4444')
            print("🛑 Phonk mode STOPPED")
        else:
            # Start phonk mode
            if not state.audio_tracks:
                status_value.config(text="NO AUDIO!", foreground='#ff8800')
                print("❌ Cannot start - no audio tracks found!")
                return
            
            state.phonk_mode_active = True
            state.stop_event.clear()
            toggle_btn.config(text="⏸️  Stop Vibing")
            status_value.config(text="ON", foreground='#44ff44')
            print("🎵 Phonk mode STARTED")
            
            # Start phonk loop in background thread
            state.current_thread = threading.Thread(target=phonk_loop, daemon=True)
            state.current_thread.start()
    
    toggle_btn = tk.Button(
        root,
        text="▶️  Start Vibing",
        font=('Arial', 14, 'bold'),
        bg='#9333ea',
        fg='white',
        activebackground='#7c3aed',
        activeforeground='white',
        bd=0,
        padx=20,
        pady=15,
        cursor='hand2',
        command=toggle_phonk
    )
    toggle_btn.pack(pady=20)
    
    # Settings
    settings_frame = tk.Frame(root, bg='#1a1a2e')
    settings_frame.pack(pady=10, padx=20, fill='x')
    
    # Interval slider
    interval_label = ttk.Label(settings_frame, text=f"Interval: {CONFIG['BASE_INTERVAL']}s")
    interval_label.pack(anchor='w')
    
    def update_interval(val):
        CONFIG['BASE_INTERVAL'] = int(float(val))
        interval_label.config(text=f"Interval: {CONFIG['BASE_INTERVAL']}s")
    
    interval_slider = tk.Scale(
        settings_frame,
        from_=10,
        to=90,
        orient='horizontal',
        bg='#1a1a2e',
        fg='white',
        troughcolor='#2a2a4e',
        highlightthickness=0,
        command=update_interval
    )
    interval_slider.set(CONFIG['BASE_INTERVAL'])
    interval_slider.pack(fill='x', pady=5)
    
    # Volume slider
    volume_label = ttk.Label(settings_frame, text=f"Volume: {int(CONFIG['VOLUME']*100)}%")
    volume_label.pack(anchor='w', pady=(10, 0))
    
    def update_volume(val):
        CONFIG['VOLUME'] = float(val) / 100
        volume_label.config(text=f"Volume: {int(CONFIG['VOLUME']*100)}%")
        try:
            pygame.mixer.music.set_volume(CONFIG['VOLUME'])
        except:
            pass
    
    volume_slider = tk.Scale(
        settings_frame,
        from_=0,
        to=100,
        orient='horizontal',
        bg='#1a1a2e',
        fg='white',
        troughcolor='#2a2a4e',
        highlightthickness=0,
        command=update_volume
    )
    volume_slider.set(int(CONFIG['VOLUME'] * 100))
    volume_slider.pack(fill='x', pady=5)
    
    # Footer
    footer = ttk.Label(
        root,
        text="aesthetic chaos on demand",
        font=('Arial', 8, 'italic'),
        foreground='#666688'
    )
    footer.pack(side='bottom', pady=10)
    
    # Cleanup on close
    def on_closing():
        state.phonk_mode_active = False
        state.stop_event.set()
        stop_audio()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    return root

# ═══════════════════════════════════════════════════════════════
# 🚀 Main Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    print("═══════════════════════════════════════════════════════")
    print("🎵 PHONK BREAK - Desktop Edition")
    print("═══════════════════════════════════════════════════════")
    print()
    
    # Initialize audio
    if not initialize_audio():
        print("❌ Cannot start without audio system!")
        input("Press Enter to exit...")
        return
    
    # Load audio tracks
    state.audio_tracks = load_audio_tracks()
    
    if not state.audio_tracks:
        print()
        print("⚠️ WARNING: No audio tracks found!")
        print("📁 Please add phonk1.mp3 through phonk5.mp3 to the 'audio' folder")
        print("🎵 The overlay will still work, but there will be no sound")
        print()
    else:
        print(f"✅ Loaded {len(state.audio_tracks)} phonk tracks")
        print()
    
    # Create GUI first (needed for PhotoImage)
    root = create_control_window()
    
    # NOW load sticker (after Tk root window exists)
    state.sticker_image = load_sticker()
    if state.sticker_image:
        print("✅ Loaded sticker.png")
    else:
        print("⚠️ sticker.png not found (continuing without sticker)")
    print()
    
    # Run GUI
    root.mainloop()
    
    print("👋 Phonk Break closed. Stay vibing!")

if __name__ == "__main__":
    main()
