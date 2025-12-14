import tkinter as tk
from tkinter import ttk
import websocket
import json
import threading
import requests
from datetime import datetime
from collections import deque
import os

# For candlestick chart
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np

class CryptoTicker:
    """Reusable ticker component for any cryptocurrency."""

    def __init__(self, parent, symbol, display_name, on_select_callback=None):
        self.parent = parent
        self.symbol = symbol.lower()
        self.display_name = display_name
        self.is_active = False
        self.ws = None
        self.on_select_callback = on_select_callback
        self.current_price = 0
        self.price_change = 0
        self.price_change_percent = 0
        self.is_selected = False

        # Create UI frame
        self.frame = tk.Frame(parent, bg="#2d2d2d", relief="flat", bd=1)

        # Make entire frame clickable
        self.frame.bind("<Button-1>", self._on_click)

        # Symbol label
        self.symbol_label = tk.Label(
            self.frame,
            text=display_name,
            font=("Segoe UI", 11, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        self.symbol_label.pack(pady=(8, 2))
        self.symbol_label.bind("<Button-1>", self._on_click)

        # Price label
        self.price_label = tk.Label(
            self.frame,
            text="--,---.--",
            font=("Segoe UI", 16, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        self.price_label.pack(pady=(0, 2))
        self.price_label.bind("<Button-1>", self._on_click)

        # Change label
        self.change_label = tk.Label(
            self.frame,
            text="--",
            font=("Segoe UI", 9),
            bg="#2d2d2d",
            fg="#888888"
        )
        self.change_label.pack(pady=(0, 8))
        self.change_label.bind("<Button-1>", self._on_click)

    def set_selected(self, selected):
        """Update visual selection state."""
        self.is_selected = selected
        bg_color = "#3d5c3d" if selected else "#2d2d2d"
        self.frame.config(bg=bg_color)
        self.symbol_label.config(bg=bg_color)
        self.price_label.config(bg=bg_color)
        self.change_label.config(bg=bg_color)

    def _on_click(self, event=None):
        """Handle click on ticker."""
        if self.on_select_callback:
            self.on_select_callback(self.symbol.upper().replace("USDT", ""))

    def start(self):
        """Start WebSocket connection."""
        if self.is_active:
            return
        self.is_active = True

        ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@ticker"

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=lambda ws, err: print(f"{self.symbol} error: {err}"),
            on_close=lambda ws, s, m: print(f"{self.symbol} closed"),
            on_open=lambda ws: print(f"{self.symbol} connected")
        )

        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def stop(self):
        """Stop WebSocket connection."""
        self.is_active = False
        if self.ws:
            self.ws.close()
            self.ws = None

    def on_message(self, ws, message):
        """Handle price updates."""
        if not self.is_active:
            return

        data = json.loads(message)
        self.current_price = float(data['c'])
        self.price_change = float(data['p'])
        self.price_change_percent = float(data['P'])

        # Schedule GUI update on main thread
        self.parent.after(0, self.update_display)

    def update_display(self):
        """Update the ticker display."""
        if not self.is_active or not self.frame.winfo_exists():
            return

        color = "#00ff88" if self.price_change >= 0 else "#ff4444"

        # Format price based on magnitude
        if self.current_price >= 1000:
            price_text = f"${self.current_price:,.2f}"
        elif self.current_price >= 1:
            price_text = f"${self.current_price:.2f}"
        else:
            price_text = f"${self.current_price:.4f}"

        self.price_label.config(text=price_text, fg=color)

        sign = "+" if self.price_change >= 0 else ""
        change_text = f"{sign}{self.price_change_percent:.2f}%"
        self.change_label.config(text=change_text, fg=color)

        
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def grid_remove(self):
        self.frame.grid_remove()