import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

def apply_modern_style(root):
    """Apply modern styling to the application"""
    # Configure colors with a more vibrant and modern palette
    colors = {
        'primary': '#E6F3FF',  # Extremely light blue
        'secondary': '#F0F8FF',  # Alice blue
        'accent': '#B3E0FF',    # Lighter blue
        'success': '#00c853',   # Bright green
        'warning': '#ffd600',   # Bright yellow
        'danger': '#d50000',    # Bright red
        'light': '#ffffff',     # Pure white
        'dark': '#333333',      # Dark gray for text
        'background': '#ffffff',  # White background
        'surface': '#E6F3FF',   # Extremely light blue surface
        'text': '#333333'       # Dark gray text
    }

    # Configure root window with modern styling
    root.configure(bg=colors['background'])

    # Create custom styles with modern aesthetics
    style = ttk.Style(root)
    style.configure('.',
                    background=colors['background'],
                    foreground=colors['dark'],
                    font=('Segoe UI', 10),  # More modern font
                    relief='flat')
    
    # Add hover effects and transitions
    root.tk_setPalette(background=colors['background'], foreground=colors['dark'])

    # Modern frame styles with subtle elevation
    style.configure('Modern.TFrame',
                    background=colors['surface'])
    style.configure('Modern.TLabelframe',
                    background=colors['surface'])
    style.configure('Modern.TLabelframe.Label',
                    background=colors['surface'],
                    foreground=colors['text'],
                    font=('Inter', 11, 'bold'))

    # Enhanced button styles with improved visibility and contrast
    style.configure('Modern.TButton',
                    background=colors['primary'],
                    foreground='black',
                    padding=(20, 12),
                    font=('Inter', 11, 'bold'),
                    relief='solid',
                    borderwidth=1)
    style.map('Modern.TButton',
              background=[('active', '#4F46E5'),
                         ('pressed', '#3730A3')],
              foreground=[('active', 'black'),
                         ('pressed', 'black')],
              relief=[('pressed', 'sunken')])

    # Modern entry field styling
    style.configure('Modern.TEntry',
                    fieldbackground=colors['surface'],
                    foreground=colors['text'],
                    padding=8,
                    relief='flat',
                    borderwidth=1)

    # Enhanced combobox styling
    style.configure('Modern.TCombobox',
                    fieldbackground=colors['surface'],
                    foreground=colors['text'],
                    padding=8,
                    relief='flat',
                    borderwidth=1)

    # Modern treeview with enhanced visuals
    style.configure('Modern.Treeview',
                    background=colors['surface'],
                    fieldbackground=colors['surface'],
                    foreground=colors['text'],
                    rowheight=30)
    style.configure('Modern.Treeview.Heading',
                    background=colors['primary'],
                    foreground='white',
                    font=('Inter', 10, 'bold'),
                    relief='flat',
                    borderwidth=0)
    style.map('Modern.Treeview',
              background=[('selected', colors['primary'])],
              foreground=[('selected', 'white')])

    # Modern notebook styling with improved visibility
    style.configure('Modern.TNotebook',
                    background=colors['background'],
                    borderwidth=1)
    style.configure('Modern.TNotebook.Tab',
                    background=colors['surface'],
                    foreground=colors['text'],
                    padding=(24, 10),
                    font=('Inter', 11),
                    borderwidth=1)
    style.map('Modern.TNotebook.Tab',
              background=[('selected', colors['primary'])],
              foreground=[('selected', 'white')])

def create_custom_font():
    return {
        'header': tkfont.Font(family='Inter', size=16, weight='bold'),
        'subheader': tkfont.Font(family='Inter', size=14, weight='bold'),
        'body': tkfont.Font(family='Inter', size=11),
        'small': tkfont.Font(family='Inter', size=10)
    }

def style_text_widget(text_widget, bg='#FFFFFF', fg='#1E293B'):
    text_widget.configure(
        bg=bg,
        fg=fg,
        font=('Inter', 11),
        selectbackground='#6366F1',
        selectforeground='white',
        padx=12,
        pady=8,
        relief='flat',
        borderwidth=1,
        insertbackground='#6366F1',  # Cursor color
        insertwidth=2  # Cursor width
    )