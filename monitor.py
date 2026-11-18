import sys

sys.stdout.reconfigure(encoding='utf-8')

from kubernetes import client, config

from datetime import datetime, UTC

from email.mime.text import MIMEText

from rag_engine import (
    store_incident,
    search_similar_incidents
)

from prometheus_client import (
    get_cluster_metrics
)

from remediation import auto_remediate

import ollama

import smtplib
import json
import os
import time

# ==========================================
# CONFIG
# ==========================================

INCIDENT_FILE = "incidents/incidents.json"

EMAIL_SENDER = "devik.cs@gmail.com"
EMAIL_PASSWORD = "dzdjiivfxaicvluq"
EMAIL_RECEIVER = "devipriyakarunagaran@gmail.com"

OLLAMA_MODEL = "phi3:mini"
# ==========================================
# KUBERNETES
# ==========================================

config.load_kube_config()

v1 = client.CoreV1Api()

alerted_pods = {}

os.makedirs("incidents", exist_ok=True)

# ==========================================
# EMAIL ALERT
# ==========================================


def send_email(subject, message):

    msg = MIMEText(message)

    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL_SENDER,
        EMAIL_PASSWORD
    )

    server.send_message(msg)

    server.quit()

# ==========================================
# AI ANALYSIS
# ==========================================


def analyze_issue(
    pod_name,
    logs,
    metrics,
    events,
    reason
):

    similar = search_similar_incidents(logs)

    prompt = f"""
You are an expert Kubernetes SRE.

Analyze this issue.

Pod:
{pod_name}

Reason:
{reason}

Logs:
{logs}

Events:
{events}

Prometheus Metrics:
{metrics}

Similar Past Incidents:
{similar}

Provide:
1. Root Cause
2. Impact
3. Fix
4. Severity
5. Auto-remediation suggestion
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]

# ==========================================
# SAVE INCIDENT
# ==========================================


def save_incident(data):

    try:

        with open(INCIDENT_FILE, "r") as f:
            incidents = json.load(f)

    except:

        incidents = []

    incidents.append(data)

    with open(INCIDENT_FILE, "w") as f:
        json.dump(
            incidents,
            f,
            indent=2
        )

# ==========================================
# MAIN LOOP
# ==========================================

print("Starting AI AIOps Monitor...")

while True:

    try:

        pods = v1.list_namespaced_pod(
            namespace="default"
        )

        metrics = get_cluster_metrics()

        for pod in pods.items:

            pod_name = pod.metadata.name

            status = pod.status.phase

            restart_count = 0

            pod_reason = ""

            container_statuses = (
                pod.status.container_statuses
            )

            if container_statuses:

                restart_count = (
                    container_statuses[0].restart_count
                )

                state = (
                    container_statuses[0].state
                )

                if state.waiting:
                    pod_reason = (
                        state.waiting.reason
                    )

                elif state.terminated:
                    pod_reason = (
                        state.terminated.reason
                    )

            previous_restart = alerted_pods.get(
                pod_name,
                0
            )

            new_issue = (
                restart_count > previous_restart
                or pod_reason in [
                    "CrashLoopBackOff",
                    "ImagePullBackOff",
                    "ErrImagePull"
                ]
            )

            if new_issue:

                print(
                    f"INCIDENT DETECTED: {pod_name}"
                )

                try:

                    logs = v1.read_namespaced_pod_log(
                        name=pod_name,
                        namespace="default",
                        tail_lines=50
                    )

                except Exception as e:

                    logs = str(e)

                events = "Kubernetes events captured"

                ai_analysis = analyze_issue(
                    pod_name,
                    logs,
                    metrics,
                    events,
                    pod_reason
                )

                incident = {
                    "timestamp": datetime.now(
                        UTC
                    ).isoformat(),
                    "pod": pod_name,
                    "status": status,
                    "reason": pod_reason,
                    "analysis": ai_analysis
                }

                save_incident(incident)
                store_incident(
                    ai_analysis,
                    metadata={
                        "pod": pod_name,
                        "reason": pod_reason
                    }
                )

                send_email(
                    f"Incident - {pod_name}",
                    ai_analysis
                )

                auto_remediate(
                    pod_name,
                    pod_reason
                )

                alerted_pods[
                    pod_name
                ] = restart_count

        time.sleep(5)

    except Exception as e:

        print(f"MONITOR ERROR: {e}")

        time.sleep(5)

