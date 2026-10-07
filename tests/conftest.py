import os

os.environ.setdefault("SECRET_KEY", "test-secret-not-used-in-prod")
os.environ.setdefault("WORKER_TOKEN", "test-worker-token-not-used-in-prod")
