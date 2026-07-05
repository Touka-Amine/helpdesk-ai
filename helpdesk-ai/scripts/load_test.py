"""
Test de charge — Phase 12.

Mesure la latence de POST /api/v1/predict sous charge concurrente et compare
au critère de réussite PFE (P95 <= 300 ms, voir PLAN.md section 1.6).

Nécessite l'API démarrée (Docker ou uvicorn local).

Usage :
    python scripts/load_test.py
    python scripts/load_test.py --url http://localhost:8000 --requests 300 --concurrency 30
"""

import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# Échantillon de tickets représentatifs des 8 catégories, pour ne pas biaiser
# la latence avec un seul chemin de code (règles heuristiques, filtre RAG…).
SAMPLE_TICKETS = [
    {"titre": "Problème connexion VPN",
     "description": "Impossible de se connecter au VPN depuis ce matin, erreur d'authentification"},
    {"titre": "Outlook ne s'ouvre plus",
     "description": "Impossible d'ouvrir Outlook, message d'erreur produit non activé"},
    {"titre": "Écran bleu au démarrage",
     "description": "Le poste affiche un écran bleu (BSOD) à chaque démarrage depuis hier"},
    {"titre": "Sauvegarde en échec",
     "description": "La sauvegarde Veeam échoue chaque nuit depuis 3 jours, espace disque insuffisant"},
    {"titre": "Tentative de connexion suspecte",
     "description": "Alerte de sécurité : tentative de connexion depuis une IP inconnue sur le compte admin"},
    {"titre": "Serveur physique en panne",
     "description": "Le serveur de fichiers ne démarre plus, voyant d'alimentation éteint"},
    {"titre": "Application Sage ne répond plus",
     "description": "Sage X3 se fige dès l'ouverture d'un dossier client"},
    {"titre": "Réunion Teams impossible",
     "description": "Impossible de rejoindre une réunion Teams, erreur de connexion audio"},
]


def fire_request(endpoint: str, payload: dict) -> tuple[float, int | None]:
    start = time.perf_counter()
    try:
        r = requests.post(endpoint, json=payload, timeout=15)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, r.status_code
    except requests.RequestException:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, None


def percentile(sorted_values: list[float], p: float) -> float:
    idx = max(0, int(len(sorted_values) * p) - 1)
    return sorted_values[idx]


def run(url: str, n_requests: int, concurrency: int) -> dict:
    endpoint = f"{url}/api/v1/predict"

    # Warm-up (non comptabilisé) : évite de mesurer le premier appel, plus
    # lent (initialisation lazy du modèle sentence-transformers).
    fire_request(endpoint, SAMPLE_TICKETS[0])

    latencies: list[float] = []
    errors = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(fire_request, endpoint, SAMPLE_TICKETS[i % len(SAMPLE_TICKETS)])
            for i in range(n_requests)
        ]
        for future in as_completed(futures):
            elapsed_ms, status = future.result()
            latencies.append(elapsed_ms)
            if status != 200:
                errors += 1

    latencies.sort()
    target_p95 = 300.0
    p95 = percentile(latencies, 0.95)

    return {
        "n_requests": n_requests,
        "concurrency": concurrency,
        "errors": errors,
        "error_rate": round(errors / n_requests, 4),
        "latency_ms": {
            "min": round(min(latencies), 1),
            "mean": round(statistics.mean(latencies), 1),
            "p50": round(percentile(latencies, 0.50), 1),
            "p95": round(p95, 1),
            "p99": round(percentile(latencies, 0.99), 1),
            "max": round(max(latencies), 1),
        },
        "target_p95_ms": target_p95,
        "target_met": p95 <= target_p95,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--out", default="metrics/load_test.json")
    args = parser.parse_args()

    print(f"[load_test] {args.requests} requêtes, concurrence={args.concurrency}, cible={args.url}")
    results = run(args.url, args.requests, args.concurrency)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[load_test] Résultats sauvegardés : {args.out}")

    status = "ATTEINT" if results["target_met"] else "NON ATTEINT"
    print(f"[load_test] Critère PFE P95<=300ms : {status} (P95={results['latency_ms']['p95']}ms)")


if __name__ == "__main__":
    main()
