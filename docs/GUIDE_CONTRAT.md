# Guide du contrat d'interface : partie conteneurs

> **Projet 3** : application web de location de conteneurs (accès SSH)
> **Responsable de ce document** : Nour (partie conteneurs / Docker / Ansible)
> **Statut** : version 1.0, à valider par tout le groupe
> **Fichier de référence court** : `docs/contracts.md` (ce guide l'explique en détail)

---

## 1. À quoi sert ce document ?

Notre projet est découpé en 4 parties, développées **en parallèle** par des personnes différentes :

| Partie | Responsable | Rôle |
|---|---|---|
| Interface web / API (Flask) | _à compléter_ | Comptes, dashboard, formulaire de location |
| Base de données (1) | _à compléter_ | Stockage des comptes et des locations |
| Base de données (2) | _à compléter_ | Stockage des comptes et des locations |
| **Conteneurs** | **Nour** | Création, suppression et supervision des conteneurs SSH |

Le problème : certaines parties ont besoin des autres pour fonctionner. L'interface web a besoin de conteneurs à louer, mes scripts n'ont pas besoin de la base pour démarrer, mais le résultat doit être stocké dedans, etc. Si chacun attend que les autres aient fini, personne n'avance.

**La solution : le contrat d'interface.** C'est un accord écrit qui fixe :

- **comment on appelle** ma partie (quelle commande, quels paramètres) ;
- **ce qu'elle renvoie** (quel format, quels champs, quelles valeurs possibles) ;
- **comment elle signale une erreur**.

Tant que ce contrat ne change pas, **chacun peut coder de son côté sans attendre les autres**, puis on branche les morceaux à la fin.

---

## 2. Vue d'ensemble

```
        Utilisateur (navigateur)
                 │
                 ▼
     ┌───────────────────────┐
     │  Interface web + API  │  ← membre Web (Flask)
     │        (Flask)        │
     └───────┬───────┬───────┘
             │       │
   stocke /  │       │  appelle les scripts
   lit les   │       │  (LE CONTRAT)
   locations │       ▼
             │  ┌─────────────────────┐
             │  │  Gestion conteneurs │  ← Nour
             │  │ Docker / Ansible    │
             │  └──────────┬──────────┘
             ▼             ▼
     ┌──────────────┐   Conteneur SSH
     │ Base de      │   de l'utilisateur
     │ données      │   (host:port)
     └──────────────┘
```

**Qui parle à qui :**

- L'**API Flask** est le chef d'orchestre : elle appelle mes scripts **et** écrit dans la base.
- Mes scripts **ne parlent jamais** à la base de données ni à Flask : ils exécutent une action et renvoient du JSON.
- La **base de données** ne parle qu'à l'API.

Cette séparation est volontaire : chaque partie reste indépendante et testable seule.

---

## 3. Le contrat en détail

Toutes mes commandes sont des scripts dans `containers/scripts/`.

### 3.1 Règles générales (valables pour tous les scripts)

1. **La sortie standard (stdout) contient uniquement du JSON**, sur une seule ligne. Les messages de débogage vont sur la sortie d'erreur (stderr). C'est ce qui permet à Python de faire `json.loads(...)` sans planter.
2. **Code de sortie** : `0` = succès, `1` = erreur.
3. **En cas d'erreur, le format est toujours le même** :
   ```json
   {"status":"error","message":"texte explicatif en anglais"}
   ```
4. Les paramètres sont **validés strictement** côté script (liste blanche). L'API doit tout de même valider les entrées du formulaire : ne jamais faire confiance à ce que saisit un utilisateur.
5. Les noms de champs JSON sont **en anglais, en snake_case**, et ne changent pas sans prévenir le groupe (voir section 8).

### 3.2 Action 1 : créer une instance

**Commande**
```bash
./containers/scripts/create_instance.sh <user_id> <distribution> <duree_minutes>
```

**Paramètres**

| Paramètre | Type | Valeurs autorisées |
|---|---|---|
| `user_id` | texte | lettres, chiffres, `_` et `-` uniquement |
| `distribution` | texte | `ubuntu` ou `debian` (d'autres pourront être ajoutées) |
| `duree_minutes` | entier | entre `1` et `1440` (24 h) |

**Réponse en cas de succès** (code de sortie 0)
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
(En vrai, le JSON est renvoyé sur une seule ligne.)

**Description des champs**

| Champ | Type | Signification |
|---|---|---|
| `status` | texte | `running` si tout s'est bien passé, `error` sinon |
| `instance_id` | texte | Identifiant unique de la location, de la forme `rent-<user_id>-<6 caractères>`. **C'est la clé** pour supprimer ou interroger l'instance ensuite. |
| `distribution` | texte | Distribution effectivement lancée |
| `host` | texte | Adresse à laquelle l'utilisateur se connecte (`localhost` en test, l'IP du serveur ensuite) |
| `ssh_port` | entier | Port SSH choisi automatiquement (change à chaque instance) |
| `ssh_user` | texte | Nom d'utilisateur Linux dans le conteneur (toujours `student` pour l'instant) |
| `ssh_password` | texte | Mot de passe généré aléatoirement, unique par location |
| `expires_at` | texte | Date d'expiration, format ISO 8601, **en UTC** (suffixe `Z`) |

