
# Immich GUI-Installer for Raspberry Pi

A simple, graphical installer for [Immich](https://immich.app/) designed for Raspberry Pi and Debian-based systems. No dependencies required.

This script automates the tedious setup process: it checks for system dependencies, installs Docker & Docker Compose, configures the necessary environment variables, and pulls the correct images for your architecture.

### Features
* **Zero Terminal Required:** Graphical interface for setting passwords and paths.
* **Auto-Dependency:** Installs Docker automatically if missing.
* **Smart Configuration:** Sets up `docker-compose.yml` and `.env` with correct ports (2283) and permissions.
* **Real-time Logs:** See exactly what is happening during the download process.

If this project makes your life easier, a donation of any amount is appreciated :-)

<a href="https://www.paypal.com/donate?hosted_button_id=CKAK6UZFJ5ULU">
  <img style="width:200px;" src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" alt="Donate with PayPal" />
</a>

---

# How to Use

#### Method 1: Download ZIP (Recommended)

1. Click the green **Code** button above and select **Download ZIP**.
2. Extract the files on your computer.
3. Double click on `installer.py`
4. Select **Execute**


#### Method 2: Command Line
Open your terminal and run the following commands one after another:

```bash
git clone https://github.com/duongel/immich-installer.git
cd immich-installer
chmod +x installer.py
./installer.py
````

---

### Accessing Immich

Once the installation is complete and the containers have started, open your browser and go to:

```
http://<YOUR_PI_IP_ADDRESS>:2283
```

_Note: If you are accessing it from the same device, you can use `http://localhost:2283`._

---

### Post-Install: Setting up External Library

If you provided a path for an External Library (e.g., /media/hdd/photos) during installation, follow these steps to make them visible in Immich:
- Log in to Immich as the Admin user
- Click on your user icon and then **Administration** (top right corner)
- Go to **External Libraries** in the left sidebar
- Click **Create Library** on top right corner
- Click on **Add Folder** in settings of External Library
- Important: Under **Path**, enter the exact same path you entered in the installer (e.g. /mnt/nas/photos)
- Click **Add**
- Click **Scan** in top right corner

---

### Troubleshooting

**The installer won't open / "Permission Denied"** If double-clicking the file does nothing, or you see a permission error, you likely need to make the script executable. Open a terminal in the folder and run:

Bash

```bash
chmod +x installer.py
```

**"Tkinter not found" or Silent Failure** If the app crashes immediately on a minimal Debian install (or nothing happens when you run it), you are likely missing the Python GUI library. Install it with:

Bash

```bash
sudo apt update && sudo apt install python3-tk -y
```

**"Connection Refused"** Wait a few minutes after installation. The database takes some time to initialize before the web interface becomes active.

---

### License

MIT License - See [LICENSE](https://www.google.com/search?q=LICENSE) for details.
