from datetime import date
from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient


class TriliumService(BaseServiceClient):
    """Asynchronous client for TriliumNext ETAPI."""

    def __init__(self) -> None:
        headers = {}
        if settings.TRILIUM_ETAPI_TOKEN:
            headers["Authorization"] = settings.TRILIUM_ETAPI_TOKEN

        super().__init__(
            service_name="TriliumNext",
            base_url=settings.TRILIUM_URL,
            default_headers=headers,
        )

    async def search_notes(
        self,
        query: str,
        fast_search: bool = False,
        include_archived: bool = False,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        params = {
            "search": query,
            "fastSearch": "true" if fast_search else "false",
            "includeArchived": "true" if include_archived else "false",
        }
        res = await self.request("GET", "/etapi/notes", params=params)
        results = res.get("results", []) if isinstance(res, dict) else []
        formatted = []
        for n in results[:limit]:
            formatted.append(
                {
                    "noteId": n.get("noteId"),
                    "title": n.get("title"),
                    "type": n.get("type"),
                    "dateModified": n.get("dateModified"),
                    "isArchived": n.get("isArchived", False),
                }
            )
        return formatted

    async def get_note(self, note_id: str, include_content: bool = True) -> dict[str, Any]:
        note = await self.request("GET", f"/etapi/notes/{note_id}")
        data = {
            "noteId": note.get("noteId"),
            "title": note.get("title"),
            "type": note.get("type"),
            "mime": note.get("mime"),
            "isProtected": note.get("isProtected", False),
            "dateCreated": note.get("dateCreated"),
            "dateModified": note.get("dateModified"),
            "attributes": [
                {"type": a.get("type"), "name": a.get("name"), "value": a.get("value")}
                for a in note.get("attributes", [])
            ],
            "parentNoteIds": note.get("parentNoteIds", []),
            "childNoteIds": note.get("childNoteIds", []),
        }
        if include_content:
            try:
                content = await self.request("GET", f"/etapi/notes/{note_id}/content")
                data["content"] = content if isinstance(content, str) else str(content)
            except Exception as exc:
                data["content_error"] = str(exc)
        return data

    async def get_note_tree(self, parent_note_id: str = "root") -> dict[str, Any]:
        note = await self.request("GET", f"/etapi/notes/{parent_note_id}")
        children = []
        for child_id in note.get("childNoteIds", [])[:40]:
            try:
                child = await self.request("GET", f"/etapi/notes/{child_id}")
                children.append(
                    {
                        "noteId": child.get("noteId"),
                        "title": child.get("title"),
                        "type": child.get("type"),
                        "childCount": len(child.get("childNoteIds", [])),
                    }
                )
            except Exception:
                continue

        return {
            "parentNoteId": parent_note_id,
            "parentTitle": note.get("title"),
            "children": children,
        }

    async def create_note(
        self,
        parent_note_id: str = "root",
        title: str = "Untitled Note",
        content: str = "",
        note_type: str = "text",
        mime: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "parentNoteId": parent_note_id,
            "title": title,
            "type": note_type,
            "content": content,
        }
        if mime:
            payload["mime"] = mime
        created = await self.request("POST", "/etapi/create-note", json_data=payload)
        return {"status": "created", "note": created.get("note", created)}

    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        append: bool = False,
    ) -> dict[str, Any]:
        if title is not None:
            await self.request("PATCH", f"/etapi/notes/{note_id}", json_data={"title": title})
        if content is not None:
            if append:
                existing = await self.request("GET", f"/etapi/notes/{note_id}/content")
                existing_str = existing if isinstance(existing, str) else str(existing)
                content = f"{existing_str}\n{content}"
            await self.request(
                "PUT",
                f"/etapi/notes/{note_id}/content",
                data=content.encode("utf-8"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
            )
        return {"status": "updated", "noteId": note_id}

    async def delete_note(self, note_id: str) -> dict[str, Any]:
        await self.request("DELETE", f"/etapi/notes/{note_id}")
        return {"status": "deleted", "noteId": note_id}

    async def get_daily_note(self, target_date: Optional[str] = None) -> dict[str, Any]:
        day_str = target_date or date.today().isoformat()
        res = await self.request("GET", f"/etapi/calendar/days/{day_str}")
        note = res.get("note") or res
        return {
            "date": day_str,
            "noteId": note.get("noteId"),
            "title": note.get("title"),
            "type": note.get("type"),
        }

    async def manage_attributes(
        self,
        note_id: str,
        action: str,
        attr_type: str = "label",
        name: str = "",
        value: str = "",
        attribute_id: Optional[str] = None,
    ) -> dict[str, Any]:
        act_lower = action.lower()
        if act_lower in ["add", "create"]:
            payload = {
                "noteId": note_id,
                "type": attr_type,
                "name": name,
                "value": value,
            }
            res = await self.request("POST", "/etapi/attributes", json_data=payload)
            return {"status": "created", "attribute": res}
        if act_lower in ["delete", "remove"]:
            if not attribute_id:
                raise ValueError("attribute_id is required to delete an attribute.")
            await self.request("DELETE", f"/etapi/attributes/{attribute_id}")
            return {"status": "deleted", "attributeId": attribute_id}
        raise ValueError("action must be 'add' or 'delete'.")

    async def get_app_info(self) -> dict[str, Any]:
        app_info = await self.request("GET", "/etapi/app-info")
        return app_info if isinstance(app_info, dict) else {}


trilium_service = TriliumService()

