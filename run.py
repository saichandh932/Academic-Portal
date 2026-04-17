# -*- coding: utf-8 -*-
"""
run.py
------
Entry-point: python run.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from backend.app    import create_app
from backend.config import Config

if __name__ == "__main__":
    app = create_app()
    print(f"\n[API] Student Performance API starting on http://{Config.HOST}:{Config.PORT}")
    print(f"[API] Debug mode : {Config.DEBUG}\n")
    
    if Config.DEBUG:
        app.run(host=Config.HOST, port=Config.PORT, debug=True)
    else:
        from waitress import serve
        print("[API] Running with production WSGI server (Waitress)")
        serve(app, host=Config.HOST, port=Config.PORT)
