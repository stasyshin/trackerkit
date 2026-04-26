"""Unit tests for `YandexTrackerRelationPolicy` — relation id parsing and lookups."""

from typing import Any

import pytest

from trackerkit.domain.enums import RelationType
from trackerkit.domain.models import CreateRelationInput
from trackerkit.domain.relation_mapping import YandexTrackerRelationMappingConfig
from trackerkit.providers.yandex_tracker.relations import YandexTrackerRelationPolicy


class _Attr:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def policy() -> YandexTrackerRelationPolicy:
    return YandexTrackerRelationPolicy(YandexTrackerRelationMappingConfig())


def test_split_relation_id_with_separator(policy: YandexTrackerRelationPolicy) -> None:
    assert policy.split_relation_id("ABC-1:42") == ("ABC-1", "42")


def test_split_relation_id_returns_none_when_no_separator(
    policy: YandexTrackerRelationPolicy,
) -> None:
    assert policy.split_relation_id("nope") is None


def test_split_relation_id_returns_none_for_empty_parts(
    policy: YandexTrackerRelationPolicy,
) -> None:
    assert policy.split_relation_id(":42") is None
    assert policy.split_relation_id("ABC-1:") is None


def test_get_create_relationship_uses_outward_value(
    policy: YandexTrackerRelationPolicy,
) -> None:
    assert policy.get_create_relationship(RelationType.RELATES) == "relates"
    assert policy.get_create_relationship(RelationType.BLOCKS) == "is dependent by"
    assert policy.get_create_relationship(RelationType.CONTAINS) == "is parent task for"


def test_build_created_relation_uses_combined_id(
    policy: YandexTrackerRelationPolicy,
) -> None:
    payload = CreateRelationInput(
        source_task_id="ABC-1",
        target_task_id="ABC-2",
        relation_type=RelationType.RELATES,
    )
    relation = policy.build_created_relation("99", payload)
    assert relation.id == "ABC-1:99"


def test_list_relations_resolves_outward_blocks_link(
    policy: YandexTrackerRelationPolicy,
) -> None:
    link = _Attr(
        id="L1",
        type=_Attr(id="dependency", outward="is dependent by", inward="depends on"),
        direction="outward",
        object=_Attr(id="ABC-2"),
    )
    issue = _Attr(id="ABC-1")
    relations = policy.list_relations(issue, [link])
    assert len(relations) == 1
    relation = relations[0]
    assert relation.relation_type is RelationType.BLOCKS
    assert relation.source_task_id == "ABC-1"
    assert relation.target_task_id == "ABC-2"
    assert relation.id == "ABC-1:L1"


def test_list_relations_resolves_inward_blocks_link(
    policy: YandexTrackerRelationPolicy,
) -> None:
    link = _Attr(
        id="L1",
        type=_Attr(id="dependency", outward="is dependent by", inward="depends on"),
        direction="inward",
        object=_Attr(id="ABC-3"),
    )
    issue = _Attr(id="ABC-2")
    relations = policy.list_relations(issue, [link])
    assert len(relations) == 1
    assert relations[0].source_task_id == "ABC-3"
    assert relations[0].target_task_id == "ABC-2"