**Ce que l'utilisateur final fera avec ces informations :**
```bash
ssh student@<host> -p <ssh_port>      # puis saisir ssh_password
```

**Exemples d'erreurs**
```json
{"status":"error","message":"unsupported distribution: fedora"}
{"status":"error","message":"duration must be between 1 and 1440"}
{"status":"error","message":"invalid user_id"}
{"status":"error","message":"could not start container"}
```

### 3.3 Action 2 : supprimer une instance

**Commande**
```bash
./containers/scripts/delete_instance.sh <instance_id>
```

**Succès**
```json
{"status":"deleted","instance_id":"rent-42-a1b2c3"}
```

**Erreurs possibles**
```json
{"status":"error","message":"instance not found"}
{"status":"error","message":"invalid instance_id"}
```

Quand l'utiliser : l'utilisateur clique sur « Arrêter ma location » avant la fin.

### 3.4 Action 3 : consulter le statut _(à venir)_

**Commande**
```bash
./containers/scripts/get_status.sh <instance_id>
```

**Réponse prévue**
```json
{"status":"running","instance_id":"rent-42-a1b2c3"}
```

Valeurs possibles de `status` : `running` (en cours), `stopped` (arrêté), `absent` (n'existe plus : expiré, supprimé ou perdu suite à une panne).

> Ce script n'existe pas encore. En attendant, l'API peut se fier à `expires_at` pour savoir si une location est terminée.

### 3.5 Nettoyage automatique (interne, rien à appeler)

Le script `cleanup.sh` supprime les conteneurs dont la date d'expiration est passée. **Il est lancé automatiquement de mon côté** (cron, toutes les minutes). Vous n'avez pas à l'appeler.

Conséquence pour vous : **une location expirée voit son conteneur disparaître toute seule**. Il faut donc que la base et l'interface gèrent l'état « expirée » (voir sections 4 et 5).

---

## 4. Comment chaque membre utilise le contrat

### 4.1 Membre Interface web / API (Flask)

**Ce que vous faites :** vous appelez mes scripts depuis Python, vous lisez le JSON, et vous affichez le résultat.

**Exemple d'appel (création)**
```python
import subprocess
import json

def create_instance(user_id, distribution, duration_minutes):
    result = subprocess.run(
        ["./containers/scripts/create_instance.sh",
         str(user_id), distribution, str(duration_minutes)],
        capture_output=True, text=True, timeout=120
    )
    data = json.loads(result.stdout)   # stdout = uniquement du JSON
    return data                        # contient "status": "running" ou "error"
```

**Exemple d'utilisation dans une route Flask**
```python
data = create_instance(current_user.id, form.distribution.data, form.duration.data)

if data["status"] == "error":
    flash(data["message"])             # afficher l'erreur à l'utilisateur
    return redirect("/dashboard")

# Succès : 1) enregistrer dans la base, 2) afficher les infos de connexion
save_rental(current_user.id, data)     # fonction fournie par l'équipe base de données
return render_template("rental.html",
    ssh_command=f"ssh {data['ssh_user']}@{data['host']} -p {data['ssh_port']}",
    password=data["ssh_password"],
    expires_at=data["expires_at"])
```

**À prévoir dans votre partie :**

- Un **formulaire** avec : choix de la distribution (liste déroulante `ubuntu` / `debian`) et durée (en minutes ou en heures, convertie en minutes avant l'appel).
- Une **page de résultat** qui affiche la commande SSH, le mot de passe et la date d'expiration.
- Un **dashboard** listant les locations de l'utilisateur avec leur statut (en cours / expirée).
- Un **bouton « Arrêter »** qui appelle `delete_instance.sh` puis met à jour la base.
- La **gestion des erreurs** : toujours tester `data["status"]` avant de lire les autres champs.
- L'affichage du mot de passe : il n'est généré **qu'une fois**. Il faut l'afficher à l'utilisateur et le conserver pour le réafficher sur le dashboard (voir 4.2).

**Pour ne pas attendre mes scripts : le mock.** Utilisez cette fonction à la place de l'appel réel, jusqu'à ce que mes scripts soient branchés :

```python
def create_instance(user_id, distribution, duration_minutes):
    # MOCK : renvoie une fausse réponse conforme au contrat
    return {
        "status": "running",
        "instance_id": f"rent-{user_id}-mock01",
        "distribution": distribution,
        "host": "localhost",
        "ssh_port": 32768,
        "ssh_user": "student",
        "ssh_password": "mockpassword123",
        "expires_at": "2026-10-01T15:30:00Z",
    }
```
Le jour où mes scripts sont prêts, vous remplacez uniquement le corps de cette fonction par l'appel `subprocess`. **Le reste de votre code ne change pas.**

**Point d'attention (à discuter ensemble) :** mes scripts utilisent Docker. L'API Flask doit donc tourner sur la même machine (ou avoir accès à cette machine). On verra ensemble comment l'organiser quand tout sera assemblé.

### 4.2 Membres Base de données

**Ce que vous faites :** vous stockez les comptes et les locations. Vous **n'avez jamais besoin de connaître Docker** : vous recevez simplement les valeurs du JSON, transmises par l'API.

**Correspondance entre les champs du contrat et une table**

Proposition de table `rentals`, à adapter selon vos besoins :

| Colonne | Type suggéré | Vient du champ JSON | Remarque |
|---|---|---|---|
| `id` | entier, clé primaire | (généré par la base) | |
| `user_id` | clé étrangère vers `users` | paramètre d'entrée | propriétaire de la location |
| `instance_id` | texte, **unique** | `instance_id` | lien avec le conteneur |
| `distribution` | texte | `distribution` | |
| `host` | texte | `host` | |
| `ssh_port` | entier | `ssh_port` | |
| `ssh_user` | texte | `ssh_user` | |
| `ssh_password` | texte | `ssh_password` | voir note de sécurité ci-dessous |
| `created_at` | date-heure | (généré par la base) | |
| `expires_at` | date-heure | `expires_at` | **stocker en UTC** |
| `status` | texte | `status` | `running`, `stopped`, `expired`, `deleted` |

**Fonctions dont l'API aura besoin** (à vous de définir les noms, mais prévenez l'API) :

- `save_rental(user_id, data)` : enregistre une location à partir du JSON reçu ;
- `get_rentals_by_user(user_id)` : liste les locations d'un utilisateur ;
- `get_rental(instance_id)` : retrouve une location ;
- `update_rental_status(instance_id, status)` : met à jour le statut ;
- `get_expired_rentals()` : locations dont `expires_at` est dépassé et qui sont encore marquées `running`. Cela permet à l'API de synchroniser l'état de la base avec la réalité (mes scripts suppriment les conteneurs expirés, mais ne touchent pas à la base).

**Point de sécurité à décider ensemble :** le mot de passe SSH doit pouvoir être **réaffiché** à l'utilisateur, donc il ne peut pas être haché comme un mot de passe de compte. Deux options : le stocker tel quel (acceptable ici car il est temporaire et lié à un conteneur jetable) ou le chiffrer. À trancher en groupe. En revanche, **les mots de passe des comptes utilisateurs de l'application doivent, eux, être hachés** (par exemple avec `werkzeug.security`).

**Et si la base n'est pas prête ?** De mon côté, en attendant, je stocke mes tests dans un simple fichier local. Côté API, vous pouvez utiliser SQLite ou une liste Python en mémoire avec les mêmes fonctions. Le jour où la vraie base est prête, on remplace uniquement ce module.

### 4.3 Moi (Nour) : partie conteneurs

**Ce que je garantis :**

- Les noms de champs, types et codes d'erreur **ne changent pas sans prévenir** le groupe.
- La sortie standard contient **uniquement du JSON** valide.
- Chaque instance a un **mot de passe unique**, un **port libre choisi automatiquement**, et une **date d'expiration**.
- Les conteneurs expirés sont **supprimés automatiquement**.
- Les scripts sont testés avant chaque push sur la branche partagée.

**Ce que j'attends des autres :**

- L'API appelle les scripts avec les bons paramètres (voir section 3) et lit toujours `status` avant le reste.
- L'API/la base gardent trace de l'`instance_id` (c'est la seule façon de retrouver un conteneur).
- Toute demande de nouveau champ ou de nouvelle action m'est communiquée (voir section 8).

**Ce que je fournirai plus tard**, sans changer le contrat : limites de ressources par conteneur (CPU, mémoire), redémarrage automatique en cas de panne, remplacement des scripts par des playbooks Ansible, et simulation de plusieurs serveurs avec Vagrant pour la haute disponibilité.

---

## 5. Cycle de vie complet d'une location

```
1. L'utilisateur remplit le formulaire (distribution + durée)
        │
2. L'API appelle       create_instance.sh <user_id> <distribution> <durée>
        │
3. Mes scripts créent le conteneur et renvoient le JSON
        │
4. L'API enregistre la location dans la base (save_rental)
        │
5. L'API affiche à l'utilisateur : ssh student@host -p port  + mot de passe
        │
6. L'utilisateur utilise son conteneur par SSH
        │
7a. Il clique sur « Arrêter »     7b. Le temps est écoulé
    → API appelle                     → cleanup.sh supprime le conteneur
      delete_instance.sh                (automatique, toutes les minutes)
    → base : status = deleted         → l'API repère expires_at dépassé
                                        → base : status = expired
```

---

## 6. Tester le contrat soi-même

Une fois mes scripts poussés sur la branche, n'importe qui avec Docker peut les essayer :

```bash
# Création
./containers/scripts/create_instance.sh 42 ubuntu 60

# Connexion (remplacer PORT par la valeur du JSON)
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p PORT student@localhost

# Suppression
./containers/scripts/delete_instance.sh rent-42-xxxxxx

# Cas d'erreur (doivent renvoyer {"status":"error",...})
./containers/scripts/create_instance.sh 42 fedora 60
./containers/scripts/create_instance.sh 42 ubuntu abc
```

Prérequis : Docker installé et lancé, `openssl` disponible, environnement Linux (WSL2 sous Windows).

---

## 7. Organisation du travail avec GitHub

**Chacun travaille sur sa propre branche :**

| Branche | Propriétaire | Contenu |
|---|---|---|
| `feature/containers` | Nour | dossier `containers/` |
| `feature/web` | _à compléter_ | dossier `web/` |
| `feature/db` | _à compléter_ | dossier `db/` |

**Règles :**

1. **Ne jamais travailler directement sur `main`.** On y fusionne via une **Pull Request** relue par au moins un autre membre.
2. **Chacun ne modifie que son dossier.** Pour changer autre chose (surtout ce contrat), on en parle d'abord.
3. Récupérer régulièrement les changements des autres :
   ```bash
   git checkout main && git pull
   git checkout ma-branche && git merge main
   ```
4. **Aucun secret dans le dépôt** : pas de mot de passe, de token ni de clé privée. Les ajouter au `.gitignore`.
5. Messages de commit clairs (`Add debian support`, `Fix port parsing`), pas de « update » ou « test ».
6. Suivre les tâches avec les **Issues GitHub** ou un tableau **Trello** (recommandé par le cours), et faire le point à chaque réunion de suivi par galon.

**Structure du dépôt :**
```
projet-iac/
├── README.md
├── docs/
│   ├── contracts.md         ← version courte du contrat
│   └── GUIDE_CONTRAT.md     ← ce document
├── web/                     ← interface web / API
├── db/                      ← base de données
└── containers/              ← partie de Nour
    ├── docker/              (Dockerfile, entrypoint.sh)
    ├── scripts/             (create / delete / cleanup / status)
    ├── ansible/
    └── vagrant/
```

---

## 8. Modifier le contrat

Le contrat est une promesse : le modifier sans prévenir casse le travail des autres. Procédure :

1. **Proposer** la modification dans une Issue GitHub ou dans le groupe de discussion (quel champ, pourquoi).
2. **Discuter** avec les membres concernés.
3. **Modifier** `docs/contracts.md` et ce guide, via une Pull Request.
4. **Prévenir** tout le monde avant la fusion.

**Règle d'or : on peut ajouter un champ sans tout casser, mais on ne renomme pas et on ne supprime pas un champ existant sans accord de tous.**

Exemples de demandes légitimes : un champ `created_at`, un champ `cpu_limit`, une nouvelle distribution, une action de prolongation de location (`extend_instance.sh`).

---

## 9. Ordre de développement prévu

| Étape | Qui | Ce qui est livré | Ce dont on a besoin |
|---|---|---|---|
| 1 | Nour | Contrat validé + mock de la réponse | Validation du groupe |
| 2 | Web, DB | Développement avec le mock | Le contrat |
| 3 | Nour | Vrais scripts create / delete / cleanup | Rien |
| 4 | Web + Nour | Branchement des vrais scripts dans l'API | Scripts + API |
| 5 | DB + Web | Branchement de la vraie base | Base + API |
| 6 | Nour | Haute disponibilité, Ansible, Vagrant | Tout ce qui précède |
| 7 | Tous | Tests d'ensemble, rapport, démonstration | |

---

## 10. Questions fréquentes

**Pourquoi des scripts Bash et pas directement une API ?**
C'est le plus simple pour commencer. Comme le contrat fixe l'interface, on pourra remplacer les scripts par Ansible, ou les exposer via une petite API, sans que les autres n'aient à modifier leur code.

**Pourquoi le port SSH change-t-il à chaque instance ?**
Plusieurs conteneurs tournent sur la même machine. Docker attribue un port libre à chacun pour éviter les conflits.

**Que se passe-t-il si le conteneur plante ?**
Pour l'instant, la location est perdue. La haute disponibilité (recréation automatique) fait partie de ma prochaine phase, sans changement du contrat.

**Que faire si je reçois une réponse qui n'est pas du JSON ?**
C'est un bug de mon côté. Envoyez-moi la commande exacte et la sortie reçue.

**Quelle heure utiliser ?**
Toujours l'UTC dans les échanges et la base. On convertit à l'heure locale uniquement à l'affichage.

**Comment savoir si un champ est obligatoire ?**
Dans une réponse de succès, **tous les champs listés sont toujours présents**.

---

