# `iqra/core/memory_store.py`

> 路径：`iqra/core/memory_store.py` | 行数：442


---


```python
"""
Iqra Memory Store - Enhanced Edition

Features:
- Session persistence with metadata (title, tags, created_at)
- Full-text search across sessions
- Session statistics and analytics
- Memory export/import for backup
- Automatic session cleanup
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MemoryStore:
    """Enhanced memory store with search, metadata, and analytics."""
    
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            self.base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "iqra"
            )
        else:
            self.base_dir = base_dir
        self.sessions_dir = os.path.join(self.base_dir, "sessions")
        self.memory_dir = os.path.join(self.base_dir, "memory")
        self.exports_dir = os.path.join(self.base_dir, "exports")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create required directories."""
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)

    def on_session_start(self, session_id: str) -> None:
        """Called when a session begins."""
        pass

    def on_session_end(self, session_id: str) -> None:
        """Called when a session ends (before final save)."""
        pass

    # ── Session Management ──────────────────────────────────

    def save_session(self, messages: List[Dict[str, Any]], session_id: str = "default",
                     title: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """Save a conversation session with optional metadata."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        # Load existing metadata if updating
        existing_meta = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    existing_meta = {
                        "created_at": existing.get("created_at"),
                        "title": existing.get("title"),
                        "tags": existing.get("tags", []),
                        "pinned": existing.get("pinned", False),
                    }
            except Exception:
                pass
        
        # Auto-generate title from first user message if not set
        if not title and not existing_meta.get("title"):
            title = self._generate_title(messages)
        
        now = datetime.now().isoformat()
        data = {
            "session_id": session_id,
            "created_at": existing_meta.get("created_at", now),
            "updated_at": now,
            "title": title or existing_meta.get("title", "Untitled"),
            "tags": tags or existing_meta.get("tags", []),
            "pinned": existing_meta.get("pinned", False),
            "message_count": len(messages),
            "messages": messages,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Session saved: {session_id} ({len(messages)} msgs)")
        return filepath

    def load_session(self, session_id: str = "default") -> List[Dict[str, Any]]:
        """Load messages from a session."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("messages", [])
        except Exception as e:
            logger.warning(f"Failed to load session {session_id}: {e}")
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata without loading all messages."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "id": data.get("session_id", session_id),
                "title": data.get("title", "Untitled"),
                "tags": data.get("tags", []),
                "pinned": data.get("pinned", False),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": data.get("message_count", 0),
            }
        except Exception:
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with metadata, sorted by update time."""
        sessions = []
        if not os.path.exists(self.sessions_dir):
            return sessions
        for fname in os.listdir(self.sessions_dir):
            if fname.endswith(".json"):
                info = self.get_session_info(fname[:-5])
                if info:
                    sessions.append(info)
        sessions.sort(key=lambda x: (x.get("pinned", False), x.get("updated_at", "")), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Session deleted: {session_id}")
            return True
        return False

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """Rename a session title."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["title"] = new_title
            data["updated_at"] = datetime.now().isoformat()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to rename session {session_id}: {e}")
            return False

    def toggle_pin_session(self, session_id: str) -> bool:
        """Toggle the pinned state of a session. Returns True if now pinned, False if unpinned."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            current = data.get("pinned", False)
            data["pinned"] = not current
            data["updated_at"] = datetime.now().isoformat()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return not current
        except Exception as e:
            logger.error(f"Failed to toggle pin session {session_id}: {e}")
            return False

    def tag_session(self, session_id: str, tags: List[str]) -> bool:
        """Set tags for a session."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["tags"] = list(set(tags))  # deduplicate
            data["updated_at"] = datetime.now().isoformat()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to tag session {session_id}: {e}")
            return False

    # ── Search ──────────────────────────────────────────────

    def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across all sessions. Returns matching sessions with snippets."""
        results = []
        query_lower = query.lower()
        query_pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        for fname in os.listdir(self.sessions_dir):
            if not fname.endswith(".json"):
                continue
            filepath = os.path.join(self.sessions_dir, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                session_id = data.get("session_id", fname[:-5])
                title = data.get("title", "Untitled")
                messages = data.get("messages", [])
                
                # Search in title
                title_matches = len(query_pattern.findall(title))
                
                # Search in messages
                snippets = []
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, str) and query_lower in content.lower():
                        # Extract snippet around match
                        idx = content.lower().find(query_lower)
                        start = max(0, idx - 40)
                        end = min(len(content), idx + len(query) + 40)
                        snippet = content[start:end].replace("\n", " ").strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet += "..."
                        snippets.append({
                            "role": msg.get("role", "unknown"),
                            "text": snippet,
                        })
                
                if title_matches > 0 or snippets:
                    results.append({
                        "id": session_id,
                        "title": title,
                        "updated_at": data.get("updated_at", ""),
                        "match_count": title_matches + len(snippets),
                        "snippets": snippets[:3],  # Top 3 snippets
                    })
            except Exception as e:
                logger.debug(f"Search failed for {fname}: {e}")
                continue
        
        # Sort by relevance (match count) then by time
        results.sort(key=lambda x: (x["match_count"], x["updated_at"]), reverse=True)
        return results[:limit]

    def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find all sessions with a specific tag."""
        results = []
        tag_lower = tag.lower()
        for session in self.list_sessions():
            session_tags = [t.lower() for t in session.get("tags", [])]
            if tag_lower in session_tags:
                results.append(session)
        return results

    # ── Statistics ──────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about stored sessions."""
        sessions = self.list_sessions()
        total_messages = sum(s.get("message_count", 0) for s in sessions)
        
        # Collect all unique tags
        all_tags = set()
        for s in sessions:
            all_tags.update(s.get("tags", []))
        
        # Date range
        dates = [s.get("updated_at", "") for s in sessions if s.get("updated_at")]
        oldest = min(dates) if dates else None
        newest = max(dates) if dates else None
        
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "unique_tags": sorted(all_tags),
            "oldest_session": oldest,
            "newest_session": newest,
            "avg_messages_per_session": round(total_messages / max(len(sessions), 1), 1),
        }

    # ── Cleanup ─────────────────────────────────────────────

    def cleanup_old_sessions(self, days: int = 30, keep_min: int = 10) -> int:
        """Remove sessions older than `days` days, keeping at least `keep_min` sessions."""
        sessions = self.list_sessions()
        if len(sessions) <= keep_min:
            return 0
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        removed = 0
        
        for session in sessions[keep_min:]:  # Skip newest `keep_min`
            if session.get("updated_at", "") < cutoff:
                self.delete_session(session["id"])
                removed += 1
        
        logger.info(f"Cleaned up {removed} old sessions (>{days} days)")
        return removed

    # ── Export / Import ─────────────────────────────────────

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a session to a file. Returns the export file path."""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            export_path = os.path.join(self.exports_dir, f"session_{session_id}_{timestamp}.json")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return export_path
        
        elif format == "markdown":
            export_path = os.path.join(self.exports_dir, f"session_{session_id}_{timestamp}.md")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            lines = [f"# {data.get('title', session_id)}\n"]
            lines.append(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
            lines.append("---\n")
            
            for msg in data.get("messages", []):
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                if isinstance(content, str):
                    lines.append(f"\n### {role}\n")
                    lines.append(content)
                    lines.append("")
            
            with open(export_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return export_path
        
        return None

    def import_session(self, import_path: str, session_id: Optional[str] = None) -> Optional[str]:
        """Import a session from an exported JSON file. Returns the new session ID."""
        if not os.path.exists(import_path):
            return None
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            new_id = session_id or data.get("session_id", f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            data["session_id"] = new_id
            data["imported_at"] = datetime.now().isoformat()
            
            filepath = os.path.join(self.sessions_dir, f"{new_id}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Session imported: {new_id} from {import_path}")
            return new_id
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return None

    # ── Persistent Memory (Markdown) ────────────────────────

    def _memory_path(self, name: str) -> str:
        return os.path.join(self.memory_dir, f"{name}.md")

    def read_memory(self, name: str) -> str:
        """Read a persistent memory file."""
        path = self._memory_path(name)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_memory(self, name: str, content: str) -> str:
        """Write a persistent memory file."""
        path = self._memory_path(name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def append_memory(self, name: str, content: str) -> str:
        """Append timestamped content to a memory file."""
        path = self._memory_path(name)
        existing = self.read_memory(name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_content = f"{existing}\n\n## {timestamp}\n\n{content}".strip()
        return self.write_memory(name, new_content)

    def list_memories(self) -> List[str]:
        """List all memory file names (without extension)."""
        if not os.path.exists(self.memory_dir):
            return []
        return [f[:-3] for f in os.listdir(self.memory_dir) if f.endswith(".md")]

    def delete_memory(self, name: str) -> bool:
        """Delete a memory file."""
        path = self._memory_path(name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_personalized_context(self) -> Optional[str]:
        """获取用户个性化上下文（称呼、人设偏好等）"""
        try:
            ctx = self.read_memory("user_persona")
            if ctx and ctx.strip():
                return ctx.strip()
        except Exception:
            pass
        return None

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _generate_title(messages: List[Dict[str, Any]], max_len: int = 50) -> str:
        """Auto-generate a session title from the first user message."""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    # Take first line, truncate
                    first_line = content.strip().split("\n")[0]
                    if len(first_line) > max_len:
                        return first_line[:max_len - 3] + "..."
                    return first_line or "Untitled"
        return "Untitled"

```
