#!/usr/bin/env python3
"""
Startup script to run both frontend and backend servers.
This allows access to the exam system from any device on the local network.
"""

import os
import sys
import subprocess
import socket
import webbrowser
import time
from threading import Thread

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket that connects to a public address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_backend(port=8000):
    """Run the backend server"""
    # Check if the port is already in use
    if check_port_in_use(port):
        print(f"⚠️  Warning: Port {port} is already in use!")
        print(f"   This could mean the backend server is already running,")
        print(f"   or another application is using this port.")
        
        # Try to find an alternative port
        alt_port = None
        for test_port in range(8001, 8020):
            if not check_port_in_use(test_port):
                alt_port = test_port
                break
        
        if alt_port:
            print(f"   Attempting to use alternative port: {alt_port}")
            port = alt_port
        else:
            print(f"   Could not find an available port. Please manually stop the process using port {port}.")
            print(f"   Try running: lsof -i :{port}")
            print(f"   Then: kill <PID>")
            return False
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, "backend")
    
    # Change to the backend directory
    os.chdir(backend_dir)
    
    # Modify app.py to use the new port
    app_path = os.path.join(backend_dir, "app.py")
    with open(app_path, "r") as f:
        content = f.read()
    
    # Update the port in app.py
    if "port=8000" in content:
        content = content.replace("port=8000", f"port={port}")
        with open(app_path, "w") as f:
            f.write(content)
    
    # Run the backend server
    print(f"Starting backend server on port {port}...")
    # On Windows use 'python' instead of 'python3'
    python_cmd = 'python3' if sys.platform != 'win32' else 'python'
    
    try:
        subprocess.run([python_cmd, "app.py"])
        return True
    except KeyboardInterrupt:
        print("Backend server stopped.")
        return False

def run_frontend(port=8080):
    """Run a simple HTTP server for the frontend"""
    # Check if port is already in use
    if check_port_in_use(port):
        print(f"⚠️  Warning: Port {port} is already in use!")
        print(f"   Attempting to use an alternative port...")
        
        # Find an available port
        for test_port in range(port+1, port+20):
            if not check_port_in_use(test_port):
                port = test_port
                print(f"   Using port {port} instead.")
                break
        else:
            print(f"   Could not find an available port. Please manually stop the process using port {port}.")
            print(f"   Try running: lsof -i :{port}")
            print(f"   Then: kill <PID>")
            return False
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(script_dir, "frontend")
    
    # Change to the frontend directory
    os.chdir(frontend_dir)
    
    # Run the frontend server
    print(f"Starting frontend server on port {port}...")
    # On Windows use 'python' instead of 'python3'
    python_cmd = 'python3' if sys.platform != 'win32' else 'python'
    
    try:
        subprocess.run([python_cmd, "-m", "http.server", str(port)])
        return True
    except KeyboardInterrupt:
        print("Frontend server stopped.")
        return False

if __name__ == "__main__":
    # Get the local IP address
    local_ip = get_local_ip()
    
    # Print access information
    print("\n===== Exam System Server =====")
    print(f"Starting servers...\n")
    
    # Choose ports (with fallbacks for conflicts)
    backend_port = 8000
    frontend_port = 8080
    
    if check_port_in_use(backend_port):
        for test_port in range(8001, 8020):
            if not check_port_in_use(test_port):
                backend_port = test_port
                break
    
    if check_port_in_use(frontend_port):
        for test_port in range(8081, 8100):
            if not check_port_in_use(test_port):
                frontend_port = test_port
                break
    
    # Update frontend to use the correct backend port
    script_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(script_dir, "frontend")
    index_path = os.path.join(frontend_dir, "index.html")
    
    try:
        with open(index_path, "r") as f:
            content = f.read()
        
        # Update backend port in the frontend code
        updated = False
        if "return `http://${window.location.hostname}:8000`;" in content:
            content = content.replace(
                "return `http://${window.location.hostname}:8000`;", 
                f"return `http://${{window.location.hostname}}:{backend_port}`;"
            )
            updated = True
        
        if updated:
            with open(index_path, "w") as f:
                f.write(content)
            print(f"Updated frontend to use backend port {backend_port}")
    except Exception as e:
        print(f"Warning: Could not update frontend code: {e}")
    
    # Start the backend server in a separate thread
    backend_thread = Thread(target=run_backend, args=(backend_port,))
    backend_thread.daemon = True
    backend_thread.start()
    
    # Give the backend a moment to start
    time.sleep(2)
    
    # Print access information
    print("\n===== Access Information =====")
    print(f"Local access (this computer):")
    print(f"  Frontend: http://localhost:{frontend_port}")
    print(f"  Backend API: http://localhost:{backend_port}")
    print(f"\nNetwork access (other devices):")
    print(f"  Frontend: http://{local_ip}:{frontend_port}")
    print(f"  Backend API: http://{local_ip}:{backend_port}")
    print("\nUse these URLs to access the exam system from any device on your network")
    print("Press Ctrl+C to stop the servers")
    print("===============================\n")
    
    # Open the browser automatically
    webbrowser.open(f"http://localhost:{frontend_port}")
    
    # Start the frontend server (this will block until stopped)
    run_frontend(frontend_port)