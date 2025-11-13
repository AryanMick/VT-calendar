#!/usr/bin/env python3
"""
VT Calendar Startup Script
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting VT Calendar Application...")
    print()
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    
    # Determine activation script based on OS
    if sys.platform == 'win32':
        activate_script = 'venv\\Scripts\\activate'
        pip = 'venv\\Scripts\\pip'
        python = 'venv\\Scripts\\python'
    else:
        activate_script = 'venv/bin/activate'
        pip = 'venv/bin/pip'
        python = 'venv/bin/python'
    
    print("📦 Installing dependencies...")
    subprocess.run([pip, 'install', '-r', 'requirements.txt'])
    
    print()
    print("🌐 Starting server on http://127.0.0.1:3001")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Start the Flask app
    os.environ['HOST'] = '127.0.0.1'
    os.environ['PORT'] = '3001'
    subprocess.run([python, 'app.py'])

if __name__ == '__main__':
    main()

