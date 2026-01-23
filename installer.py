#!/usr/bin/env python3
import sys, os, subprocess, threading, secrets, urllib.request

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ImportError:
    print("Missing tkinter. Run: sudo apt install python3-tk -y")
    sys.exit(1)

COMPOSE = """name: immich
networks:
  internal: {driver: bridge, internal: true}
  public: {driver: bridge}
services:
  immich-server:
    container_name: immich_server
    image: ghcr.io/immich-app/immich-server:release
    command: ['start.sh', 'immich']
    volumes: ['{photos}:/usr/src/app/upload', '{extlib}:{extlib}:ro', '/etc/localtime:/etc/localtime:ro']
    env_file: [.env]
    ports: ['2283:2283']
    depends_on: [redis, database]
    restart: always
    networks: [internal, public]
  immich-machine-learning:
    container_name: immich_ml
    image: ghcr.io/immich-app/immich-machine-learning:release
    volumes: [model-cache:/cache]
    env_file: [.env]
    restart: always
    networks: [internal]
  redis:
    container_name: immich_redis
    image: redis:6.2-alpine
    restart: always
    networks: [internal]
  database:
    container_name: immich_postgres
    image: tensorchord/pgvecto-rs:pg14-v0.2.0
    environment: {POSTGRES_PASSWORD: '{dbpass}', POSTGRES_USER: postgres, POSTGRES_DB: immich, POSTGRES_INITDB_ARGS: '--data-checksums'}
    volumes: ['{install}/postgres:/var/lib/postgresql/data']
    restart: always
    networks: [internal]
volumes: {model-cache: }
"""

ENV = """HOST=0.0.0.0
UPLOAD_LOCATION={photos}
IMMICH_MACHINE_LEARNING_URL=http://immich-machine-learning:3003
DB_PASSWORD={dbpass}
DB_HOSTNAME=immich_postgres
DB_USERNAME=postgres
DB_DATABASE_NAME=immich
REDIS_HOSTNAME=immich_redis
"""

class App:
    def __init__(self, root):
        self.root = root
        root.title("Immich Installer")
        root.geometry("600x650")
        self.pw, self.install, self.photos, self.extlib = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        self._ui()

    def _ui(self):
        tk.Label(self.root, text="Immich Installer", font=("Arial", 16, "bold")).pack(pady=10)
        for label, var, hint in [
            ("Root Password:", self.pw, "Required for sudo"),
            ("Install Path:", self.install, "e.g. /home/pi/immich"),
            ("Photos Path:", self.photos, "e.g. /home/pi/photos"),
            ("External Library:", self.extlib, "e.g. /mnt/nas/photos"),
        ]:
            f = tk.Frame(self.root)
            f.pack(fill='x', padx=10, pady=3)
            tk.Label(f, text=label, width=20, anchor='w').pack(side='left')
            e = tk.Entry(f, textvariable=var, show="*" if "Password" in label else "")
            e.pack(side='left', fill='x', expand=True)
            if "Password" not in label:
                tk.Button(f, text="Browse", command=lambda v=var: v.set(filedialog.askdirectory() or v.get())).pack(side='left', padx=5)
            tk.Label(self.root, text=f"   {hint}", fg="gray", font=("Arial", 9)).pack(anchor='w', padx=10)
        self.btn = tk.Button(self.root, text="INSTALL", bg="green", fg="white", font=("Arial", 12, "bold"), command=self._start)
        self.btn.pack(pady=20)
        self.log = scrolledtext.ScrolledText(self.root, height=15, state='disabled')
        self.log.pack(fill='both', expand=True, padx=10, pady=5)

    def _log(self, msg):
        self.root.after(0, lambda: (self.log.configure(state='normal'), self.log.insert(tk.END, msg.strip()+"\n"), self.log.see(tk.END), self.log.configure(state='disabled')))

    def _run(self, cmd, pw=None, cwd=None, live=False):
        full = f"echo '{pw}' | sudo -S {cmd}" if pw else cmd
        p = subprocess.Popen(full, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, bufsize=1)
        if live:
            for line in p.stdout:
                self._log(line)
        p.wait()
        if p.returncode != 0:
            raise Exception(f"Failed: {cmd}")

    def _install(self):
        pw, inst, photos, extlib = self.pw.get(), self.install.get(), self.photos.get(), self.extlib.get()
        if not all([pw, inst, photos, extlib]):
            messagebox.showerror("Error", "All fields required")
            self.btn.config(state='normal')
            return
        try:
            self._log("Checking Docker...")
            try:
                self._run("docker --version")
                self._log("Docker found")
            except:
                self._log("Installing Docker...")
                urllib.request.urlretrieve("https://get.docker.com", "get-docker.sh")
                self._run("sh get-docker.sh", pw)
                os.remove("get-docker.sh")
            self._run(f"usermod -aG docker {os.getenv('USER')}", pw)
            os.makedirs(inst, exist_ok=True)
            dbpass = secrets.token_urlsafe(16)
            with open(f"{inst}/docker-compose.yml", "w") as f:
                f.write(COMPOSE.format(photos=photos, extlib=extlib, dbpass=dbpass, install=inst))
            with open(f"{inst}/.env", "w") as f:
                f.write(ENV.format(photos=photos, dbpass=dbpass))
            self._log("Pulling images...")
            self._run("docker compose pull", pw, inst, live=True)
            self._log("Starting containers...")
            self._run("docker compose up -d", pw, inst, live=True)
            self._log("SUCCESS! Access: http://<PI_IP>:2283")
            messagebox.showinfo("Done", "Immich installed! Reboot to finalize.")
        except Exception as e:
            self._log(f"ERROR: {e}")
            messagebox.showerror("Failed", str(e))
        finally:
            self.btn.config(state='normal')

    def _start(self):
        self.btn.config(state='disabled')
        threading.Thread(target=self._install, daemon=True).start()

if __name__ == "__main__":
    tk.Tk().mainloop() if not (root := tk.Tk()) else (App(root), root.mainloop())