"""Unit tests for `JiraRelationPolicy` — relation parsing/building."""

from typing import Any

import pytest

from trackerkit.domain.enums import RelationType
from trackerkit.domain.models import CreateRelationInput
from trackerkit.domain.relation_mapping import (
    JiraContainsMode,
    JiraLinkTypeMapping,
    JiraRelationMappingConfig,
)
from trackerkit.providers.jira.relations import JiraRelationPolicy


class _Attr:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def default_policy() -> JiraRelationPolicy:
    return JiraRelationPolicy(JiraRelationMappingConfig())


def _link_type(name: str, outward: str | None = None, inward: str | None = None) -> _Attr:
    return _Attr(name=name, outward=outward, inward=inward)


def test_matches_mapping_with_name_only_when_labels_unspecified() -> None:
    config = JiraRelationMappingConfig(
        link_mappings=(
            JiraLinkTypeMapping(
                relation_type=RelationType.RELATES,
                type_name="Relates",
            ),
        )
    )
    policy = JiraRelationPolicy(config)
    assert policy._matches_mapping(_link_type("Relates"), config.link_mappings[0])
    assert not policy._matches_mapping(_link_type("Other"), config.link_mappings[0])


def test_matches_mapping_requires_both_labels_when_specified(
    default_policy: JiraRelationPolicy,
) -> None:
    blocks = next(
        m for m in default_policy._config.link_mappings if m.relation_type is RelationType.BLOCKS
    )
    assert default_policy._matches_mapping(
        _link_type("Blocks", outward="blocks", inward="is blocked by"),
        blocks,
    )
    assert not default_policy._matches_mapping(
        _link_type("Blocks", outward="other", inward="is blocked by"),
        blocks,
    )


def test_round_trip_structural_relation_id(default_policy: JiraRelationPolicy) -> None:
    rid = default_policy.build_structural_relation_id("100", "200")
    assert rid == "jira-contains:100:200"
    parsed = default_policy.parse_structural_relation_id(rid)
    assert parsed == ("100", "200")


def test_parse_structural_relation_id_rejects_unknown_prefix(
    default_policy: JiraRelationPolicy,
) -> None:
    assert default_policy.parse_structural_relation_id("9999") is None
    assert default_policy.parse_structural_relation_id("other:1:2") is None


def test_uses_structural_contains_for_default_config(
    default_policy: JiraRelationPolicy,
) -> None:
    assert default_policy.uses_structural_contains() is True
    assert default_policy.uses_custom_contains_links() is False


def test_uses_custom_contains_links_when_mode_is_custom() -> None:
    config = JiraRelationMappingConfig(
        contains_mode=JiraContainsMode.CUSTOM_LINK_MAPPING,
        contains_link_mappings=(
            JiraLinkTypeMapping(
                relation_type=RelationType.CONTAINS,
                type_name="Contains",
            ),
        ),
    )
    policy = JiraRelationPolicy(config)
    assert policy.uses_custom_contains_links() is True
    assert policy.uses_structural_contains() is False


def test_build_created_relation_uses_structural_id_for_contains(
    default_policy: JiraRelationPolicy,
) -> None:
    payload = CreateRelationInput(
        source_task_id="A",
        target_task_id="B",
        relation_type=RelationType.CONTAINS,
    )
    relation = default_policy.build_created_relation(None, payload)
    assert relation.id == "jira-contains:A:B"


def test_list_relations_deduplicates_when_same_link_seen_twice(
    default_policy: JiraRelationPolicy,
) -> None:
    inward_link = _Attr(
        id="L1",
        type=_link_type("Blocks", outward="blocks", inward="is blocked by"),
        inwardIssue=_Attr(id="100"),
        outwardIssue=None,
    )
    issue = _Attr(
        id="200",
        fields=_Attr(issuelinks=[inward_link, inward_link], parent=None, subtasks=[]),
    )
    relations = default_policy.list_relations(issue)
    assert len(relations) == 1
    assert relations[0].source_task_id == "100"
    assert relations[0].target_task_id == "200"
    assert relations[0].relation_type is RelationType.BLOCKS
