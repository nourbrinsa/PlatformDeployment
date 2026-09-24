# Guide du contrat d'interface : partie conteneurs

> **Projet 3** : application web de location de conteneurs (accès SSH)
> **Responsable de ce document** : Nour (partie conteneurs / Worker Agent / Ansible)
> **Statut** : version 2.0 — mise à jour après réception du sujet détaillé de la prof (`PROJET_3.pdf`)
> **Fichier de référence court** : `docs/contracts.md` (à mettre à jour avec cette version)

---

## ⚠️ Ce qui a changé depuis la version 1

La version 1 de ce guide décrivait des **scripts bash appelés en ligne de commande**, sur une seule machine. Le sujet officiel envoyé par la prof décrit une architecture **distribuée**, avec plusieurs machines (un Controller + plusieurs Workers) qui communiquent en **HTTP**, pas en ligne de commande locale.

**Ce qui ne change pas** : la logique interne (Docker, SSH, génération de mot de passe, expiration) reste la même, dans les mêmes scripts bash.
**Ce qui change** : ces scripts ne sont plus appelés directement par l'API web. Ils sont maintenant encapsulés dans un **Worker Agent**, une petite API Flask qui tourne en continu sur chaque machine Worker, et que le Controller appelle par le réseau (HTTP), pas par `subprocess`.

---

## 1. Vue d'ensemble de l'architecture officielle

```
                         Utilisateur (navigateur)
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │          CONTROLLER           │  ← membre(s) Web + DB
                    │  Flask (API) + Base de données│
                    │                                │
                    │   ┌────────────────────────┐   │
                    │   │   Resource Manager      │   │  ← logique dans Flask,
                    │   │  (choisit un Worker)     │   │    pas une machine à part
                    │   └───────────┬──────────────┘   │
                    └───────────────┼──────────────────┘
                                     │ HTTP (le contrat de ce document)
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
             ┌────────────┐  ┌────────────┐    ┌────────────┐
             │  Worker 1   │  │  Worker 2   │    │  Worker 3   │  ← VM Vagrant,
             │ Worker Agent│  │ Worker Agent│    │ Worker Agent│    partie de Nour
             │  (Flask)    │  │  (Flask)    │    │  (Flask)    │
             │      │       │  │      │       │    │      │       │
             │      ▼       │  │      ▼       │    │      ▼       │
             │  Docker      │  │  Docker      │    │  Docker      │
             │  (conteneur  │  │  (conteneur  │    │  (conteneur  │
             │   SSH loué)  │  │   SSH loué)  │    │   SSH loué)  │
             └────────────┘  └────────────┘    └────────────┘
```

**Rôles, pour clarifier le vocabulaire du sujet :**

- **Controller** : la machine qui héberge Flask (API web) et la base de données. C'est le point d'entrée pour l'utilisateur.
- **Resource Manager / Scheduler** : pas une machine séparée — c'est une partie du **code Flask du Controller**. Il décide *quel Worker* doit héberger une nouvelle instance (en regardant qui est `AVAILABLE`, sa charge CPU/RAM).
- **Worker** : une machine (VM Vagrant) qui héberge réellement les conteneurs loués.
- **Worker Agent** : le programme (API Flask) qui tourne sur **chaque Worker**, reçoit les ordres du Controller en HTTP, et exécute réellement Docker localement. **C'est ma partie.**

Le **contrat de ce document décrit l'interface entre le Resource Manager (côté Controller) et le Worker Agent (côté chaque Worker)**. C'est un contrat interne à l'infrastructure, différent (mais lié) du contrat entre l'utilisateur et l'API web (`POST /rent`, décrit dans le sujet de la prof).

---

## 2. Pourquoi HTTP et pas des scripts bash appelés directement

Dans une architecture à une seule machine, un simple appel `subprocess` suffisait. Mais ici, le Controller et les Workers sont des **machines séparées** (des VM Vagrant différentes). Le Controller ne peut pas exécuter un script bash situé physiquement sur une autre machine sans passer par le réseau. D'où le choix d'une **API HTTP** exposée par chaque Worker Agent :

- Le Controller envoie une requête HTTP (`POST http://worker2-ip:5001/instances`).
- Le Worker Agent, qui tourne en continu sur `worker2`, la reçoit, exécute `create_instance.sh` **localement sur sa propre machine**, et renvoie le résultat en HTTP.

C'est la même logique métier que dans la version 1 du contrat (mêmes champs JSON), mais le moyen de communication change : **HTTP au lieu de ligne de commande**.

---

## 3. Le contrat en détail (version HTTP)

Le Worker Agent tourne sur le port **5001** de chaque Worker.

### 3.1 Règles générales

