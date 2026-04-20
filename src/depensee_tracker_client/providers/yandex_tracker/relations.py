from typing import Any

from depensee_tracker_client.domain.models import CreateRelationInput, Relation
from depensee_tracker_client.domain.relation_mapping import (
    YandexTrackerRelationMapping,
    YandexTrackerRelationMappingConfig,
)


class YandexTrackerRelationPolicy:
    def __init__(self, config: YandexTrackerRelationMappingConfig) -> None:
        self._config = config

    def list_relations(self, issue: Any, links: list[Any]) -> list[Relation]:
        relations: list[Relation] = []
        current_issue_id = str(issue.id)
        for link in links:
            relation = self._to_relation_from_issue_context(current_issue_id, link)
            if relation is not None:
                relations.append(relation)
        return relations

    def get_create_relationship(self, relation_type) -> str | None:
        mapping = self._find_mapping_by_relation_type(relation_type)
        if mapping is None:
            return None
        return mapping.outward_value

    def build_created_relation(
        self,
        relation_id: str | None,
        payload: CreateRelationInput,
    ) -> Relation:
        return Relation(
            id=relation_id,
            source_task_id=payload.source_task_id,
            target_task_id=payload.target_task_id,
            relation_type=payload.relation_type,
        )

    def _to_relation_from_issue_context(
        self,
        current_issue_id: str,
        link: Any,
    ) -> Relation | None:
        link_type = getattr(link, "type", None)
        direction = getattr(link, "direction", None)
        if link_type is None or direction not in {"inward", "outward"}:
            return None

        current_label = (
            getattr(link_type, "outward", None)
            if direction == "outward"
            else getattr(link_type, "inward", None)
        )
        mapping = self._find_mapping_by_label(current_label)
        if mapping is None:
            return None

        linked_object = getattr(link, "object", None)
        linked_issue_id = getattr(linked_object, "id", None)
        if linked_issue_id is None:
            return None

        if current_label == mapping.outward_value:
            source_task_id = current_issue_id
            target_task_id = str(linked_issue_id)
        else:
            source_task_id = str(linked_issue_id)
            target_task_id = current_issue_id

        return Relation(
            id=str(getattr(link, "id", "")) or None,
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            relation_type=mapping.relation_type,
        )

    def _find_mapping_by_label(
        self,
        label: str | None,
    ) -> YandexTrackerRelationMapping | None:
        if label is None:
            return None
        for mapping in self._config.mappings:
            if label in {mapping.outward_value, mapping.inward_value}:
                return mapping
        return None

    def _find_mapping_by_relation_type(
        self,
        relation_type,
    ) -> YandexTrackerRelationMapping | None:
        for mapping in self._config.mappings:
            if mapping.relation_type is relation_type:
                return mapping
        return None
