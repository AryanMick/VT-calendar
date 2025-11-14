"""
VT Calendar Startup Script
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting VT Calendar Application...")
    print()
    
    # Resolve paths relative to this script (backend directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(script_dir, 'venv')
    requirements_path = os.path.join(script_dir, 'requirements.txt')
    app_path = os.path.join(script_dir, 'app.py')

    # Check if virtual environment exists
    if not os.path.exists(venv_path):
        print(" Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_path])
    
    #  activation
    if sys.platform == 'win32':
        pip = os.path.join(venv_path, 'Scripts', 'pip')
        python = os.path.join(venv_path, 'Scripts', 'python')
    else:
        pip = os.path.join(venv_path, 'bin', 'pip')
        python = os.path.join(venv_path, 'bin', 'python')
    
    print("📦 Installing dependencies...")
    subprocess.run([pip, 'install', '-r', requirements_path])
    
    print()
    print("🌐 Starting server on http://127.0.0.1:3001")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Strat
    os.environ['HOST'] = '127.0.0.1'
    os.environ['PORT'] = '3001'
    subprocess.run([python, app_path])

if __name__ == '__main__':
    main()

