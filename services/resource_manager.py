from models.worker import Worker

def pick_candidate_workers():
    """Renvoie tous les Workers, dans l'ordre. Le vrai test de
    disponibilité se fait en direct (check_health) au moment de
    l'appel, pas via ce champ status en base (pas de heartbeat fiable
    pour l'instant). Permet de redonner sa chance à un Worker revenu
    en ligne, sans dépendre d'un flag qui ne se met jamais à jour."""
    return Worker.query.order_by(Worker.id).all()
