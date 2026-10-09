from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Blacklist:
    def __init__(self, path: Path, *, initial_usernames: frozenset[str] = frozenset(), initial_ids: frozenset[int] = frozenset()) -> None:
        self.path = path
        self.usernames: set[str] = {u.lower().lstrip("@") for u in initial_usernames}
        self.user_ids: set[int] = set(initial_ids)
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to read blacklist %s", self.path)
            return
        for u in data.get("usernames") or []:
            if isinstance(u, str) and u.strip():
                self.usernames.add(u.strip().lower().lstrip("@"))
        for i in data.get("user_ids") or []:
            try:
                self.user_ids.add(int(i))
            except (TypeError, ValueError):
                continue
        logger.info(
            "Blacklist loaded: %s username(s), %s id(s)",
            len(self.usernames),
            len(self.user_ids),
        )

    def _save(self) -> None:
        data = {
            "usernames": sorted(self.usernames),
            "user_ids": sorted(self.user_ids),
        }
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            logger.exception("Failed to save blacklist %s", self.path)

    def is_blocked(self, *, username: str | None, user_id: int | None) -> bool:
        if username:
            name = username.strip().lower().lstrip("@")
            if name and name in self.usernames:
                return True
        if user_id is not None and int(user_id) in self.user_ids:
            return True
        return False

    def add_username(self, username: str) -> bool:
        name = username.strip().lower().lstrip("@")
        if not name:
            return False
        if name in self.usernames:
            return False
        self.usernames.add(name)
        self._save()
        return True

    def add_user_id(self, user_id: int) -> bool:
        uid = int(user_id)
        if uid in self.user_ids:
            return False
        self.user_ids.add(uid)
        self._save()
        return True

    def remove_username(self, username: str) -> bool:
        name = username.strip().lower().lstrip("@")
        if name not in self.usernames:
            return False
        self.usernames.discard(name)
        self._save()
        return True

    def remove_user_id(self, user_id: int) -> bool:
        uid = int(user_id)
        if uid not in self.user_ids:
            return False
        self.user_ids.discard(uid)
        self._save()
        return True

    def list_all(self) -> dict[str, list]:
        return {
            "usernames": sorted(self.usernames),
            "user_ids": sorted(self.user_ids),
        }