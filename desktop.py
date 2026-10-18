"""
Dead-State Pruner: Native Desktop Application Launcher
College TAE Project - Theory of Automata and Formal Languages

Uses native Microsoft Edge WebView2 (Chromium) via pywebview.
Runs the Flask backend in a background thread and opens a sleek,
frameless-ready native desktop window.
"""

import sys
import os
import time
import socket
import threading
import webview

# Adjust working directory so bundled PyInstaller assets resolve properly
if getattr(sys, 'frozen', False):
    # Running as compiled PyInstaller executable
    base_dir = sys._MEIPASS
    os.chdir(base_dir)
else:
    # Running in normal Python script mode
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

from app import app


def find_available_port(default_port=5000):
    """Finds an available local port, trying default_port first."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', default_port))
        s.close()
        return default_port
    except OSError:
        # Port 5000 is occupied, pick an ephemeral free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        free_port = s.getsockname()[1]
        s.close()
        return free_port


def run_flask(port):
    """Starts the Flask server in background daemon thread."""
    # Run with reloader and debug disabled for clean desktop execution
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def main():
    port = find_available_port()
    
    # Start Flask in daemon thread so it automatically terminates when window closes
    server_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    server_thread.start()

    # Give server a brief moment to initialize
    time.sleep(0.4)

    # Create native desktop window
    window = webview.create_window(
        title="Dead-State Pruner | DFA Optimization & State Pruning Engine",
        url=f"http://127.0.0.1:{port}",
        width=1340,
        height=880,
        min_size=(980, 660),
        text_select=True,
        zoomable=True
    )

    # Launch native desktop app loop (Edge Chromium WebView2 on Windows)
    webview.start(gui='edgechromium', debug=False)


if __name__ == '__main__':
    main()
