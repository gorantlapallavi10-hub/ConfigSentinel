"""
ConfigSentinel - Central Configuration
----------------------------------------
All secrets and environment-specific settings are loaded from environment
variables (see .env.example). NOTHING sensitive is hardcoded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file if present


class Settings:
    # --- App ---
    APP_NAME: str = "ConfigSentinel"
    ENV: str = os.getenv("APP_ENV", "development")          # development | production
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # --- Security ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))

    # --- Database ---
    # SQLite for local/dev by default; set DATABASE_URL to a postgres:// URL in prod.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./configsentinel.db")

    # --- AI (LLM) ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-sonnet-4-6")

    # --- AWS ---
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    EC2_HOST: str = os.getenv("EC2_HOST", "")
    EC2_SSH_USER: str = os.getenv("EC2_SSH_USER", "ec2-user")
    EC2_SSH_KEY_PATH: str = os.getenv("EC2_SSH_KEY_PATH", "")
    CLOUDWATCH_NAMESPACE: str = os.getenv("CLOUDWATCH_NAMESPACE", "ConfigSentinel")
    # NOTE: AWS credentials themselves are never read here directly.
    # boto3 automatically picks them up from the environment, an IAM role,
    # or the shared AWS credentials file - never store access keys in code or DB.

    # --- Ansible ---
    ANSIBLE_INVENTORY_PATH: str = os.getenv("ANSIBLE_INVENTORY_PATH", "../ansible/inventory")
    ANSIBLE_PLAYBOOK_PATH: str = os.getenv("ANSIBLE_PLAYBOOK_PATH", "../ansible/remediation.yml")

    # --- Desired state file ---
    DESIRED_STATE_PATH: str = os.getenv("DESIRED_STATE_PATH", "./demo/desired_state.yaml")


settings = Settings()
