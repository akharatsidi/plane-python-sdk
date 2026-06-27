from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..models.projects import (
    CreateProject,
    PaginatedProjectResponse,
    Project,
    ProjectFeature,
    ProjectMember,
    ProjectWorklogSummary,
    UpdateProject,
)
from ..models.query_params import PaginatedQueryParams
from .base_resource import BaseResource


class Projects(BaseResource):
    def __init__(self, config: Any) -> None:
        super().__init__(config, "/workspaces/")

    def create(self, workspace_slug: str, data: CreateProject) -> Project:
        """Create a new project.

        Args:
            workspace_slug: The workspace slug identifier
            data: Project data
        """
        response = self._post(f"{workspace_slug}/projects", data.model_dump(exclude_none=True))
        return Project.model_validate(response)

    def retrieve(self, workspace_slug: str, project_id: str) -> Project:
        """Retrieve a project by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
        """
        response = self._get(f"{workspace_slug}/projects/{project_id}")
        return Project.model_validate(response)

    def update(self, workspace_slug: str, project_id: str, data: UpdateProject) -> Project:
        """Update a project by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            data: Updated project data
        """
        response = self._patch(
            f"{workspace_slug}/projects/{project_id}", data.model_dump(exclude_none=True)
        )
        return Project.model_validate(response)

    def delete(self, workspace_slug: str, project_id: str) -> None:
        """Delete a project by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
        """
        return self._delete(f"{workspace_slug}/projects/{project_id}")

    def list(
        self, workspace_slug: str, params: PaginatedQueryParams | None = None
    ) -> PaginatedProjectResponse:
        """List projects with optional filtering parameters.

        Args:
            workspace_slug: The workspace slug identifier
            params: Optional query parameters
        """
        query_params = params.model_dump(exclude_none=True) if params else None
        response = self._get(f"{workspace_slug}/projects", params=query_params)
        return PaginatedProjectResponse.model_validate(response)

    def get_worklog_summary(self, workspace_slug: str, project_id: str) -> [ProjectWorklogSummary]:
        """Get work log summary for a project.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
        """
        response = self._get(f"{workspace_slug}/projects/{project_id}/total-worklogs")
        return [ProjectWorklogSummary.model_validate(item) for item in response]

    def get_members(
        self, workspace_slug: str, project_id: str, params: Mapping[str, Any] | None = None
    ) -> list[ProjectMember]:
        """Get all members of a project.

        Returns a list of ProjectMember objects that include role (int) and
        role_slug (str) fields in addition to basic identity fields.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            params: Optional query parameters
        """
        response = self._get(f"{workspace_slug}/projects/{project_id}/members", params=params)
        return [ProjectMember.model_validate(item) for item in response or []]

    def get_features(self, workspace_slug: str, project_id: str) -> ProjectFeature:
        """Get features of a project.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
        """
        response = self._get(f"{workspace_slug}/projects/{project_id}/features")
        return ProjectFeature.model_validate(response)

    def update_features(
        self, workspace_slug: str, project_id: str, data: ProjectFeature
    ) -> ProjectFeature:
        """Update features of a project.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            data: Updated project features
        """
        response = self._patch(
            f"{workspace_slug}/projects/{project_id}/features", data.model_dump(exclude_none=True)
        )
        return ProjectFeature.model_validate(response)

    def archive(self, workspace_slug: str, project_id: str) -> None:
        """Archive a project.

        Move a project to archived status, hiding it from active project lists.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project

        Returns:
            None (HTTP 204 No Content)
        """
        self._post(f"{workspace_slug}/projects/{project_id}/archive", {})

    def unarchive(self, workspace_slug: str, project_id: str) -> None:
        """Unarchive a project.

        Restore an archived project to active status, making it available
        in regular workflows.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project

        Returns:
            None (HTTP 204 No Content)
        """
        self._delete(f"{workspace_slug}/projects/{project_id}/archive")

    def add_member(
        self, workspace_slug: str, project_id: str, member_id: str, role: int
    ) -> dict:
        """Add a member to a project.

        POST ``{slug}/projects/{pid}/members`` with body
        ``{member, role}``. Returns the raw project-member dict from the
        backend.

        Role is an integer: ADMIN=20, MEMBER=15, GUEST=5.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            member_id: User UUID to add as a project member
            role: Project role as an int (ADMIN=20, MEMBER=15, GUEST=5)
        """
        return self._post(
            f"{workspace_slug}/projects/{project_id}/members",
            {"member": member_id, "role": role},
        )

    def update_member(
        self, workspace_slug: str, project_id: str, member_pk: str, role: int
    ) -> dict:
        """Update a project member's role.

        PATCH ``{slug}/projects/{pid}/members/{member_pk}`` with body
        ``{role}``. Returns the raw updated project-member dict.

        Role is an integer: ADMIN=20, MEMBER=15, GUEST=5.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            member_pk: Primary key of the project-member record
            role: Project role as an int (ADMIN=20, MEMBER=15, GUEST=5)
        """
        return self._patch(
            f"{workspace_slug}/projects/{project_id}/members/{member_pk}",
            {"role": role},
        )

    def remove_member(
        self, workspace_slug: str, project_id: str, member_pk: str
    ) -> None:
        """Remove a member from a project.

        DELETE ``{slug}/projects/{pid}/members/{member_pk}``.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            member_pk: Primary key of the project-member record to remove
        """
        return self._delete(
            f"{workspace_slug}/projects/{project_id}/members/{member_pk}"
        )

