import re
from dataclasses import dataclass
from enum import Enum


class ActionClass(str, Enum):
    OBSERVE = "observe"
    DRAFT = "draft"
    MUTATE_BOUNDED = "mutate_bounded"
    MUTATE_CRITICAL = "mutate_critical"


@dataclass(frozen=True)
class QueryPolicyResult:
    allowed: bool
    action_class: ActionClass
    reason: str = ""


WAREHOUSE_SIZE_ORDER = {
    "XSMALL": 0,
    "X-SMALL": 0,
    "SMALL": 1,
    "MEDIUM": 2,
    "LARGE": 3,
    "X-LARGE": 4,
    "XLARGE": 4,
    "2X-LARGE": 5,
    "2XLARGE": 5,
    "3X-LARGE": 6,
    "3XLARGE": 6,
    "4X-LARGE": 7,
    "4XLARGE": 7,
    "5X-LARGE": 8,
    "5XLARGE": 8,
    "6X-LARGE": 9,
    "6XLARGE": 9,
}
MAX_WAREHOUSE_SIZE = "X-LARGE"
OBSERVE_PREFIXES = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")
MUTATION_PREFIXES = (
    "CREATE",
    "ALTER",
    "DROP",
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "COPY",
    "GRANT",
    "REVOKE",
    "TRUNCATE",
)


def _normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip()).upper()


def _extract_warehouse_size(sql_upper: str) -> str | None:
    match = re.search(
        r"\bWAREHOUSE_SIZE\s*=\s*['\"]?([0-9X\-A-Z]+)['\"]?",
        sql_upper,
    )
    if not match:
        return None
    return match.group(1).replace(" ", "")


def _warehouse_size_allowed(size: str) -> bool:
    normalized_size = size.upper().replace(" ", "")
    rank = WAREHOUSE_SIZE_ORDER.get(normalized_size)
    max_rank = WAREHOUSE_SIZE_ORDER[MAX_WAREHOUSE_SIZE]
    return rank is not None and rank <= max_rank


def evaluate_action(action_class: ActionClass) -> bool:
    return action_class is not ActionClass.MUTATE_CRITICAL


def evaluate_query_policy(sql: str) -> QueryPolicyResult:
    sql_upper = _normalize_sql(sql)
    if not sql_upper:
        return QueryPolicyResult(
            allowed=False,
            action_class=ActionClass.DRAFT,
            reason="Empty SQL is not allowed.",
        )

    if re.search(r"\bDROP\s+(DATABASE|ACCOUNT|SHARE)\b", sql_upper):
        match = re.search(r"\bDROP\s+(DATABASE|ACCOUNT|SHARE)\b", sql_upper)
        target = match.group(1) if match else "OBJECT"
        return QueryPolicyResult(
            allowed=False,
            action_class=ActionClass.MUTATE_CRITICAL,
            reason=f"DROP {target} requires manual approval.",
        )

    if re.search(r"\bALTER\s+TABLE\b.*\bDROP\s+COLUMN\b", sql_upper):
        return QueryPolicyResult(
            allowed=False,
            action_class=ActionClass.MUTATE_CRITICAL,
            reason="ALTER TABLE ... DROP COLUMN is blocked by governance policy.",
        )

    if re.search(r"\bREVOKE\s+ALL(?:\s+PRIVILEGES)?\b", sql_upper):
        return QueryPolicyResult(
            allowed=False,
            action_class=ActionClass.MUTATE_CRITICAL,
            reason="REVOKE ALL is blocked by governance policy.",
        )

    if re.search(r"\b(?:CREATE(?:\s+OR\s+REPLACE)?|ALTER)\s+WAREHOUSE\b", sql_upper):
        size = _extract_warehouse_size(sql_upper)
        if size and not _warehouse_size_allowed(size):
            return QueryPolicyResult(
                allowed=False,
                action_class=ActionClass.MUTATE_CRITICAL,
                reason=f"Warehouse sizes above {MAX_WAREHOUSE_SIZE} are blocked ({size}).",
            )

        if re.search(r"\bCREATE(?:\s+OR\s+REPLACE)?\s+WAREHOUSE\b", sql_upper):
            if not re.search(r"\b(?:WITH\s+)?TAG\s*\(", sql_upper):
                return QueryPolicyResult(
                    allowed=False,
                    action_class=ActionClass.MUTATE_BOUNDED,
                    reason="CREATE WAREHOUSE requires a TAG clause for cost governance.",
                )

        return QueryPolicyResult(
            allowed=True,
            action_class=ActionClass.MUTATE_BOUNDED,
        )

    if sql_upper.startswith(OBSERVE_PREFIXES):
        return QueryPolicyResult(allowed=True, action_class=ActionClass.OBSERVE)

    if sql_upper.startswith(MUTATION_PREFIXES):
        action_class = ActionClass.MUTATE_BOUNDED
        return QueryPolicyResult(
            allowed=evaluate_action(action_class),
            action_class=action_class,
        )

    return QueryPolicyResult(allowed=True, action_class=ActionClass.DRAFT)


def check_query_safety(sql: str) -> bool:
    """
    Compatibility wrapper for existing callers that only need a boolean allow/deny.
    """
    return evaluate_query_policy(sql).allowed
