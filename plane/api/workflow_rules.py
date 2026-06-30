from collections.abc import Mapping
from typing import Any

from .base_resource import BaseResource


class WorkflowRules(BaseResource):
    """API client for the ENCY per-project workflow *transition rules* and
    *approvals* feature (distinct from upstream Plane ``Workflows``).

    Targets the public v1 endpoints:
      - ``projects/{id}/workflow-transitions/`` — transition-rule CRUD
      - ``projects/{id}/issues/{iid}/approvals/`` — list / request approvals
      - ``projects/{id}/approvals/{aid}/votes/`` — cast a vote

    Payloads/results are plain dicts (the v1 endpoints return the app serializer
    shape directly); no typed models are required.
    """

    def __init__(self, config: Any) -> None:
        super().__init__(config, "/workspaces/")

    # --- transition rules ---
    def list_transitions(self, workspace_slug: str, project_id: str) -> list[dict[str, Any]]:
        return self._get(f"{workspace_slug}/projects/{project_id}/workflow-transitions")

    def create_transition(
        self, workspace_slug: str, project_id: str, data: Mapping[str, Any]
    ) -> dict[str, Any]:
        return self._post(f"{workspace_slug}/projects/{project_id}/workflow-transitions", dict(data))

    def update_transition(
        self, workspace_slug: str, project_id: str, transition_id: str, data: Mapping[str, Any]
    ) -> dict[str, Any]:
        return self._patch(
            f"{workspace_slug}/projects/{project_id}/workflow-transitions/{transition_id}", dict(data)
        )

    def delete_transition(self, workspace_slug: str, project_id: str, transition_id: str) -> None:
        self._delete(f"{workspace_slug}/projects/{project_id}/workflow-transitions/{transition_id}")

    # --- approvals ---
    def list_approvals(self, workspace_slug: str, project_id: str, issue_id: str) -> list[dict[str, Any]]:
        return self._get(f"{workspace_slug}/projects/{project_id}/issues/{issue_id}/approvals")

    def request_approval(
        self, workspace_slug: str, project_id: str, issue_id: str, target_state: str
    ) -> dict[str, Any]:
        return self._post(
            f"{workspace_slug}/projects/{project_id}/issues/{issue_id}/approvals",
            {"target_state": target_state},
        )

    def vote_approval(
        self,
        workspace_slug: str,
        project_id: str,
        approval_id: str,
        decision: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            f"{workspace_slug}/projects/{project_id}/approvals/{approval_id}/votes",
            {"decision": decision, "comment": comment or ""},
        )
