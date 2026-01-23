#!/usr/bin/env python3
"""
Immich Installer for Raspberry Pi OS Desktop
Automatically installs Docker and Immich with user-specified configuration
Zero external dependencies - uses only built-in Python libraries
"""

import sys
import os
import subprocess
import secrets
import string
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


class ImmichInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title('Immich Installer for Raspberry Pi')
        self.root.geometry('750x750')
        self.root.resizable(False, False)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2196F3', height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text='Immich Installer', 
                        font=('Arial', 24, 'bold'), bg='#2196F3', fg='white')
        title.pack(pady=20)
        
        # Main content frame
        main_frame = tk.Frame(self.root, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Description
        desc = tk.Label(main_frame, 
                       text='This installer will automatically set up Immich with Docker on your Raspberry Pi',
                       wraplength=650, justify=tk.CENTER, font=('Arial', 10))
        desc.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Root Password
        tk.Label(main_frame, text='Root/Sudo Password:', 
                font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.root_pass_var = tk.StringVar()
        self.root_pass_entry = tk.Entry(main_frame, textvariable=self.root_pass_var, 
                                       show='*', width=50, font=('Arial', 10))
        self.root_pass_entry.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # Installation Path
        tk.Label(main_frame, text='Installation Path:', 
                font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.install_path_var = tk.StringVar(value='/home/pi/immich')
        self.install_path_entry = tk.Entry(main_frame, textvariable=self.install_path_var, 
                                          width=40, font=('Arial', 10))
        self.install_path_entry.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        
        browse_install_btn = tk.Button(main_frame, text='Browse...', 
                                       command=self.browse_install_path, width=10)
        browse_install_btn.grid(row=4, column=2, padx=(5, 0), pady=(0, 5))
        
        # Photos Path
        tk.Label(main_frame, text='Original Photos Location:', 
                font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.photos_path_var = tk.StringVar(value='/mnt/photos')
        self.photos_path_entry = tk.Entry(main_frame, textvariable=self.photos_path_var, 
                                         width=40, font=('Arial', 10))
        self.photos_path_entry.grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        
        browse_photos_btn = tk.Button(main_frame, text='Browse...', 
                                      command=self.browse_photos_path, width=10)
        browse_photos_btn.grid(row=6, column=2, padx=(5, 0), pady=(0, 5))
        
        # External Library Path
        tk.Label(main_frame, text='External Library Path:', 
                font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.external_path_var = tk.StringVar(value='/mnt/external-hdd')
        self.external_path_entry = tk.Entry(main_frame, textvariable=self.external_path_var, 
                                           width=40, font=('Arial', 10))
        self.external_path_entry.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        
        browse_external_btn = tk.Button(main_frame, text='Browse...', 
                                        command=self.browse_external_path, width=10)
        browse_external_btn.grid(row=8, column=2, padx=(5, 0), pady=(0, 5))
        
        # Checkbox to stop existing Immich instances
        self.stop_existing_var = tk.BooleanVar(value=True)
        stop_existing_check = tk.Checkbutton(
            main_frame, 
            text='Stop existing Immich instances to avoid port conflicts',
            variable=self.stop_existing_var,
            font=('Arial', 10)
        )
        stop_existing_check.grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        # Info label for checkbox
        info_label = tk.Label(
            main_frame,
            text='(Recommended: Checks for running Immich containers and stops them before installation)',
            font=('Arial', 8),
            fg='#666666',
            wraplength=650,
            justify=tk.LEFT
        )
        info_label.grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        # Install Button
        self.install_btn = tk.Button(main_frame, text='Install Immich', 
                                     command=self.start_installation,
                                     bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'),
                                     height=2, cursor='hand2')
        self.install_btn.grid(row=11, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(10, 15))
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=12, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # Log Output
        tk.Label(main_frame, text='Installation Log:', 
                font=('Arial', 10, 'bold')).grid(row=13, column=0, sticky=tk.W, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=80, 
                                                  font=('Courier', 9), state=tk.DISABLED)
        self.log_text.grid(row=14, column=0, columnspan=3, sticky=tk.W+tk.E)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def browse_install_path(self):
        path = filedialog.askdirectory(title='Select Installation Directory')
        if path:
            self.install_path_var.set(path)
    
    def browse_photos_path(self):
        path = filedialog.askdirectory(title='Select Photos Directory')
        if path:
            self.photos_path_var.set(path)
    
    def browse_external_path(self):
        path = filedialog.askdirectory(title='Select External Library Directory')
        if path:
            self.external_path_var.set(path)
    
    def log(self, message):
        """Add message to log output"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def validate_inputs(self):
        """Validate all input fields"""
        if not self.root_pass_var.get():
            messagebox.showerror('Missing Input', 'Please enter your root/sudo password')
            return False
        
        if not self.install_path_var.get():
            messagebox.showerror('Missing Input', 'Please specify the installation path')
            return False
        
        if not self.photos_path_var.get():
            messagebox.showerror('Missing Input', 'Please specify the photos location')
            return False
        
        if not self.external_path_var.get():
            messagebox.showerror('Missing Input', 'Please specify the external library path')
            return False
        
        # Check if paths exist
        if not Path(self.photos_path_var.get()).exists():
            messagebox.showerror('Invalid Path', 'Photos path does not exist')
            return False
        
        if not Path(self.external_path_var.get()).exists():
            messagebox.showerror('Invalid Path', 'External library path does not exist')
            return False
        
        return True
    
    def start_installation(self):
        """Start the installation process in a separate thread"""
        if not self.validate_inputs():
            return
        
        # Disable install button and start progress
        self.install_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Run installation in separate thread to prevent UI freeze
        thread = threading.Thread(target=self.run_installation, daemon=True)
        thread.start()
    
    def run_installation(self):
        """Execute the installation steps"""
        try:
            # Check for existing Immich instances if checkbox is selected
            if self.stop_existing_var.get():
                self.log("Checking for existing Immich instances...")
                if not self.stop_existing_immich():
                    self.installation_complete(False, "Failed to stop existing Immich instances")
                    return
            
            # Check Docker installation
            self.log("Checking Docker installation...")
            if not self.check_docker():
                self.log("Docker not found. Installing Docker...")
                if not self.install_docker():
                    self.installation_complete(False, "Failed to install Docker")
                    return
            else:
                self.log("Docker is already installed and running")
            
            # Create installation directory
            install_path = Path(self.install_path_var.get())
            self.log(f"Creating installation directory: {install_path}")
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Generate credentials
            self.log("Generating secure database credentials...")
            db_password = self.generate_password()
            db_username = "immich"
            db_name = "immich"
            
            # Create docker-compose.yml
            self.log("Creating docker-compose.yml...")
            compose_content = self.create_docker_compose(
                install_path,
                Path(self.photos_path_var.get()),
                Path(self.external_path_var.get()),
                db_username, db_password, db_name
            )
            compose_file = install_path / "docker-compose.yml"
            compose_file.write_text(compose_content)
            self.log(f"Created: {compose_file}")
            
            # Create .env file
            self.log("Creating .env file...")
            env_content = self.create_env_file(install_path, db_username, db_password, db_name)
            env_file = install_path / ".env"
            env_file.write_text(env_content)
            self.log(f"Created: {env_file}")
            
            # Start Immich
            self.log("Starting Immich containers (this may take a few minutes)...")
            if not self.start_immich(install_path):
                self.installation_complete(False, "Failed to start Immich containers")
                return
            
            self.log("✓ Installation completed successfully!")
            self.installation_complete(True, 
                "Immich is now running!\n\nAccess it at: http://localhost:2283\n\n" +
                f"Configuration saved in: {install_path}")
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.installation_complete(False, f"Installation failed: {str(e)}")
    
    def stop_existing_immich(self):
        """Check for and stop existing Immich instances"""
        try:
            # Check if docker is available
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.log("Docker not installed yet, skipping existing instance check")
                return True
            
            # List all running containers with "immich" in the name
            self.log("Searching for running Immich containers...")
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                self.log("Could not check for existing containers")
                return True
            
            # Find Immich containers
            immich_containers = [
                name for name in result.stdout.strip().split('\n') 
                if name and 'immich' in name.lower()
            ]
            
            if not immich_containers:
                self.log("No existing Immich containers found")
                return True
            
            self.log(f"Found {len(immich_containers)} Immich container(s): {', '.join(immich_containers)}")
            
            # Check for port 2283 usage
            self.log("Checking if port 2283 is in use...")
            port_check = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}: {{.Ports}}'],
                capture_output=True, text=True, timeout=10
            )
            
            port_conflict = False
            if '2283' in port_check.stdout or '0.0.0.0:2283' in port_check.stdout:
                port_conflict = True
                self.log("⚠ Port 2283 is currently in use by a Docker container")
            
            # Stop containers
            for container in immich_containers:
                self.log(f"Stopping container: {container}")
                stop_result = subprocess.run(
                    ['docker', 'stop', container],
                    capture_output=True, text=True, timeout=30
                )
                
                if stop_result.returncode == 0:
                    self.log(f"✓ Stopped: {container}")
                else:
                    self.log(f"⚠ Failed to stop {container}: {stop_result.stderr}")
            
            # Look for docker-compose projects
            self.log("Checking for Immich Docker Compose projects...")
            compose_check = subprocess.run(
                ['docker', 'compose', 'ls', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            
            if compose_check.returncode == 0 and 'immich' in compose_check.stdout.lower():
                self.log("Found Immich Docker Compose project, attempting to stop...")
                
                # Try to find and stop compose projects
                import json
                try:
                    projects = json.loads(compose_check.stdout)
                    for project in projects:
                        if 'immich' in project.get('Name', '').lower():
                            project_path = project.get('ConfigFiles', '')
                            if project_path:
                                project_dir = Path(project_path).parent
                                self.log(f"Found project at: {project_dir}")
                                self.log("Running docker compose down...")
                                
                                compose_down = subprocess.run(
                                    ['docker', 'compose', 'down'],
                                    cwd=project_dir,
                                    capture_output=True, text=True, timeout=60
                                )
                                
                                if compose_down.returncode == 0:
                                    self.log("✓ Successfully stopped Docker Compose project")
                                else:
                                    self.log(f"⚠ Compose down failed: {compose_down.stderr}")
                except json.JSONDecodeError:
                    self.log("Could not parse compose project list")
            
            # Final verification
            self.log("Verifying port 2283 is now free...")
            final_check = subprocess.run(
                ['docker', 'ps', '--format', '{{.Ports}}'],
                capture_output=True, text=True, timeout=10
            )
            
            if '2283' in final_check.stdout:
                self.log("⚠ Warning: Port 2283 may still be in use")
                # Give user option to continue
                response = messagebox.askyesno(
                    'Port Conflict',
                    'Port 2283 appears to still be in use. Continue anyway?'
                )
                return response
            else:
                self.log("✓ Port 2283 is now available")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Timeout while checking for existing instances")
            return False
        except Exception as e:
            self.log(f"Error checking for existing instances: {str(e)}")
            return False
    
    def check_docker(self):
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install_docker(self):
        """Install Docker using the official convenience script"""
        try:
            root_pass = self.root_pass_var.get()
            
            # Download Docker install script using wget (more reliable than curl on Pi)
            self.log("Downloading Docker installation script...")
            download_cmd = ['wget', '-O', '/tmp/get-docker.sh', 'https://get.docker.com']
            result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                # Try with curl as fallback
                self.log("Trying alternative download method...")
                download_cmd = ['curl', '-fsSL', 'https://get.docker.com', '-o', '/tmp/get-docker.sh']
                result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    self.log(f"Failed to download Docker script: {result.stderr}")
                    return False
            
            # Run install script with sudo
            self.log("Running Docker installation script (this may take several minutes)...")
            install_cmd = f'echo {root_pass} | sudo -S sh /tmp/get-docker.sh'
            result = subprocess.run(install_cmd, shell=True, capture_output=True, 
                                  text=True, timeout=600)
            
            if result.returncode != 0:
                self.log(f"Docker installation failed: {result.stderr}")
                return False
            
            # Add current user to docker group
            user = os.getenv('USER', 'pi')
            self.log(f"Adding user '{user}' to docker group...")
            add_user_cmd = f'echo {root_pass} | sudo -S usermod -aG docker {user}'
            subprocess.run(add_user_cmd, shell=True, capture_output=True, text=True)
            
            # Start Docker service
            self.log("Starting Docker service...")
            start_cmd = f'echo {root_pass} | sudo -S systemctl start docker'
            subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
            
            # Enable Docker service
            self.log("Enabling Docker to start on boot...")
            enable_cmd = f'echo {root_pass} | sudo -S systemctl enable docker'
            subprocess.run(enable_cmd, shell=True, capture_output=True, text=True)
            
            self.log("✓ Docker installed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Docker installation timed out")
            return False
        except Exception as e:
            self.log(f"Error installing Docker: {str(e)}")
            return False
    
    def generate_password(self, length=32):
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_docker_compose(self, install_path, photos_path, external_path, 
                             db_user, db_pass, db_name):
        """Create docker-compose.yml content with custom network and volumes"""
        return f"""version: "3.8"

name: immich

networks:
  immich-backend:
    driver: bridge

services:
  immich-server:
    container_name: immich_server
    image: ghcr.io/immich-app/immich-server:release
    command: ["start.sh", "immich"]
    volumes:
      - {install_path}/upload:/usr/src/app/upload
      - {photos_path}:/usr/src/app/library:ro
      - {external_path}:/usr/src/app/external:ro
      - /etc/localtime:/etc/localtime:ro
    env_file:
      - .env
    ports:
      - "2283:3001"
    depends_on:
      - redis
      - database
    restart: always
    networks:
      - immich-backend

  immich-microservices:
    container_name: immich_microservices
    image: ghcr.io/immich-app/immich-server:release
    command: ["start.sh", "microservices"]
    volumes:
      - {install_path}/upload:/usr/src/app/upload
      - {photos_path}:/usr/src/app/library:ro
      - {external_path}:/usr/src/app/external:ro
      - /etc/localtime:/etc/localtime:ro
    env_file:
      - .env
    depends_on:
      - redis
      - database
    restart: always
    networks:
      - immich-backend

  immich-machine-learning:
    container_name: immich_machine_learning
    image: ghcr.io/immich-app/immich-machine-learning:release
    volumes:
      - {install_path}/model-cache:/cache
    env_file:
      - .env
    restart: always
    networks:
      - immich-backend

  redis:
    container_name: immich_redis
    image: redis:6.2-alpine
    restart: always
    networks:
      - immich-backend

  database:
    container_name: immich_postgres
    image: tensorchord/pgvecto-rs:pg14-v0.2.0
    env_file:
      - .env
    environment:
      POSTGRES_PASSWORD: {db_pass}
      POSTGRES_USER: {db_user}
      POSTGRES_DB: {db_name}
    volumes:
      - {install_path}/postgres:/var/lib/postgresql/data
    restart: always
    networks:
      - immich-backend
"""

    def create_env_file(self, install_path, db_user, db_pass, db_name):
        """Create .env file content"""
        return f"""# Database
DB_HOSTNAME=database
DB_USERNAME={db_user}
DB_PASSWORD={db_pass}
DB_DATABASE_NAME={db_name}

# Redis
REDIS_HOSTNAME=redis

# Upload location
UPLOAD_LOCATION={install_path}/upload

# Machine Learning
IMMICH_MACHINE_LEARNING_URL=http://immich-machine-learning:3003

# Other settings
TZ=Europe/Berlin
"""

    def start_immich(self, install_path):
        """Start Immich using docker compose"""
        try:
            os.chdir(install_path)
            result = subprocess.run(['docker', 'compose', 'up', '-d'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.log(f"Failed to start Immich: {result.stderr}")
                return False
            
            self.log("✓ Immich containers started successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Starting Immich timed out")
            return False
        except Exception as e:
            self.log(f"Error starting Immich: {str(e)}")
            return False
    
    def installation_complete(self, success, message):
        """Handle installation completion"""
        self.root.after(0, lambda: self._show_completion(success, message))
    
    def _show_completion(self, success, message):
        """Show completion dialog (must run in main thread)"""
        self.progress.stop()
        self.install_btn.config(state=tk.NORMAL)
        
        if success:
            messagebox.showinfo('Installation Complete', message)
        else:
            messagebox.showerror('Installation Failed', message)


def main():
    root = tk.Tk()
    app = ImmichInstaller(root)
    root.mainloop()


if __name__ == '__main__':
    main()
