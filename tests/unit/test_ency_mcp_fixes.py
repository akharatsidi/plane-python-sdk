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
