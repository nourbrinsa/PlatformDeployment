# Projet 3 — IaC Rental Dashboard (4ASTI)

A web application built with Flask that lets users register, log in, and rent SSH-accessible container instances for a set duration, with high availability and automatic expiry. Built as part of the 4ASTI Infrastructure as Code course at INSA.

---

## What this does

- Users register and log in via a web dashboard
- Users can rent a container (Ubuntu/Debian) for a chosen duration
- Each rental gives the user SSH access to their own isolated container
- Containers are automatically destroyed when the rental expires
- If a container crashes, it is automatically restarted (high availability)

---

## Tech stack

| Layer | Tool |
|---|---|
| VM environment | Vagrant + VirtualBox |
| Containerization | Docker + Docker Compose |
| Configuration management | Ansible |
| Web backend | Flask (Python) |
| Database | PostgreSQL |
| SSH provisioning | Paramiko + OpenSSH |

---

## Prerequisites (install these on your host machine)

### 1. VirtualBox

Download and install from the official site:
https://www.virtualbox.org/wiki/Downloads

Pick the installer for your OS

On Ubuntu/Kubuntu/Debian-based Linux:
```bash
sudo apt update
sudo apt install virtualbox
```

> **Note (Linux only):** If you have Secure Boot enabled, you will be prompted to set a MOK password during install. On reboot, enter the MOK Management screen, select **Enroll MOK**, and enter the password you chose. This is required for VirtualBox kernel modules to load.

---

### 2. Vagrant

Download from:
https://developer.hashicorp.com/vagrant/downloads

Pick the package for your OS and version.

On Ubuntu/Kubuntu/Debian-based Linux:
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update
sudo apt install vagrant
```

Verify both are installed:
```bash
vagrant --version
vboxmanage --version
```

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/mehdi15649/projet-iac
cd projet-iac
```

### 2. Boot the VM

```bash
vagrant up
```

This will:
- Download the Ubuntu 22.04 base box (~500 MB, first time only)
- Boot the VM in VirtualBox
- Automatically install Docker, Ansible, Python, PostgreSQL and all Flask dependencies inside the VM

**First boot takes ~5–10 minutes.** Subsequent boots are fast (under a minute).

### 3. Enter the VM

```bash
vagrant ssh
```

### 4. Activate the Python environment and run the app

```bash
cd /vagrant
source venv/bin/activate
flask run --host=0.0.0.0
```

### 5. Open in your browser

```
http://localhost:5000
```

---

## Daily workflow

```bash
vagrant up          # start the VM (if it's not already running)
vagrant ssh         # enter the VM
cd /vagrant
source venv/bin/activate
flask run --host=0.0.0.0
```

Edit code in your normal editor on your **host machine** — the `/vagrant` folder inside the VM is synced live with the project folder on your host.

---

## Stopping and cleaning up

```bash
vagrant halt        # stop the VM (keeps everything, like shutting down)
vagrant reload      # restart the VM (use after Vagrantfile changes)
vagrant provision   # re-run bootstrap.sh (use after bootstrap.sh changes)
vagrant destroy -f  # DELETE the VM completely (use at end of project)
```

> After `vagrant destroy`, your host machine is left exactly as it was before. All installed tools (Docker, Ansible, PostgreSQL, Python packages) existed only inside the VM.

---

## Project structure

```
projet3-iac/
├── Vagrantfile          # VM configuration
├── bootstrap.sh         # Provisioning script (installs all tools)
├── app.py               # Flask application entry point
├── models/              # SQLAlchemy DB models (users, rentals)
├── routes/              # Flask route blueprints
├── templates/           # Jinja2 HTML templates
├── ansible/             # Ansible playbooks for container provisioning
├── docker/              # Dockerfiles and docker-compose templates
├── .env.example         # Example environment variables (copy to .env)
├── .gitignore
└── README.md
```

---

## Environment variables

Copy `.env.example` to `.env` inside the VM and fill in values:

```bash
cp .env.example .env
nano .env
```

* `.env`is already in `.gitignore`.

---

## Branching strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, working code only. Never push directly. |
| `dev` | Integration branch — merge features here first |
| `feature/web-api` | Web API and Flask routes |
| `feature/ansible` | Ansible playbooks |
| `feature/database` | DB models and migrations |
| `feature/docker` | Dockerfiles and compose templates |

### Workflow for each feature

```bash
git checkout dev
git pull
git checkout -b feature/your-feature
# ... work ...
git add .
git commit -m "Description of what you did"
git push origin feature/your-feature
# Then open a Pull Request to merge into dev on GitHub
```

`dev` is merged into `main` once a working milestone is reached.

---

## Team

- **Web API** — Flask routes, auth, dashboard
- **Ansible** — Playbooks for container provisioning and SSH setup
- **Database** — SQLAlchemy models, PostgreSQL schema, migrations
- **Docker** — Dockerfiles, Compose templates, container lifecycle scripts

---

## Troubleshooting

**`vagrant up` fails with a network error mid-provisioning:**
```bash
vagrant provision   # retries the install step without rebuilding the VM
```

**Port 5000 already in use on your host:**
Edit `Vagrantfile`, change `host: 5000` to another port (e.g. `5001`), then run `vagrant reload`.

**Flask says "Could not locate a Flask application":**
Make sure you are in `/vagrant` and have run `source venv/bin/activate` first.

**Container SSH ports not reachable:**
Check that your `Vagrantfile` has forwarded the relevant ports (2200–2210) and run `vagrant reload`.
