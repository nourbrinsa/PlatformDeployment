#!/bin/bash
set -e

echo ">>> Updating system"
apt-get update -y

echo ">>> Installing Docker"
curl -fsSL https://get.docker.com | sh
usermod -aG docker vagrant

echo ">>> Installing Docker Compose plugin"
apt-get install -y docker-compose-plugin

echo ">>> Installing Ansible"
apt-get install -y ansible

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
  pip install flask flask-sqlalchemy flask-login psycopg2-binary paramiko apscheduler
"

echo ">>> Provisioning complete!"
