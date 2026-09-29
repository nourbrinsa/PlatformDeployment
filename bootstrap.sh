#!/bin/bash
set -e

echo ">>> Updating system"
apt-get update -y

echo ">>> Installing Python + Flask deps"
apt-get install -y python3 python3-pip python3-venv

echo ">>> Installing PostgreSQL"
apt-get install -y postgresql postgresql-contrib

echo ">>> Setting up Python virtual environment"
echo ">>> Installing python-dotenv flask-migrate"
sudo -u vagrant bash -c "
  cd /vagrant &&
  python3 -m venv venv &&
  source venv/bin/activate &&
  pip install --upgrade pip &&
  pip install flask flask-sqlalchemy flask-login psyco pg2-binary paramiko apscheduler &&
  pip install python-dotenv flask-migrate
"

echo ">>> Provisioning complete!"
