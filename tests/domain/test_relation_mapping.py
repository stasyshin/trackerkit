"""Unit tests for `JiraRelationMappingConfig.from_env` and `RelationMappingConfig.from_env`."""

import pytest

from trackerkit.domain.enums import RelationType
from trackerkit.domain.errors import ConfigurationError
from trackerkit.domain.relation_mapping import (
    JiraContainsMode,
    JiraRelationMappingConfig,
    RelationMappingConfig,
)


def test_from_env_with_empty_environment_returns_defaults() -> None:
    config = JiraRelationMappingConfig.from_env(environ={})
    assert config.contains_mode is JiraContainsMode.STRUCTURAL_HIERARCHY
    relates = [m for m in config.link_mappings if m.relation_type is RelationType.RELATES]
    assert len(relates) == 1


def test_from_env_overrides_blocks_link_types() -> None:
    config = JiraRelationMappingConfig.from_env(
        environ={"JIRA_BLOCKS_LINK_TYPES": "Blocks|blocks|is blocked by"}
    )
    blocks = [m for m in config.link_mappings if m.relation_type is RelationType.BLOCKS]
    assert len(blocks) == 1
    assert blocks[0].type_name == "Blocks"
    assert blocks[0].outward_label == "blocks"
    assert blocks[0].inward_label == "is blocked by"


def test_from_env_supports_multiple_link_entries_per_relation() -> None:
    config = JiraRelationMappingConfig.from_env(
        environ={"JIRA_RELATES_LINK_TYPES": "Relates;Linked"}
    )
    relates = [m for m in config.link_mappings if m.relation_type is RelationType.RELATES]
    assert {m.type_name for m in relates} == {"Relates", "Linked"}


def test_from_env_rejects_malformed_link_entry() -> None:
    with pytest.raises(ConfigurationError):
        JiraRelationMappingConfig.from_env(
            environ={"JIRA_BLOCKS_LINK_TYPES": "Blocks|onlyOne"}
        )


def test_from_env_implies_custom_mode_when_contains_mappings_set() -> None:
    config = JiraRelationMappingConfig.from_env(
        environ={"JIRA_CONTAINS_LINK_TYPES": "Contains|contains|is contained by"}
    )
    assert config.contains_mode is JiraContainsMode.CUSTOM_LINK_MAPPING


def test_from_env_keeps_explicit_contains_mode() -> None:
    config = JiraRelationMappingConfig.from_env(
        environ={
            "JIRA_CONTAINS_LINK_TYPES": "Contains|contains|is contained by",
            "JIRA_CONTAINS_MODE": "hybrid",
        }
    )
    assert config.contains_mode is JiraContainsMode.HYBRID


def test_from_env_rejects_unknown_contains_mode() -> None:
    with pytest.raises(ConfigurationError):
        JiraRelationMappingConfig.from_env(environ={"JIRA_CONTAINS_MODE": "bogus"})


def test_relation_mapping_config_from_env_passes_through_jira_config() -> None:
    cfg = RelationMappingConfig.from_env(
        environ={"JIRA_BLOCKS_LINK_TYPES": "Blocks|blocks|is blocked by"}
    )
    blocks = [m for m in cfg.jira.link_mappings if m.relation_type is RelationType.BLOCKS]
    assert len(blocks) == 1
    assert blocks[0].type_name == "Blocks"
