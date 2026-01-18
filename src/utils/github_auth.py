import logging
import time
from itertools import cycle
from typing import List

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self, tokens: List[str]):
        if not tokens:
            raise ValueError("Aucun token GitHub fourni dans la configuration.")

        # Cycle permet de tourner indéfiniment : [1, 2, 3] -> 1, 2, 3, 1, 2...
        self._tokens_cycle = cycle(tokens)
        self._current_token = next(self._tokens_cycle)
        self._total_tokens = len(tokens)
        self._switch_count = 0

    def get_token(self) -> str:
        return self._current_token

    def rotate(self):
        """Passe au token suivant."""
        self._current_token = next(self._tokens_cycle)
        self._switch_count += 1
        logger.warning(
            f"Rotation de token effectuée. "
            f"(Token #{self._switch_count % self._total_tokens + 1})"
        )

    def handle_rate_limit(self):
        """
        Appelé quand un token est cramé.
        Si on a fait un tour complet de tous les tokens, on dort.
        """
        self.rotate()
        # Si on a épuisé tous les tokens (nombre de switchs > nombre de tokens)
        # on attend
        if self._switch_count > 0 and (self._switch_count % self._total_tokens == 0):
            wait_time = 60 * 10  # 10 minutes
            logger.warning(f"Tous les tokens sont épuisés. Pause de {wait_time}s...")
            time.sleep(wait_time)
