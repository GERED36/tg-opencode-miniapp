import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SESSIONS_FILE = Path(__file__).resolve().parent.parent / "user_sessions.json"
CONTEXTS_FILE = Path(__file__).resolve().parent.parent / "user_contexts.json"


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, bool] = {}
        self._contexts: dict[int, str] = {}
        self._load_sessions()
        self._load_contexts()

    # --- Sessions ---

    def _load_sessions(self) -> None:
        if not SESSIONS_FILE.exists():
            self._sessions = {}
            return
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._sessions = {int(k): bool(v) for k, v in raw.items()}
            logger.info("Loaded %d user sessions", len(self._sessions))
        except Exception as e:
            self._backup_corrupted(SESSIONS_FILE)
            logger.warning("Failed to load sessions, reset: %s", e)
            self._sessions = {}

    def _save_sessions(self) -> None:
        try:
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save sessions: %s", e)

    def has_session(self, user_id: int) -> bool:
        return self._sessions.get(user_id, False)

    def mark_session_started(self, user_id: int) -> None:
        self._sessions[user_id] = True
        self._save_sessions()

    def reset_session(self, user_id: int) -> None:
        self._sessions[user_id] = False
        self._save_sessions()

    def delete_session(self, user_id: int) -> bool:
        if user_id in self._sessions:
            del self._sessions[user_id]
            self._save_sessions()
            return True
        return False

    def delete_all_sessions(self, user_id: int) -> bool:
        removed = False
        for uid in list(self._sessions.keys()):
            if uid == user_id or user_id == 0:
                del self._sessions[uid]
                removed = True
        if removed:
            self._save_sessions()
        return removed

    # --- Contexts ---

    def _load_contexts(self) -> None:
        if not CONTEXTS_FILE.exists():
            self._contexts = {}
            return
        try:
            with open(CONTEXTS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._contexts = {int(k): str(v) for k, v in raw.items()}
            logger.info("Loaded %d user contexts", len(self._contexts))
        except Exception as e:
            self._backup_corrupted(CONTEXTS_FILE)
            logger.warning("Failed to load contexts, reset: %s", e)
            self._contexts = {}

    def _save_contexts(self) -> None:
        try:
            with open(CONTEXTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._contexts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save contexts: %s", e)

    def get_context(self, user_id: int) -> str:
        return self._contexts.get(user_id, "")

    def set_context(self, user_id: int, text: str) -> None:
        if text:
            self._contexts[user_id] = text
        else:
            self._contexts.pop(user_id, None)
        self._save_contexts()

    def delete_context(self, user_id: int) -> bool:
        if user_id in self._contexts:
            del self._contexts[user_id]
            self._save_contexts()
            return True
        return False

    # --- Helpers ---

    @staticmethod
    def _backup_corrupted(path: Path) -> None:
        try:
            bak = path.with_suffix(path.suffix + ".bak")
            path.rename(bak)
            logger.info("Backed up corrupted %s to %s", path.name, bak.name)
        except Exception:
            pass

    def get_all_active_users(self) -> list[int]:
        return [uid for uid, active in self._sessions.items() if active]

    def get_connected_user_ids(self) -> set[int]:
        return {uid for uid, active in self._sessions.items() if active}
