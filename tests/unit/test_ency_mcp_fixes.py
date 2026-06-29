"""Offline regression tests for ENCY MCP-driven SDK fixes (gaps 1.3, 1.4, 1.5).

The Plane MCP server drives this SDK against the ENCY CE backend
(`tasks.encysoftware.com`). These tests pin the response shapes that backend
actually returns and that SDK 0.2.16 mis-modelled:

- gap 1.4: relation buckets come back as objects ``{project_id, issue_id}``,
  not bare ID strings.
- gap 1.5: a work item's ``assignees``/``labels`` come back as UUID strings
  unless explicitly expanded.
- gap 1.3: list endpoints return a paginated envelope ``{"results": [...]}``
  (fork "rule D"), and an unset property value's read-time fallback row has
  ``id == None``.

All tests are offline: model validation is pure, and resource methods are
exercised by stubbing the HTTP layer (``_get``) — no network, so they run in
the default suite instead of skipping like the live integration tests.
"""

from plane.client import PlaneClient
from plane.models.views import CreateView, UpdateView, View
from plane.models.work_item_properties import WorkItemPropertyValueDetail
from plane.models.work_items import WorkItemDetail, WorkItemRelationResponse


def _client() -> PlaneClient:
    return PlaneClient(base_url="https://example.test", api_key="k")


# --- gap 1.4: relations are objects, not bare strings -----------------------


def test_relation_response_accepts_object_buckets():
    resp = WorkItemRelationResponse.model_validate(
        {"blocking": [{"project_id": "p1", "issue_id": "i1"}], "blocked_by": []}
    )
    assert resp.blocking[0].issue_id == "i1"
    assert resp.blocking[0].project_id == "p1"


def test_relation_response_missing_buckets_default_empty():
    resp = WorkItemRelationResponse.model_validate({})
    assert resp.relates_to == []
    assert resp.duplicate == []


# --- gap 1.5: assignees/labels return as UUID strings unless expanded -------


def test_work_item_detail_accepts_uuid_string_assignees_and_labels():
    wi = WorkItemDetail.model_validate(
        {"id": "wi1", "assignees": ["u-uuid"], "labels": ["l-uuid"]}
    )
    assert wi.assignees == ["u-uuid"]
    assert wi.labels == ["l-uuid"]


def test_work_item_detail_still_accepts_expanded_objects():
    wi = WorkItemDetail.model_validate(
        {"id": "wi1", "assignees": [{"id": "u1"}], "labels": [{"id": "l1", "name": "bug"}]}
    )
    assert wi.assignees[0].id == "u1"
    assert wi.labels[0].name == "bug"


# --- gap 1.3: value-detail id may be absent (default-value fallback row) -----


def test_property_value_detail_allows_missing_id():
    v = WorkItemPropertyValueDetail.model_validate(
        {"property_id": "p1", "issue_id": "i1", "value": "x"}
    )
    assert v.id is None


# --- gap 1.3: list endpoints return a paginated envelope --------------------


def test_list_properties_unwraps_paginated_envelope(monkeypatch):
    res = _client().work_item_properties
    envelope = {
        "grouped_by": None,
        "total_count": 1,
        "results": [{"display_name": "ICE", "property_type": "DECIMAL"}],
    }
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.list("ws", "proj", "type")
    assert len(out) == 1
    assert out[0].display_name == "ICE"


def test_list_properties_still_accepts_bare_list(monkeypatch):
    res = _client().work_item_properties
    monkeypatch.setattr(
        res, "_get", lambda *a, **k: [{"display_name": "ICE", "property_type": "DECIMAL"}]
    )
    out = res.list("ws", "proj", "type")
    assert len(out) == 1


def test_list_property_options_unwraps_envelope(monkeypatch):
    res = _client().work_item_properties.options
    envelope = {"results": [{"name": "low"}, {"name": "high"}], "total_count": 2}
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.list("ws", "proj", "prop")
    assert [o.name for o in out] == ["low", "high"]


def test_list_worklogs_unwraps_envelope(monkeypatch):
    res = _client().work_items.work_logs
    envelope = {"results": [{"id": "wl1", "description": "x"}], "total_count": 1}
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.list("ws", "proj", "wi")
    assert len(out) == 1
    assert out[0].id == "wl1"


def test_property_values_unwrap_envelope_to_list(monkeypatch):
    res = _client().work_item_properties.values
    envelope = {"results": [{"id": "v1", "property_id": "p1", "issue_id": "i1", "value": "x"}]}
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.retrieve("ws", "proj", "wi", "p1")
    assert isinstance(out, list)
    assert out[0].id == "v1"


def test_list_work_item_types_unwraps_envelope(monkeypatch):
    # The fork's public work-item-types list is enveloped (rule D); resolve_work_item_type
    # iterates it, so the SDK must unwrap before validating.
    res = _client().work_item_types
    envelope = {"results": [{"name": "Epic"}, {"name": "Task"}], "total_count": 2}
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.list("ws", "proj")
    assert [t.name for t in out] == ["Epic", "Task"]