1. Toutes les réponses sont en **JSON**.
2. Les codes HTTP suivent une convention standard : `200` (succès, lecture/suppression), `201` (créé avec succès), `400` (erreur côté appelant — mauvais paramètre), `404` (ressource introuvable), `500` (erreur interne du Worker).
3. En cas d'erreur, le corps de la réponse suit toujours le même format :
   ```json
   {"status": "error", "message": "texte explicatif en anglais"}
   ```
4. Les paramètres sont validés strictement côté Worker Agent (liste blanche de distributions, etc.). Le Controller doit aussi valider les entrées venant du formulaire utilisateur : ne jamais faire confiance à une saisie utilisateur transmise telle quelle.

### 3.2 `GET /health`

Vérifie que le Worker Agent est vivant et répond. Utile pour le heartbeat (Fonctionnalité 7 du sujet).

**Réponse (200)**
```json
{"status": "ok"}
```

### 3.3 `POST /instances` — créer une instance

**Corps de la requête (JSON)**
```json
{"user_id": "42", "distribution": "ubuntu", "duration_minutes": 60}
```

| Champ | Type | Valeurs autorisées |
|---|---|---|
| `user_id` | texte | lettres, chiffres, `_` et `-` |
| `distribution` | texte | `ubuntu` ou `debian` (extensible) |
| `duration_minutes` | entier | entre `1` et `1440` |

**Réponse en cas de succès (201)**
```json
{
  "status": "running",
  "instance_id": "rent-42-a1b2c3",
  "distribution": "ubuntu",
  "host": "localhost",
  "ssh_port": 32768,
  "ssh_user": "student",
  "ssh_password": "9f8e7d6c5b4a3210",
  "expires_at": "2026-10-01T15:30:00Z"
}
```

| Champ | Type | Signification |
|---|---|---|
| `status` | texte | `running` si succès, `error` sinon |
| `instance_id` | texte | identifiant unique de la location. **Clé** pour toute action ultérieure (statut, suppression) |
| `distribution` | texte | distribution effectivement lancée |
| `host` | texte | adresse IP du Worker sur lequel le conteneur tourne (le Controller doit la connaître ou la déduire de l'appel) |
| `ssh_port` | entier | port SSH choisi automatiquement par Docker |
| `ssh_user` | texte | utilisateur Linux dans le conteneur (`student`) |
| `ssh_password` | texte | mot de passe généré aléatoirement, unique par location |
| `expires_at` | texte | date d'expiration, ISO 8601, **en UTC** |

**Réponse en cas d'erreur (400)**
```json
{"status": "error", "message": "unsupported distribution: fedora"}
```

### 3.4 `GET /instances/<instance_id>` — consulter le statut

**Réponse (200)** — toujours 200, même si l'instance n'existe plus (voir note ci-dessous) :
```json
{"status": "running", "instance_id": "rent-42-a1b2c3"}
```
Valeurs possibles de `status` : `running`, `stopped`, `absent`.

> **Important** : `absent` n'est **pas une erreur HTTP** (toujours code 200). C'est un état métier normal — l'instance a expiré ou a été supprimée. Le Controller doit distinguer ce cas d'une vraie panne réseau ou d'un Worker injoignable (qui, eux, provoqueraient une erreur de connexion, pas une réponse 200 avec `status: absent`).

### 3.5 `DELETE /instances/<instance_id>` — supprimer une instance

**Réponse en cas de succès (200)**
```json
{"status": "deleted", "instance_id": "rent-42-a1b2c3"}
```

**Réponse en cas d'erreur (404)**
```json
{"status": "error", "message": "instance not found"}
```

### 3.6 Nettoyage automatique (interne, rien à appeler)

Chaque Worker Agent gère son propre nettoyage (`cleanup.sh` + cron, en interne). **Aucune route HTTP n'est nécessaire pour ça** — c'est autonome. Conséquence pour le Controller : une instance peut disparaître (passer à `absent`) sans qu'il ait rien demandé. Le Resource Manager doit vérifier périodiquement `expires_at` ou interroger `GET /instances/<id>` pour rester synchronisé.

---

## 4. Comment chaque membre utilise ce contrat

### 4.1 Membre Interface web / API (Flask, côté Controller)

**Ce que vous faites** : le Resource Manager (dans votre code Flask) appelle le Worker Agent choisi, en HTTP, via la librairie `requests` :

```python
import requests

def create_instance_on_worker(worker_ip, user_id, distribution, duration_minutes):
    url = f"http://{worker_ip}:5001/instances"
    response = requests.post(url, json={
        "user_id": str(user_id),
        "distribution": distribution,
        "duration_minutes": duration_minutes
    }, timeout=30)
    return response.json(), response.status_code
```

**Exemple dans une route Flask (`POST /rent`)** :
```python
@app.route("/rent", methods=["POST"])
def rent():
    # 1. Resource Manager : choisir un Worker disponible
    worker = pick_available_worker()   # votre logique, table `workers`
    if worker is None:
        return jsonify({"status": "error", "message": "no worker available"}), 503

    # 2. Appeler le Worker Agent choisi (LE CONTRAT de ce document)
    data, code = create_instance_on_worker(
        worker.ip, current_user.id, form.distribution.data, form.duration.data
    )
    if data["status"] == "error":
        flash(data["message"])
        return redirect("/dashboard")

    # 3. Enregistrer en base (table instances + rentals)
    save_rental(current_user.id, worker.id, data)

    # 4. Marquer le Worker comme BUSY si besoin, selon votre stratégie
    return render_template("rental.html", **data)
```

**Le mock, pour ne pas attendre mon Worker Agent** :
```python
def create_instance_on_worker(worker_ip, user_id, distribution, duration_minutes):
    # MOCK conforme au contrat HTTP — à remplacer par le vrai appel requests plus tard
    return {
        "status": "running",
        "instance_id": f"rent-{user_id}-mock01",
        "distribution": distribution,
        "host": worker_ip,
        "ssh_port": 32768,
        "ssh_user": "student",
        "ssh_password": "mockpassword123",
        "expires_at": "2026-10-01T15:30:00Z",
    }, 201
```

**À prévoir en plus, propre à cette architecture distribuée :**
- Gérer le cas où un Worker ne répond pas (`requests.exceptions.ConnectionError` / `Timeout`) → le marquer `OFFLINE`, et réessayer sur un autre Worker (Fonctionnalité 13 : résilience).
- Stocker l'IP de chaque Worker en base (reçue via `POST /workers/register`, décrit dans le sujet) pour savoir quelle URL appeler.

### 4.2 Membres Base de données

Aucun changement majeur par rapport à la version 1 : les mêmes champs JSON sont à stocker. Un ajout important : la table `instances` doit maintenant retenir **`worker_id`**, puisqu'une instance est désormais liée à un Worker précis (voir le modèle `Instance` du sujet de la prof : `id, container_id, worker_id, distribution_id, ssh_port, status, created_at`).

### 4.3 Moi (Nour) : Worker Agent

**Ce que je garantis :**
- Chaque Worker Agent expose les routes `GET /health`, `POST /instances`, `GET /instances/<id>`, `DELETE /instances/<id>`, conformes au format ci-dessus.
- Chaque route respecte le format JSON et les codes HTTP décrits, sans changement non annoncé.
- Le Worker Agent gère lui-même son cycle de vie (limites de ressources, redémarrage automatique via `--restart unless-stopped`, nettoyage automatique des instances expirées).
- Le Worker Agent est déployé et démarré automatiquement par **Ansible** (playbook `worker.yml`), pas installé à la main.

**Ce que j'attends des autres :**
- Le Controller connaît l'IP et le port (5001) de chaque Worker Agent (via l'enregistrement `POST /workers/register`, côté API web).
- Le Controller gère les cas d'erreur réseau (Worker injoignable) — ce n'est pas au Worker Agent de le faire, il ne sait pas qu'il existe d'autres Workers.

