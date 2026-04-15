from enum import Enum


class Provider(str, Enum):
    JIRA = "jira"
    YANDEX_TRACKER = "yandex_tracker"
    ASANA = "asana"


class RelationType(str, Enum):
    RELATES = "relates"
    BLOCKS = "blocks"
    IS_BLOCKED_BY = "is_blocked_by"
    DUPLICATES = "duplicates"
    IS_DUPLICATED_BY = "is_duplicated_by"