def test_list_workspace_work_item_types_unwraps_envelope(monkeypatch):
    res = _client().workspace_work_item_types
    envelope = {"results": [{"name": "Epic"}], "total_count": 1}
    monkeypatch.setattr(res, "_get", lambda *a, **k: envelope)
    out = res.list("ws")
    assert out[0].name == "Epic"


def test_property_values_single_object_still_returns_single(monkeypatch):
    res = _client().work_item_properties.values
    monkeypatch.setattr(
        res,
        "_get",
        lambda *a, **k: {"id": "v1", "property_id": "p1", "issue_id": "i1", "value": "x"},
    )
    out = res.retrieve("ws", "proj", "wi", "p1")
    assert isinstance(out, WorkItemPropertyValueDetail)
    assert out.value == "x"


# --- workspace invitations (create / list / delete) -------------------------
#
# Role values are ints throughout: ADMIN=20, MEMBER=15, GUEST=5.
# BaseResource._build_url appends a trailing slash, so methods pass paths
# WITHOUT a trailing slash; here we assert the path-shape the method builds
# (the first positional arg to the stubbed HTTP method).


def test_create_invite_posts_email_and_role(monkeypatch):
    res = _client().workspaces
    captured = {}

    def _post(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "inv1", "email": "a@b.test", "role": 15}

    monkeypatch.setattr(res, "_post", _post)
    out = res.create_invite("ws", "a@b.test", 15)
    assert captured["endpoint"] == "ws/invitations"
    assert captured["data"] == {"email": "a@b.test", "role": 15}
    assert out == {"id": "inv1", "email": "a@b.test", "role": 15}


