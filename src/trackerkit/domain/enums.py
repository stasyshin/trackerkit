from enum import Enum


class Provider(str, Enum):
    JIRA = "jira"
    YANDEX_TRACKER = "yandex_tracker"
    ASANA = "asana"


class RelationType(str, Enum):
    RELATES = "relates"
    BLOCKS = "blocks"
    CONTAINS = "contains"

