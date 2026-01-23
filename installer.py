#!/usr/bin/env python3
import os
import secrets
import subprocess
import threading
import urllib.request

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ImportError:
    print("ERROR: 'tkinter' is missing. Install with: sudo apt install python3-tk -y")
    exit(1)

DOCKER_COMPOSE = """
name: immich
networks:
  immich_internal: {driver: bridge, internal: true}
  immich_public: {driver: bridge}
services:
  immich-server:
    container_name: immich_server
    image: ghcr.io/immich-app/immich-server:release
    command: ['start.sh', 'immich']
    volumes: ["{photos}:/usr/src/app/upload", "{extlib}:{extlib}:ro", "/etc/localtime:/etc/localtime:ro"]
    env_file: [.env]
    ports: ["2283:2283"]
    depends_on: [redis, database]
    restart: always
    networks: [immich_internal, immich_public]
  immich-machine-learning:
    container_name: immich_machine_learning
    image: ghcr.io/immich-app/immich-machine-learning:release
    volumes: [model-cache:/cache]
    env_file: [.env]
    restart: always
    networks: [immich_internal]
  redis:
    container_name: immich_redis
    image: redis:6.2-alpine
    restart: always
    networks: [immich_internal]
  database:
    container_name: immich_postgres
    image: tensorchord/pgvecto-rs:pg14-v0.2.0
    environment: {{POSTGRES_PASSWORD: "{dbpass}", POSTGRES_USER: postgres, POSTGRES_DB: immich, POSTGRES_INITDB_ARGS: '--data-checksums'}}
    volumes: ["{install}/postgres:/var/lib/postgresql/data"]
    restart: always
    networks: [immich_internal]
volumes:
  model-cache:
"""

ENV_TEMPLATE = "HOST=0.0.0.0\nUPLOAD_LOCATION={photos}\nIMMICH_MACHINE_LEARNING_URL=http://immich-machine-learning:3003\nDB_PASSWORD={dbpass}\nDB_HOSTNAME=immich_postgres\nDB_USERNAME=postgres\nDB_DATABASE_NAME=immich\nREDIS_HOSTNAME=immich_redis\n"


class ImmichInstaller:
    def __init__(self, root):
        self.root = root
        root.title("Immich Installer for Raspberry Pi")
        root.geometry("600x700")

        self.fields = {
            "Root Password (sudo):": (tk.StringVar(), True, "Required for Docker installation"),
            "Install Location:": (tk.StringVar(), False, "e.g. /home/pi/immich"),
            "Photos Storage:": (tk.StringVar(), False, "e.g. /home/pi/photos"),
            "External Library:": (tk.StringVar(), False, "e.g. /mnt/nas/photos"),
        }
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="Immich Auto-Installer", font=("Arial", 16, "bold")).pack(pady=15)

        for label, (var, is_password, hint) in self.fields.items():
            frame = tk.Frame(self.root)
            frame.pack(fill='x', padx=10, pady=5)
            tk.Label(frame, text=label, width=20, anchor='w').pack(side='left')
            tk.Entry(frame, textvariable=var, show="*" if is_password else "").pack(side='left', fill='x', expand=True)
            if not is_password:
                tk.Button(frame, text="Browse", command=lambda v=var: v.set(filedialog.askdirectory() or v.get())).pack(side='left', padx=5)
            tk.Label(self.root, text=f"   {hint}", fg="gray", font=("Arial", 9)).pack(anchor='w', padx=10)

        self.btn = tk.Button(self.root, text="INSTALL IMMICH", bg="green", fg="white", font=("Arial", 12, "bold"), command=self.start)
        self.btn.pack(pady=20)

        self.log_area = scrolledtext.ScrolledText(self.root, height=15, state='disabled')
        self.log_area.pack(fill='both', expand=True, padx=10, pady=10)

    def log(self, msg):
        self.root.after(0, lambda: (self.log_area.configure(state='normal'), self.log_area.insert(tk.END, f"{msg}\n"), self.log_area.see(tk.END), self.log_area.configure(state='disabled')))

    def run(self, cmd, pw=None, cwd=None, stream=False):
        full_cmd = f"echo '{pw}' | sudo -S {cmd}" if pw else cmd
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
        if stream:
            for line in proc.stdout:
                self.log(line.strip())
        proc.wait()
        if proc.returncode != 0:
            raise Exception(f"Command failed: {cmd}")

    def install(self):
        pw, install, photos, extlib = [v.get() for v, *_ in self.fields.values()]
        if not all([pw, install, photos, extlib]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            self.log("Checking Docker...")
            try:
                self.run("docker --version")
            except:
                self.log("Installing Docker...")
                urllib.request.urlretrieve("https://get.docker.com", "get-docker.sh")
                self.run("sh get-docker.sh", pw)
                os.remove("get-docker.sh")

            self.run(f"usermod -aG docker {os.getenv('USER')}", pw)
            os.makedirs(install, exist_ok=True)

            dbpass = secrets.token_urlsafe(16)
            with open(f"{install}/docker-compose.yml", "w") as f:
                f.write(DOCKER_COMPOSE.format(photos=photos, extlib=extlib, dbpass=dbpass, install=install))
            with open(f"{install}/.env", "w") as f:
                f.write(ENV_TEMPLATE.format(photos=photos, dbpass=dbpass))

            self.log("Pulling images...")
            self.run("docker compose pull", pw, install, stream=True)
            self.log("Starting containers...")
            self.run("docker compose up -d", pw, install, stream=True)

            self.log("SUCCESS! Access at http://<PI_IP>:2283\nReboot to finalize Docker permissions.")
            messagebox.showinfo("Success", "Immich installed! Please reboot.")
        except Exception as e:
            self.log(f"ERROR: {e}")
            messagebox.showerror("Failed", str(e))
        finally:
            self.btn.config(state='normal')

    def start(self):
        self.btn.config(state='disabled')
        threading.Thread(target=self.install, daemon=True).start()


if __name__ == "__main__":
    tk.Tk().mainloop() if not (root := tk.Tk()) else ImmichInstaller(root) or root.mainloop()