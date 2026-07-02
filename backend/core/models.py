from typing import Any

from pydantic import BaseModel, Field


from enum import Enum

class FeatureType(str, Enum):
    REVENUE = "revenue"
    MARGIN = "margin"
    MARGIN_PCT = "margin_pct"
    RATIO = "ratio"
    DISCOUNT = "discount"
    DERIVED_FEATURE = "derived_feature"
    UNKNOWN = "unknown"


class AcceptedFeature(BaseModel):
    name: str
    type: FeatureType
    source_columns: list[str]
    formula: str | None = None
    status: str | None = "accepted"


class CleaningAction(BaseModel):
    type: str
    column: str | None = None
    params: dict[str, Any] | None = None


class EdaContext(BaseModel):
    target: str | None = None
    problem_type: str | None = None
    semantic_overrides: dict[str, str] = Field(default_factory=dict)
    selected_features: list[str] = Field(default_factory=list)
    accepted_features: list[AcceptedFeature] = Field(default_factory=list)
    cleaning_actions: list[CleaningAction] = Field(default_factory=list)


class AnalysisRequest(EdaContext):
    """Body della richiesta POST /analyze/{file_id}."""
    pass
