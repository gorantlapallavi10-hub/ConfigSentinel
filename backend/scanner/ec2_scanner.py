"""
ConfigSentinel - EC2 / Linux Configuration Scanner
------------------------------------------------------
Connects to a real Linux server (e.g. an AWS EC2 instance) over SSH and
collects READ-ONLY information about its current configuration:

- installed packages (rpm/dpkg)
- running services (systemctl)
- open listening ports (ss)
- system users (/etc/passwd, UID >= 1000)
- existence of important config files
- CPU / memory usage (for display; detailed metrics come from CloudWatch)

SECURITY NOTE:
This module only ever runs a fixed, hardcoded list of READ-ONLY shell
commands needed for scanning. It never accepts or executes arbitrary
user-supplied commands, and it never executes anything the AI suggests.
Remediation (which changes system state) is handled separately by
Ansible playbooks with explicit user confirmation - see remediation/.
"""

import json
import paramiko
from config import settings

# Fixed, read-only commands. Nothing here is built from user input.
_CMDS = {
    "packages_rpm": "rpm -qa --qf '%{NAME}\\n' 2>/dev/null",
    "packages_dpkg": "dpkg-query -W -f='${Package}\\n' 2>/dev/null",
    "services": "systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null",
    "service_status_nginx": "systemctl is-active nginx 2>/dev/null || echo unknown",
    "service_status_ssh": "systemctl is-active ssh 2>/dev/null || systemctl is-active sshd 2>/dev/null || echo unknown",
    "ports": "ss -tuln 2>/dev/null | awk 'NR>1 {print $5}'",
    "users": "awk -F: '$3>=1000 && $1!=\"nobody\" {print $1}' /etc/passwd",
    "cpu": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'",
    "memory": "free | grep Mem | awk '{print ($3/$2)*100}'",
}


class EC2Scanner:
    def __init__(self, host: str, username: str = None, key_path: str = None):
        self.host = host
        self.username = username or settings.EC2_SSH_USER
        self.key_path = key_path or settings.EC2_SSH_KEY_PATH

    def _run(self, ssh_client, command: str) -> str:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=15)
        return stdout.read().decode("utf-8", errors="ignore").strip()

    def scan(self) -> dict:
        """Connect over SSH and return the actual state as a plain dict,
        in the same shape as demo/simulated_server.py's get_state()."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            username=self.username,
            key_filename=self.key_path,
            timeout=10,
        )
        try:
            packages = set(self._run(client, _CMDS["packages_rpm"]).splitlines())
            packages |= set(self._run(client, _CMDS["packages_dpkg"]).splitlines())
            packages.discard("")

            nginx_status = self._run(client, _CMDS["service_status_nginx"])
            ssh_status = self._run(client, _CMDS["service_status_ssh"])

            raw_ports = self._run(client, _CMDS["ports"]).splitlines()
            ports = set()
            for line in raw_ports:
                if ":" in line:
                    try:
                        ports.add(int(line.rsplit(":", 1)[1]))
                    except ValueError:
                        continue

            users = [u for u in self._run(client, _CMDS["users"]).splitlines() if u]

            nginx_conf_check = self._run(
                client, "test -f /etc/nginx/nginx.conf && echo yes || echo no"
            )

            cpu_raw = self._run(client, _CMDS["cpu"])
            mem_raw = self._run(client, _CMDS["memory"])

            state = {
                "packages": sorted(packages),
                "services": {
                    "nginx": {"state": "running" if nginx_status == "active" else "stopped"},
                    "ssh": {"state": "running" if ssh_status == "active" else "stopped"},
                },
                "ports": sorted(ports),
                "users": users,
                "files": {
                    "/etc/nginx/nginx.conf": {"exists": nginx_conf_check == "yes"},
                },
                "cpu_percent": _safe_float(cpu_raw, default=0.0),
                "memory_percent": _safe_float(mem_raw, default=0.0),
            }
            return state
        finally:
            client.close()


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        return round(float(value.replace("%", "").strip()), 1)
    except (ValueError, AttributeError):
        return default