def test_list_invites_unwraps_envelope(monkeypatch):
    res = _client().workspaces
    captured = {}

    def _get(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return {"results": [{"id": "inv1"}, {"id": "inv2"}], "total_count": 2}

    monkeypatch.setattr(res, "_get", _get)
    out = res.list_invites("ws")
    assert captured["endpoint"] == "ws/invitations"
    assert [i["id"] for i in out] == ["inv1", "inv2"]


def test_list_invites_accepts_bare_list(monkeypatch):
    res = _client().workspaces
    monkeypatch.setattr(res, "_get", lambda *a, **k: [{"id": "inv1"}])
    out = res.list_invites("ws")
    assert out == [{"id": "inv1"}]


def test_delete_invite_hits_invitation_path(monkeypatch):
    res = _client().workspaces
    captured = {}

    def _delete(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return None

    monkeypatch.setattr(res, "_delete", _delete)
    assert res.delete_invite("ws", "inv1") is None
    assert captured["endpoint"] == "ws/invitations/inv1"


# --- project members (add / update / remove) --------------------------------


def test_add_member_posts_member_and_role(monkeypatch):
    res = _client().projects
    captured = {}

    def _post(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "pm1", "member": "u1", "role": 20}

    monkeypatch.setattr(res, "_post", _post)
    out = res.add_member("ws", "proj", "u1", 20)
    assert captured["endpoint"] == "ws/projects/proj/members"
    assert captured["data"] == {"member": "u1", "role": 20}
    assert out == {"id": "pm1", "member": "u1", "role": 20}


def test_update_member_patches_role(monkeypatch):
    res = _client().projects
    captured = {}

    def _patch(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "pm1", "role": 5}

    monkeypatch.setattr(res, "_patch", _patch)
    out = res.update_member("ws", "proj", "pm1", 5)
    assert captured["endpoint"] == "ws/projects/proj/members/pm1"
    assert captured["data"] == {"role": 5}
    assert out == {"id": "pm1", "role": 5}


def test_remove_member_hits_member_pk_path(monkeypatch):
    res = _client().projects
    captured = {}

    def _delete(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return None

    monkeypatch.setattr(res, "_delete", _delete)
    assert res.remove_member("ws", "proj", "pm1") is None
    assert captured["endpoint"] == "ws/projects/proj/members/pm1"


# --- views (gap 1.11): saved filters, project vs workspace path-shape -------
#
# A single Views resource serves both project views and workspace views: when
# project_id is None the workspace path is used, otherwise the project path.
# Lists are enveloped (rule D) and unwrapped via _as_items. Paths carry NO
# trailing slash (BaseResource._build_url appends it).


def test_list_project_views_uses_project_path_and_unwraps_envelope(monkeypatch):
    res = _client().views
    captured = {}

    def _get(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return {"results": [{"id": "v1", "name": "Bugs"}], "total_count": 1}

    monkeypatch.setattr(res, "_get", _get)
    out = res.list("ws", "proj")
    assert captured["endpoint"] == "ws/projects/proj/views"
    assert isinstance(out, list)
    assert [v.id for v in out] == ["v1"]
    assert out[0].name == "Bugs"


def test_list_workspace_views_uses_workspace_path_when_project_none(monkeypatch):
    res = _client().views
    captured = {}

    def _get(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return {"results": [{"id": "wv1", "name": "My Work"}]}

    monkeypatch.setattr(res, "_get", _get)
    out = res.list("ws")
    assert captured["endpoint"] == "ws/views"
    assert [v.name for v in out] == ["My Work"]


def test_list_views_accepts_bare_list(monkeypatch):
    res = _client().views
    monkeypatch.setattr(res, "_get", lambda *a, **k: [{"id": "v1", "name": "X"}])
    out = res.list("ws", "proj")
    assert [v.id for v in out] == ["v1"]


def test_create_project_view_posts_to_project_path(monkeypatch):
    res = _client().views
    captured = {}

    def _post(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "v1", "name": "Bugs", "access": 1}

    monkeypatch.setattr(res, "_post", _post)
    out = res.create("ws", CreateView(name="Bugs", access=1), project_id="proj")
    assert captured["endpoint"] == "ws/projects/proj/views"
    # exclude_none drops unset optionals (description/query/filters/...)
    assert captured["data"] == {"name": "Bugs", "access": 1}
    assert isinstance(out, View)
    assert out.id == "v1"


def test_create_workspace_view_posts_to_workspace_path(monkeypatch):
    res = _client().views
    captured = {}

    def _post(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "wv1", "name": "Mine"}

    monkeypatch.setattr(res, "_post", _post)
    out = res.create("ws", CreateView(name="Mine"))
    assert captured["endpoint"] == "ws/views"
    assert captured["data"] == {"name": "Mine"}
    assert out.id == "wv1"


def test_retrieve_view_project_vs_workspace_path(monkeypatch):
    res = _client().views
    captured = {}

    def _get(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return {"id": "v1", "name": "Bugs"}

    monkeypatch.setattr(res, "_get", _get)

    assert res.retrieve("ws", "v1", project_id="proj").id == "v1"
    assert captured["endpoint"] == "ws/projects/proj/views/v1"

    assert res.retrieve("ws", "v1").id == "v1"
    assert captured["endpoint"] == "ws/views/v1"


def test_update_view_patches_correct_path_and_drops_none(monkeypatch):
    res = _client().views
    captured = {}

    def _patch(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "v1", "name": "Renamed"}

    monkeypatch.setattr(res, "_patch", _patch)
    out = res.update("ws", "v1", UpdateView(name="Renamed"), project_id="proj")
    assert captured["endpoint"] == "ws/projects/proj/views/v1"
    assert captured["data"] == {"name": "Renamed"}
    assert out.name == "Renamed"

    res.update("ws", "v1", UpdateView(name="Renamed"))
    assert captured["endpoint"] == "ws/views/v1"


def test_delete_view_project_vs_workspace_path(monkeypatch):
    res = _client().views
    captured = {}

    def _delete(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return None

    monkeypatch.setattr(res, "_delete", _delete)

    assert res.delete("ws", "v1", project_id="proj") is None
    assert captured["endpoint"] == "ws/projects/proj/views/v1"

    assert res.delete("ws", "v1") is None
    assert captured["endpoint"] == "ws/views/v1"


# --- Sprint 2: property explicit name + page update/archive -----------------


def test_create_work_item_property_carries_explicit_name():
    from plane.models.work_item_properties import CreateWorkItemProperty

    body = CreateWorkItemProperty(
        name="expected_rev_usd", display_name="Expected Revenue (USD)", property_type="DECIMAL"
    ).model_dump(exclude_none=True)
    assert body["name"] == "expected_rev_usd"
    assert body["display_name"] == "Expected Revenue (USD)"


def test_update_project_page_patches_path_and_body(monkeypatch):
    res = _client().pages
    captured = {}

    def _patch(endpoint, data=None, *a, **k):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"id": "pg1", "name": "Renamed"}

    monkeypatch.setattr(res, "_patch", _patch)
    out = res.update_project_page("ws", "proj", "pg1", {"name": "Renamed"})
    assert captured["endpoint"] == "ws/projects/proj/pages/pg1"
    assert captured["data"] == {"name": "Renamed"}
    assert out.name == "Renamed"


def test_archive_unarchive_project_page_paths(monkeypatch):
    res = _client().pages
    captured = {}

    def _post(endpoint, *a, **k):
        captured["endpoint"] = endpoint
        return {"archived_at": "2026-07-01"}

    monkeypatch.setattr(res, "_post", _post)
    res.archive_project_page("ws", "proj", "pg1")
    assert captured["endpoint"] == "ws/projects/proj/pages/pg1/archive"
    res.unarchive_project_page("ws", "proj", "pg1")
    assert captured["endpoint"] == "ws/projects/proj/pages/pg1/unarchive"
