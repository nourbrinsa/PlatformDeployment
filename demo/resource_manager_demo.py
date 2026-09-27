"""
Script de DEMO, jetable, qui simule ce que fera le Resource Manager
cote Flask (POST /rent). Ne fait pas partie du livrable final,
sert uniquement a prouver que le flux complet fonctionne avant que
la partie web ne soit codee.

Usage :
    pip install requests
    python3 resource_manager_demo.py rent client1 ubuntu 30
    python3 resource_manager_demo.py status rent-client1-xxxxxx 192.168.56.11
    python3 resource_manager_demo.py stop rent-client1-xxxxxx 192.168.56.11
    python3 resource_manager_demo.py demo-ha        (demo resilience)
"""
import sys
import time

import requests

WORKERS = ["192.168.56.11", "192.168.56.12"]
WORKER_AGENT_PORT = 5001
TIMEOUT = 5


def pick_available_worker():
    """
    Resource Manager simplifie : renvoie le premier worker qui repond
    a /health. C'est exactement ce que fera la vraie fonction Flask,
    en plus complet (verification CPU/RAM, table workers en base...).
    """
    for ip in WORKERS:
        try:
            r = requests.get(f"http://{ip}:{WORKER_AGENT_PORT}/health", timeout=TIMEOUT)
            if r.status_code == 200:
                return ip
        except requests.exceptions.RequestException:
            print(f"  worker {ip} injoignable, on essaie le suivant...")
            continue
    return None


def rent(user_id, distribution, duration_minutes):
    print(f"Recherche d'un worker disponible parmi {WORKERS}...")
    worker_ip = pick_available_worker()
    if worker_ip is None:
        print("Aucun worker disponible. Abandon.")
        return None

    print(f"Worker choisi : {worker_ip}")
    try:
        r = requests.post(
            f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances",
            json={
                "user_id": user_id,
                "distribution": distribution,
                "duration_minutes": duration_minutes,
            },
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print(f"Erreur reseau vers {worker_ip} : {e}")
        return None

    data = r.json()
    if data.get("status") != "running":
        print(f"Erreur renvoyee par le worker : {data.get('message')}")
        return None

    # Le Worker Agent renvoie "host": "localhost" -> on corrige avec la
    # vraie IP du worker qu'on a appele (c'est le Controller qui le sait,
    # pas le Worker Agent lui-meme)
    data["host"] = worker_ip

    print("\n=== Instance creee avec succes ===")
    print(f"  instance_id : {data['instance_id']}")
    print(f"  commande SSH : ssh {data['ssh_user']}@{data['host']} -p {data['ssh_port']}")
    print(f"  mot de passe : {data['ssh_password']}")
    print(f"  expire a     : {data['expires_at']}")
    print("===================================\n")
    return data


def status(instance_id, worker_ip):
    try:
        r = requests.get(
            f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances/{instance_id}", timeout=TIMEOUT
        )
        print(r.json())
    except requests.exceptions.RequestException as e:
        print(f"Erreur : {e}")


def stop(instance_id, worker_ip):
    try:
        r = requests.delete(
            f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances/{instance_id}", timeout=TIMEOUT
        )
        print(r.json())
    except requests.exceptions.RequestException as e:
        print(f"Erreur : {e}")


def demo_ha():
    """
    Demo de resilience : cree une instance, puis simule la disponibilite
    des workers en boucle pour montrer la bascule automatique si un
    worker tombe (a combiner avec `vagrant halt worker1` fait a la main
    dans un autre terminal pendant que ce script tourne).
    """
    print("=== DEMO HAUTE DISPONIBILITE ===")
    print("Ce script va essayer de louer une instance toutes les 5 secondes.")
    print("Pendant ce temps, dans un autre terminal, fais : vagrant halt worker1")
    print("Observe que le script bascule automatiquement sur worker2.\n")
    try:
        while True:
            rent("demo-ha", "ubuntu", 5)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nDemo arretee.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    action = sys.argv[1]

    if action == "rent":
        _, _, user_id, distribution, duration = sys.argv
        rent(user_id, distribution, int(duration))
    elif action == "status":
        _, _, instance_id, worker_ip = sys.argv
        status(instance_id, worker_ip)
    elif action == "stop":
        _, _, instance_id, worker_ip = sys.argv
        stop(instance_id, worker_ip)
    elif action == "demo-ha":
        demo_ha()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
