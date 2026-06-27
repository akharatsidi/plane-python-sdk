from collections.abc import Mapping
from typing import Any

from ..models.views import CreateView, UpdateView, View
from .base_resource import BaseResource


class Views(BaseResource):
    """Saved views (filters) resource.

    Covers both project views and workspace-level views. When
    ``project_id`` is ``None`` the workspace path is used:

    - project:   /workspaces/<slug>/projects/<project_id>/views/[<pk>/]
    - workspace: /workspaces/<slug>/views/[<pk>/]

    ``BaseResource._build_url`` appends the trailing slash, so the paths
    here are passed WITHOUT one.
    """

    def __init__(self, config: Any) -> None:
        super().__init__(config, "/workspaces/")

    def _collection_path(self, workspace_slug: str, project_id: str | None) -> str:
        if project_id is None:
            return f"{workspace_slug}/views"
        return f"{workspace_slug}/projects/{project_id}/views"

    def _detail_path(
        self, workspace_slug: str, view_id: str, project_id: str | None
    ) -> str:
        return f"{self._collection_path(workspace_slug, project_id)}/{view_id}"

    def list(
        self,
        workspace_slug: str,
        project_id: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[View]:
        """List views in a project, or workspace views when ``project_id`` is None.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project, or None for workspace views
            params: Optional query parameters
        """
        response = self._get(
            self._collection_path(workspace_slug, project_id), params=params
        )
        return [View.model_validate(item) for item in self._as_items(response)]

    def create(
        self,
        workspace_slug: str,
        data: CreateView,
        project_id: str | None = None,
    ) -> View:
        """Create a view in a project, or a workspace view when ``project_id`` is None.

        Args:
            workspace_slug: The workspace slug identifier
            data: View data
            project_id: UUID of the project, or None for a workspace view
        """
        response = self._post(
            self._collection_path(workspace_slug, project_id),
            data.model_dump(exclude_none=True),
        )
        return View.model_validate(response)

    def retrieve(
        self,
        workspace_slug: str,
        view_id: str,
        project_id: str | None = None,
    ) -> View:
        """Retrieve a view by ID.

        Args:
            workspace_slug: The workspace slug identifier
            view_id: UUID of the view
            project_id: UUID of the project, or None for a workspace view
        """
        response = self._get(self._detail_path(workspace_slug, view_id, project_id))
        return View.model_validate(response)

    def update(
        self,
        workspace_slug: str,
        view_id: str,
        data: UpdateView,
        project_id: str | None = None,
    ) -> View:
        """Update a view by ID.

        Args:
            workspace_slug: The workspace slug identifier
            view_id: UUID of the view
            data: Updated view data
            project_id: UUID of the project, or None for a workspace view
        """
        response = self._patch(
            self._detail_path(workspace_slug, view_id, project_id),
            data.model_dump(exclude_none=True),
        )
        return View.model_validate(response)

    def delete(
        self,
        workspace_slug: str,
        view_id: str,
        project_id: str | None = None,
    ) -> None:
        """Delete a view by ID.

        Args:
            workspace_slug: The workspace slug identifier
            view_id: UUID of the view
            project_id: UUID of the project, or None for a workspace view
        """
        return self._delete(self._detail_path(workspace_slug, view_id, project_id))
