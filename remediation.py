from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()


def restart_pod(pod_name):

    v1.delete_namespaced_pod(
        name=pod_name,
        namespace="default"
    )

    print(f"Restarted pod {pod_name}")


def auto_remediate(pod_name, reason):

    if "CrashLoopBackOff" in reason:

        restart_pod(pod_name)

    if "OOMKilled" in reason:

        print(
            "Recommendation: Increase memory limits"
        )
