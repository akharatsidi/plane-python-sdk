from __future__ import annotations

from typing import Any

from ..models.workspaces import WorkspaceFeature, WorkspaceMember
from .base_resource import BaseResource


class Workspaces(BaseResource):
    def __init__(self, config: Any) -> None:
        super().__init__(config, "/workspaces/")

    def get_members(
        self, workspace_slug: str
    ) -> list[WorkspaceMember]:
        """Get all members of a workspace.

        Returns a list of WorkspaceMember objects that include role (int) and
        role_slug (str) fields in addition to basic identity fields.

        Args:
            workspace_slug: The workspace slug identifier
        """
        response = self._get(f"{workspace_slug}/members")
        return [WorkspaceMember.model_validate(item) for item in response or []]

    def get_features(self, workspace_slug: str) -> WorkspaceFeature:
        """Get features of a workspace.

        Args:
            workspace_slug: The workspace slug identifier
        """
        response = self._get(f"{workspace_slug}/features")
        return WorkspaceFeature.model_validate(response)
    
    def update_features(self, workspace_slug: str, data: WorkspaceFeature) -> WorkspaceFeature:
        """Update features of a workspace.

        Args:
            workspace_slug: The workspace slug identifier
            data: Updated workspace features
        """
        response = self._patch(f"{workspace_slug}/features", data.model_dump(exclude_none=True))
        return WorkspaceFeature.model_validate(response)

    def create_invite(self, workspace_slug: str, email: str, role: int) -> dict:
        """Invite a user to a workspace by email.

        POST ``{slug}/invitations`` with body ``{email, role}``. Returns the
        raw invitation dict as sent by the backend.

        Role is an integer: ADMIN=20, MEMBER=15, GUEST=5.

        Args:
            workspace_slug: The workspace slug identifier
            email: Email address of the invitee
            role: Workspace role as an int (ADMIN=20, MEMBER=15, GUEST=5)
        """
        return self._post(
            f"{workspace_slug}/invitations", {"email": email, "role": role}
        )

    def list_invites(self, workspace_slug: str) -> list:
        """List pending invitations for a workspace.

        GET ``{slug}/invitations``. Unwraps a paginated envelope
        (``{"results": [...]}``) to a bare list via ``_as_items``.

        Args:
            workspace_slug: The workspace slug identifier
        """
        response = self._get(f"{workspace_slug}/invitations")
        return self._as_items(response)

    def delete_invite(self, workspace_slug: str, invitation_id: str) -> None:
        """Revoke a pending workspace invitation.

        DELETE ``{slug}/invitations/{invitation_id}``.

        Args:
            workspace_slug: The workspace slug identifier
            invitation_id: UUID of the invitation to revoke
        """
        return self._delete(f"{workspace_slug}/invitations/{invitation_id}")