---

## 5. Cycle de vie complet d'une location (mis à jour)

```
1. L'utilisateur remplit le formulaire (distribution + durée) sur le Controller
        │
2. Flask reçoit  POST /rent
        │
3. Resource Manager (code Flask) choisit un Worker AVAILABLE
        │
4. Flask appelle  POST http://<worker-ip>:5001/instances   ← LE CONTRAT
        │
5. Le Worker Agent choisi crée le conteneur localement (Docker) et répond en JSON
        │
6. Flask enregistre la location en base (avec le worker_id)
        │
7. Flask affiche à l'utilisateur : ssh student@<worker-ip> -p <port>  + mot de passe
        │
8a. L'utilisateur clique "Arrêter"     8b. Le temps est écoulé
    → Flask appelle                       → le Worker Agent supprime lui-même
      DELETE .../instances/<id>             le conteneur (cleanup interne)
    → base : status = deleted             → Flask détecte via expires_at
                                             ou GET /instances/<id> → absent
                                           → base : status = expired
```

---

## 6. Tester le contrat soi-même

Une fois le Worker Agent lancé sur une machine (ta VM Vagrant ou ta machine locale) :

```bash
curl http://<worker-ip>:5001/health

curl -X POST http://<worker-ip>:5001/instances \
  -H "Content-Type: application/json" \
  -d '{"user_id": "42", "distribution": "ubuntu", "duration_minutes": 60}'

curl http://<worker-ip>:5001/instances/rent-42-xxxxxx

curl -X DELETE http://<worker-ip>:5001/instances/rent-42-xxxxxx
```

Depuis Windows (PowerShell), remplacer `curl` par `curl.exe` ou utiliser `Invoke-WebRequest` si le vrai `curl` n'est pas installé.

