from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.trilium import trilium_service


def register_trilium_tools(server) -> None:
    """Registers TriliumNext note management and knowledge base tools."""

    @server.tool()
    async def trilium_search_notes(
        query: str,
        fast_search: bool = False,
        include_archived: bool = False,
        limit: int = 25,
    ) -> str:
        """Searches notes in TriliumNext by title, content, or advanced Trilium syntax (e.g. #tag, #status=done).

        Args:
            query: Search query or label selector.
            fast_search: If True, uses prefix match on title only.
            include_archived: Whether to include archived notes (default False).
            limit: Maximum notes to return (default 25).
        """
        logger.info(f"Executing trilium_search_notes: query='{query}'")
        res = await trilium_service.search_notes(
            query=query,
            fast_search=fast_search,
            include_archived=include_archived,
            limit=limit,
        )
        return to_pretty_json(res)

    @server.tool()
    async def trilium_get_note(note_id: str, include_content: bool = True) -> str:
        """Gets complete details of a note including its labels, relations, and content.

        Args:
            note_id: The Trilium note ID.
            include_content: Whether to fetch the full text/HTML note content (default True).
        """
        logger.info(f"Executing trilium_get_note: note_id='{note_id}'")
        res = await trilium_service.get_note(note_id=note_id, include_content=include_content)
        return to_pretty_json(res)

    @server.tool()
    async def trilium_get_note_tree(parent_note_id: str = "root") -> str:
        """Navigates the note tree by listing child notes under a given parent note ID (default 'root').

        Args:
            parent_note_id: The parent note ID to explore (default 'root').
        """
        logger.info(f"Executing trilium_get_note_tree: parent='{parent_note_id}'")
        res = await trilium_service.get_note_tree(parent_note_id=parent_note_id)
        return to_pretty_json(res)

    @server.tool()
    async def trilium_create_note(
        title: str,
        content: str = "",
        parent_note_id: str = "root",
        note_type: str = "text",
    ) -> str:
        """Creates a new note under a parent note in TriliumNext.

        Args:
            title: The title of the note.
            content: Note body (text or HTML).
            parent_note_id: Parent note ID (defaults to 'root').
            note_type: 'text', 'code', 'mermaid', 'book', etc. (default 'text').
        """
        logger.info(f"Executing trilium_create_note: title='{title}', parent='{parent_note_id}'")
        res = await trilium_service.create_note(
            parent_note_id=parent_note_id,
            title=title,
            content=content,
            note_type=note_type,
        )
        return to_pretty_json(res)

    @server.tool()
    async def trilium_update_note(
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        append: bool = False,
    ) -> str:
        """Updates a note title or content (overwrite or append).

        Args:
            note_id: The Trilium note ID.
            title: Optional new title.
            content: Optional new content.
            append: If True, appends content to the existing note body instead of overwriting (default False).
        """
        logger.info(f"Executing trilium_update_note: note_id='{note_id}', append={append}")
        res = await trilium_service.update_note(note_id=note_id, title=title, content=content, append=append)
        return to_pretty_json(res)

    @server.tool()
    async def trilium_delete_note(note_id: str) -> str:
        """Deletes a note from TriliumNext by note ID.

        Args:
            note_id: The Trilium note ID to delete.
        """
        logger.info(f"Executing trilium_delete_note: note_id='{note_id}'")
        res = await trilium_service.delete_note(note_id=note_id)
        return to_pretty_json(res)

    @server.tool()
    async def trilium_get_daily_note(target_date: Optional[str] = None) -> str:
        """Gets or initializes the Daily Journal note for a given date (defaults to today: YYYY-MM-DD).

        Use this whenever the user wants to log notes or to-do items into their daily journal.

        Args:
            target_date: Optional date in YYYY-MM-DD format (defaults to current date).
        """
        logger.info(f"Executing trilium_get_daily_note: date='{target_date}'")
        res = await trilium_service.get_daily_note(target_date=target_date)
        return to_pretty_json(res)

    @server.tool()
    async def trilium_manage_attributes(
        note_id: str,
        action: str,
        attr_type: str = "label",
        name: str = "",
        value: str = "",
        attribute_id: Optional[str] = None,
    ) -> str:
        """Adds or deletes labels and relations on a note in TriliumNext.

        Args:
            note_id: The Trilium note ID.
            action: 'add' or 'delete'.
            attr_type: 'label' or 'relation' (default 'label').
            name: Name of the label (e.g. 'project', 'priority').
            value: Value of the label (e.g. 'homelab', 'high').
            attribute_id: The ID of the attribute to delete (required if action is 'delete').
        """
        logger.info(f"Executing trilium_manage_attributes: note_id='{note_id}', action='{action}'")
        res = await trilium_service.manage_attributes(
            note_id=note_id,
            action=action,
            attr_type=attr_type,
            name=name,
            value=value,
            attribute_id=attribute_id,
        )
        return to_pretty_json(res)

    @server.tool()
    async def trilium_get_app_info() -> str:
        """Retrieves TriliumNext application version and sync status."""
        logger.info("Executing trilium_get_app_info")
        res = await trilium_service.get_app_info()
        return to_pretty_json(res)

    logger.debug("Registered Trilium tools.")

