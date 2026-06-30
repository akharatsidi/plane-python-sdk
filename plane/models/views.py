from typing import Any

from pydantic import BaseModel, ConfigDict


class View(BaseModel):
    """Saved view (filter) model.

    Mirrors the fork's ``IssueView`` model. ``access`` is an int
    (0=Private, 1=Public). Extra fields (e.g. ``is_favorite``, audit
    columns) are allowed since the public serializer returns ``__all__``.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str | None = None
    name: str | None = None
    description: str | None = None
    query: Any | None = None
    filters: Any | None = None
    rich_filters: Any | None = None
    display_filters: Any | None = None
    display_properties: Any | None = None
    access: int | None = None
    owned_by: str | None = None
    project: str | None = None
    workspace: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None


class CreateView(BaseModel):
    """Request model for creating a view.

    ``query`` is required by the model but defaults to ``{}`` server-side
    when absent; we leave it optional here and let the backend fill it.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    description: str | None = None
    query: Any | None = None
    filters: Any | None = None
    rich_filters: Any | None = None
    display_filters: Any | None = None
    display_properties: Any | None = None
    access: int | None = None


class UpdateView(BaseModel):
    """Request model for updating a view."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    query: Any | None = None
    filters: Any | None = None
    rich_filters: Any | None = None
    display_filters: Any | None = None
    display_properties: Any | None = None
    access: int | None = None
