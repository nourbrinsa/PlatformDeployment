#!/bin/bash
set -e

echo ">>> Updating system"
apt-get update -y

echo ">>> Installing Python + Flask deps"
apt-get install -y python3 python3-pip python3-venv

echo ">>> Installing PostgreSQL"
apt-get install -y postgresql postgresql-contrib

echo ">>> Setting up Python virtual environment"
sudo -u vagrant bash -c "
  cd /vagrant &&
  python3 -m venv venv &&
  source venv/bin/activate &&
  pip install --upgrade pip &&
  pip install -r requirements.txt &&
  pip install apscheduler
"

echo ">>> Provisioning complete!"
echo ">>> N'oubliez pas : cp .env.example .env (puis SECRET_KEY et WORKER_TOKEN)"
