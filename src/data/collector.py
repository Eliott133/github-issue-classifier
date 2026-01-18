import logging
from typing import Any, Dict, Iterator, List, Optional, Union

import requests
from pymongo import DESCENDING, UpdateOne

from src.config import settings
from src.db.mongo_client import mongo_client
from src.utils.github_auth import TokenManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitHubCollector:
    def __init__(self):
        self.db_client = mongo_client
        self.token_manager = TokenManager(settings.tokens_list)
        self.collection = self.db_client.get_collection("raw_issues")
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token_manager.get_token()}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_last_update_date(self, repo_name: str) -> Optional[str]:
        """
        Trouve la date de dernière modification de l'issue la plus récente en base.
        Cela sert de 'High Water Mark' pour la collecte incrémentale.
        """
        # L'URL du repo dans le JSON ressemble à : https://api.github.com/repos/owner/repo
        repo_url = f"{self.base_url}/repos/{repo_name}"

        # On cherche le document le plus récent (tri par updated_at décroissant)
        last_issue = self.collection.find_one(
            {"repository_url": repo_url}, sort=[("updated_at", DESCENDING)]
        )

        if last_issue and "updated_at" in last_issue:
            return last_issue["updated_at"]
        return None

    def fetch_repo_issues(
        self, repo_name: str, batch_size: int = 100
    ) -> Iterator[List[Dict]]:
        """
        Générateur intelligent : ne récupère que ce
        qui a changé depuis la dernière fois.
        """
        url = f"{self.base_url}/repos/{repo_name}/issues"

        # 1. Récupération du point de repère (Checkpoint)
        since_date = self.get_last_update_date(repo_name)

        if since_date:
            logger.info(
                f"Mode Incrémental activé pour {repo_name}."
                f"Récupération depuis : {since_date}"
            )
        else:
            logger.info(
                f"Première collecte pour {repo_name}."
                f"Récupération complète (Full Load)."
            )

        page = 1

        while True:
            params: Dict[str, Union[str, int]] = {
                "state": "all",
                "per_page": batch_size,
                "page": page,
                # On trie par mise à jour, pas par création
                "sort": "updated",
                # Plus vieux au plus récent (pour reprendre chronologiquement)
                "direction": "asc",
            }

            # Ajout du filtre 'since' si on a déjà des données
            if since_date:
                params["since"] = since_date

            try:
                response = requests.get(url, headers=self._get_headers(), params=params)

                if response.status_code in [403, 429]:
                    logger.warning(f"Rate limit atteint (Page {page}). Rotation...")
                    self.token_manager.handle_rate_limit()
                    continue

                response.raise_for_status()

                batch = response.json()
                if not batch:
                    break

                # Filtrage des PRs
                issues = [item for item in batch if "pull_request" not in item]

                if issues:
                    yield issues

                # Optimisation : Si le batch est incomplet (< 100),
                # c'est que c'est la fin
                if len(batch) < batch_size:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur réseau sur {repo_name}: {e}")
                break

    def save_batch(self, issues: List[Dict[str, Any]]):
        if not issues:
            return

        operations = [
            UpdateOne({"id": issue["id"]}, {"$set": issue}, upsert=True)
            for issue in issues
        ]

        try:
            self.collection.bulk_write(operations)
        except Exception as e:
            logger.error(f"Erreur d'écriture Mongo: {e}")

    def run(self):
        if not self.db_client.is_healthy():
            return

        repos = settings.repos_list
        for repo in repos:
            print(f"\n--- Démarrage {repo} ---")
            count = 0
            for batch in self.fetch_repo_issues(repo):
                self.save_batch(batch)
                count += len(batch)
                print(f"\r{count} issues mises à jour/insérées...", end="")
            print(f"\nTerminé pour {repo}.")


if __name__ == "__main__":
    GitHubCollector().run()
