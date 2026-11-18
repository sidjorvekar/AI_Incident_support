import requests

PROM_URL = "http://localhost:9090/api/v1/query"


def query_prometheus(query):

    try:

        response = requests.get(
            PROM_URL,
            params={"query": query},
            timeout=5
        )

        return response.json()

    except Exception as e:

        return {"error": str(e)}


def get_cluster_metrics():

    cpu = query_prometheus(
        'rate(container_cpu_usage_seconds_total[5m])'
    )

    memory = query_prometheus(
        'container_memory_usage_bytes'
    )

    restarts = query_prometheus(
        'kube_pod_container_status_restarts_total'
    )

    return {
        "cpu": cpu,
        "memory": memory,
        "restarts": restarts
    }
