from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from depensee_tracker_client.domain.enums import RelationType


class JiraContainsMode(str, Enum):
    STRUCTURAL_HIERARCHY = "structural_hierarchy"
    CUSTOM_LINK_MAPPING = "custom_link_mapping"
    HYBRID = "hybrid"


class JiraLinkTypeMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    relation_type: RelationType
    type_name: str
    outward_label: str
    inward_label: str


class JiraRelationMappingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    link_mappings: tuple[JiraLinkTypeMapping, ...] = Field(
        default_factory=lambda: (
            JiraLinkTypeMapping(
                relation_type=RelationType.RELATES,
                type_name="Relates",
                outward_label="relates to",
                inward_label="relates to",
            ),
            JiraLinkTypeMapping(
                relation_type=RelationType.BLOCKS,
                type_name="Blocks",
                outward_label="blocks",
                inward_label="is blocked by",
            ),
        )
    )
    contains_mode: JiraContainsMode = JiraContainsMode.STRUCTURAL_HIERARCHY
    contains_link_mappings: tuple[JiraLinkTypeMapping, ...] = ()


class YandexTrackerRelationMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    relation_type: RelationType
    outward_value: str
    inward_value: str


class YandexTrackerRelationMappingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    mappings: tuple[YandexTrackerRelationMapping, ...] = Field(
        default_factory=lambda: (
            YandexTrackerRelationMapping(
                relation_type=RelationType.RELATES,
                outward_value="relates",
                inward_value="relates",
            ),
            YandexTrackerRelationMapping(
                relation_type=RelationType.BLOCKS,
                outward_value="is dependent by",
                inward_value="depends on",
            ),
            YandexTrackerRelationMapping(
                relation_type=RelationType.CONTAINS,
                outward_value="is parent task for",
                inward_value="is subtask for",
            ),
        )
    )


class RelationMappingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    jira: JiraRelationMappingConfig = Field(default_factory=JiraRelationMappingConfig)
    yandex_tracker: YandexTrackerRelationMappingConfig = Field(
        default_factory=YandexTrackerRelationMappingConfig
    )