---

## 7. Organisation du travail avec GitHub (mise à jour de la structure)

```
projet-iac/
├── README.md
├── docs/
│   ├── contracts.md              ← version courte du contrat (à mettre à jour avec ce document)
│   └── GUIDE_CONTRAT.md          ← ce document
├── web/                          ← Controller : API Flask, Resource Manager, Dashboard
├── db/                           ← modèles, migrations
└── containers/                   ← partie de Nour, déployée sur chaque Worker
    ├── docker/                   (Dockerfile, entrypoint.sh)
    ├── scripts/                  (create/delete/get_status/cleanup — logique interne)
    ├── agent/                    (worker_agent.py — expose la logique en HTTP)
    ├── ansible/                  (docker.yml, worker.yml, site.yml — déploiement automatique)
    └── vagrant/                  (Vagrantfile — VM(s) Worker de test)
```

Règles inchangées par rapport à la v1 : pas de travail direct sur `main`, Pull Requests relues, pas de secrets commités, messages de commit clairs.

---

## 8. Modifier le contrat

Procédure inchangée : proposer dans une Issue → discuter avec les membres concernés → modifier `docs/contracts.md` et ce guide via Pull Request → prévenir tout le monde avant fusion.

**Règle d'or, toujours valable** : on peut ajouter un champ sans tout casser, mais on ne renomme pas et on ne supprime pas un champ existant sans accord de tous.

---

## 9. Correspondance avec les fonctionnalités du sujet officiel

Pour que le groupe s'y retrouve facilement dans le découpage à 17 fonctionnalités du document de la prof :

| Fonctionnalité du sujet | Concerne ce document ? |
|---|---|
| F6 — Automatisation Ansible | ✅ oui, `containers/ansible/` |
| F7 — Worker Agent et enregistrement dynamique | ✅ oui, `containers/agent/worker_agent.py` |
| F10 — Déploiement des instances Docker | ✅ oui, `containers/scripts/` + `docker/` |
| F11 — Accès SSH | ✅ oui, déjà en place |
| F12 — Gestion de l'expiration | ✅ oui, `cleanup.sh` + cron, côté Worker |
| F5 — Infrastructure Vagrant | ✅ oui, `containers/vagrant/` |
| F8 — Resource Manager / Scheduler | ⚠️ partagé — logique de sélection côté Controller, mais s'appuie sur les routes de ce contrat |
| F9 — Service de location (formulaire, `/rent`) | ❌ côté Controller (API web) |
| F2, F3 — API Flask, Base de données | ❌ côté autres membres |

**À clarifier avec le groupe** : qui prend précisément F7 (Worker Agent) et la partie "enregistrement dynamique" (`POST /workers/register`, `POST /workers/heartbeat`) — ces routes sont exposées par le **Controller**, mais c'est le **Worker Agent** qui doit les **appeler** au démarrage. Il y a donc un petit bout de code à écrire des deux côtés, à coordonner.

---

## 10. Questions fréquentes (mises à jour)

**Pourquoi une API Flask sur chaque Worker, et pas un simple script SSH déclenché par le Controller ?**
C'est possible aussi (Ansible ou un appel SSH direct), mais une API HTTP répond plus vite (pas de connexion SSH à établir à chaque appel) et renvoie une réponse structurée (JSON) facile à traiter côté Controller. C'est le choix que documente ce contrat.

**Le Worker Agent doit-il connaître les autres Workers ?**
Non. Chaque Worker Agent ne connaît que sa propre machine. C'est le Resource Manager (côté Controller) qui a la vue d'ensemble.

**Que se passe-t-il si le Worker entier tombe en panne (pas juste le conteneur) ?**
Le Worker Agent ne peut rien faire dans ce cas (il est lui-même hors service). C'est au Resource Manager, via le heartbeat, de détecter l'absence de réponse et de basculer vers un autre Worker (Fonctionnalité 13).

**Comment le Controller connaît-il l'IP de chaque Worker ?**
Via `POST /workers/register`, envoyé par chaque Worker (ou son agent) au démarrage — décrit dans le sujet officiel, à implémenter en coordination avec le membre API web.

---

## 11. Checklist de validation (mise à jour)

- [ ] **Web/API** : j'ai compris que j'appelle le Worker Agent en HTTP (`requests`), pas en ligne de commande, et j'ai mis à jour mon mock en conséquence.
- [ ] **DB** : la table `instances` inclut bien `worker_id`.
- [ ] **Nour** : le Worker Agent (`worker_agent.py`) est déployé et testé, au minimum en local puis sur une VM Vagrant.
- [ ] **Tous** : on a discuté ensemble de qui code `POST /workers/register` et `POST /workers/heartbeat`, côté Controller et côté Worker.
