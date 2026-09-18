# ConfigSentinel - Backend Dockerfile
# ------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# System deps needed by ansible-playbook (real remediation mode) and paramiko
RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir ansible-core==2.16.*

COPY backend/ ./backend/
COPY ansible/ ./ansible/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
