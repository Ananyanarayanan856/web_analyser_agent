# app/tools/database_tool.py

import json
import re
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from app.database import SessionLocal

# ─────────────────────────────────────────────
# Logger Setup
# ─────────────────────────────────────────────

logger = logging.getLogger("db_tool")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

ALLOWED_OPERATIONS = {"SELECT", "INSERT", "UPDATE", "DELETE"}

ALLOWED_TABLES = [
    "websites",
    "seo_reports",
    "accessibility_reports",
    "content_reports",
    "analysis_summary",
    "db_logs"
]

# Maps report type → correct table name
REPORT_TYPE_TABLE_MAP = {
    "seo"            : "seo_reports",
    "accessibility"  : "accessibility_reports",
    "content"        : "content_reports",
    "summary"        : "analysis_summary",
    "website"        : "websites",
    "log"            : "db_logs",
}

# SQL injection patterns to reject outright
INJECTION_PATTERNS = [
    r";\s*DROP\s+",
    r";\s*TRUNCATE\s+",
    r";\s*ALTER\s+",
    r";\s*CREATE\s+",
    r";\s*GRANT\s+",
    r";\s*REVOKE\s+",
    r"--",                         # line comment
    r"/\*.*?\*/",                  # block comment
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bxp_\w+",                   # MSSQL extended procs
    r"\bUNION\s+ALL\s+SELECT\b",
    r"\bINFORMATION_SCHEMA\b",
    r"\bSYS\.\w+",
    r"\bSLEEP\s*\(",
    r"\bWAITFOR\b",
    r"\bBENCHMARK\s*\(",
    r"0x[0-9a-fA-F]+",             # hex encoding
    r"CHAR\s*\(\s*\d+",            # CHAR() obfuscation
]


# ─────────────────────────────────────────────
# Validation Layer
# ─────────────────────────────────────────────

def _validate(query_data: dict) -> None:
    """
    Full validation pipeline. Raises ValueError with a clear message on failure.
    Checks:
      1. Required fields present
      2. Operation is whitelisted
      3. Table is whitelisted
      4. SQL references only the declared table
      5. SQL injection pattern scan
      6. No stacked statements (multiple ';')
    """

    # ── 1. Required fields ────────────────────
    for field in ("operation", "table", "sql"):
        if field not in query_data:
            raise ValueError(f"Missing required field: '{field}'")

    operation = query_data["operation"].strip().upper()
    table     = query_data["table"].strip().lower()
    sql       = query_data["sql"].strip()

    # ── 2. Whitelisted operation ──────────────
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(
            f"Operation '{operation}' is not allowed. "
            f"Permitted: {', '.join(ALLOWED_OPERATIONS)}"
        )

    # ── 3. Whitelisted table ──────────────────
    if table not in ALLOWED_TABLES:
        raise ValueError(
            f"Table '{table}' is not in the allowed list. "
            f"Permitted tables: {', '.join(ALLOWED_TABLES)}"
        )

    # ── 4. SQL must reference only declared table ─
    #    Extract all table-like tokens after FROM / JOIN / INTO / UPDATE
    sql_upper      = sql.upper()
    referenced     = re.findall(
        r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([`"\[]?(\w+)[`"\]]?)',
        sql_upper
    )
    referenced_tables = {m[1].lower() for m in referenced}

    for ref in referenced_tables:
        if ref not in ALLOWED_TABLES:
            raise ValueError(
                f"SQL references table '{ref}' which is not in the allowed list."
            )

    # ── 5. SQL injection pattern scan ────────
    sql_normalized = re.sub(r'\s+', ' ', sql.upper())
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sql_normalized, re.IGNORECASE):
            raise ValueError(
                f"SQL rejected: potential injection pattern detected → '{pattern}'"
            )

    # ── 6. No stacked statements ─────────────
    #    Strip string literals first to avoid false positives
    stripped = re.sub(r"'[^']*'", "''", sql)
    stripped = re.sub(r'"[^"]*"', '""', stripped)
    if stripped.count(";") > 1:
        raise ValueError(
            "Stacked SQL statements (multiple ';') are not permitted."
        )

    # ── 7. Operation must match SQL verb ──────
    sql_verb = sql_upper.lstrip().split()[0]
    if sql_verb != operation:
        raise ValueError(
            f"Declared operation '{operation}' does not match "
            f"the SQL verb '{sql_verb}'."
        )


# ─────────────────────────────────────────────
# Operation Logger  (writes to db_operation_logs)
# ─────────────────────────────────────────────

def _log_operation(
    db,
    operation   : str,
    table       : str,
    sql         : str,
    status      : str,
    error_msg   : str | None = None
) -> None:
    """
    Persist a record of every DB operation to db_logs.
    Silently swallows failures so a log error never breaks the main query.
    """
    try:
        db.execute(text("""
            INSERT INTO db_logs
                (operation, table_name, query, status, error_message, executed_by, timestamp)
            VALUES
                (:operation, :table_name, :query, :status, :error_msg, :executed_by, :ts)
        """), {
            "operation"  : operation,
            "table_name" : table,
            "query"      : sql[:2000],          # cap at 2000 chars
            "status"     : status,
            "error_msg"  : error_msg,
            "executed_by": "db_executor_node",
            "ts"         : datetime.now(timezone.utc).isoformat()
        })
        db.commit()
    except Exception as log_err:
        logger.warning(f"Failed to write operation log: {log_err}")


# ─────────────────────────────────────────────
# Helper: serialise row dicts
# ─────────────────────────────────────────────

def _serialise_rows(rows) -> list[dict]:
    """Convert SQLAlchemy row objects to JSON-safe dicts."""
    output = []
    for row in rows:
        row_dict = dict(row._mapping)
        for key, val in row_dict.items():
            if hasattr(val, "isoformat"):
                row_dict[key] = val.isoformat()
        output.append(row_dict)
    return output


# ─────────────────────────────────────────────
# Public Interface
# ─────────────────────────────────────────────

def execute_db_query(query: str) -> dict:
    """
    Execute a validated, whitelisted SQL operation.

    Expects a JSON string with the structure:
    {
      "operation" : "SELECT | INSERT | UPDATE | DELETE",
      "table"     : "<one of the ALLOWED_TABLES>",
      "sql"       : "<full SQL statement>",
      "description": "(optional) human-readable intent"
    }

    Returns:
    {
      "type"      : "Database Operation",
      "operation" : ...,
      "table"     : ...,
      "status"    : "success" | "error",
      "result"    : <rows (SELECT) | confirmation string>,
      "row_count" : <int>
    }
    """
    operation   = "UNKNOWN"
    table       = "UNKNOWN"
    sql         = ""
    description = ""

    try:

        # ── Parse input ───────────────────────
        try:
            query_data = json.loads(query) if isinstance(query, str) else query
        except json.JSONDecodeError as je:
            raise ValueError(f"Invalid JSON input: {je}")

        operation   = str(query_data.get("operation", "")).strip().upper()
        table       = str(query_data.get("table",     "")).strip().lower()
        sql         = str(query_data.get("sql",       "")).strip()
        description = str(query_data.get("description", ""))

        # ── Validate ──────────────────────────
        _validate(query_data)

        logger.info(
            f"DB query validated | op={operation} table={table} | {description or sql[:60]}"
        )

        # ── Execute ───────────────────────────
        with SessionLocal() as db:
            try:
                result    = db.execute(text(sql))
                db.commit()

                if operation == "SELECT":
                    rows      = result.fetchall()
                    output    = _serialise_rows(rows)
                    row_count = len(output)

                    _log_operation(db, operation, table, sql, "success")
                    logger.info(f"SELECT returned {row_count} row(s) from '{table}'")

                    return {
                        "type"      : "Database Operation",
                        "operation" : operation,
                        "table"     : table,
                        "status"    : "success",
                        "result"    : output,
                        "row_count" : row_count
                    }

                else:
                    row_count = result.rowcount if result.rowcount != -1 else 0
                    msg       = (
                        f"{operation} on '{table}' executed successfully "
                        f"({row_count} row(s) affected)."
                    )

                    _log_operation(db, operation, table, sql, "success")
                    logger.info(msg)

                    return {
                        "type"      : "Database Operation",
                        "operation" : operation,
                        "table"     : table,
                        "status"    : "success",
                        "result"    : msg,
                        "row_count" : row_count
                    }

            except Exception as db_err:
                # Rollback on any DB-level failure
                db.rollback()
                _log_operation(db, operation, table, sql, "error", str(db_err))
                logger.error(f"DB execution error | op={operation} table={table} | {db_err}")
                raise

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"execute_db_query FAILED | op={operation} table={table} | {error_msg}"
        )
        return {
            "type"      : "Database Operation",
            "operation" : operation,
            "table"     : table,
            "status"    : "error",
            "error"     : error_msg
        }


# ─────────────────────────────────────────────
# Convenience Wrappers  (used by the LLM agent
# when it knows the intent but not exact SQL)
# ─────────────────────────────────────────────

def store_report(report_type: str, url: str, data: dict) -> dict:
    """
    Store an analysis report in the correct table.

    report_type : "seo" | "accessibility" | "content" | "summary"
    url         : the analysed page URL
    data        : dict of columns → values
    """
    table = REPORT_TYPE_TABLE_MAP.get(report_type.lower())
    if not table:
        return {
            "status": "error",
            "error" : f"Unknown report type '{report_type}'. "
                      f"Use one of: {', '.join(REPORT_TYPE_TABLE_MAP)}"
        }

    # Build parameterised INSERT  (values are passed via :key placeholders)
    data["url"]        = url
    data["created_at"] = datetime.now(timezone.utc).isoformat()

    columns      = ", ".join(data.keys())
    placeholders = ", ".join(f":{k}" for k in data.keys())
    sql          = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    return execute_db_query(json.dumps({
        "operation"  : "INSERT",
        "table"      : table,
        "sql"        : sql,
        "description": f"Store {report_type} report for {url}"
    }))


def fetch_reports(report_type: str, filters: dict | None = None) -> dict:
    """
    Fetch reports from the correct table with optional WHERE filters.

    report_type : "seo" | "accessibility" | "content" | "summary"
    filters     : e.g. {"url": "example.com"} or {"score_lt": 50}
    """
    table = REPORT_TYPE_TABLE_MAP.get(report_type.lower())
    if not table:
        return {
            "status": "error",
            "error" : f"Unknown report type '{report_type}'."
        }

    sql = f"SELECT * FROM {table}"

    where_clauses = []
    if filters:
        for key, val in filters.items():
            if key.endswith("_lt"):
                col = key[:-3]
                where_clauses.append(f"{col} < {int(val)}")
            elif key.endswith("_gt"):
                col = key[:-3]
                where_clauses.append(f"{col} > {int(val)}")
            else:
                # String-safe quoting for simple equality
                safe_val = str(val).replace("'", "''")
                where_clauses.append(f"{key} = '{safe_val}'")

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY created_at DESC"

    return execute_db_query(json.dumps({
        "operation"  : "SELECT",
        "table"      : table,
        "sql"        : sql,
        "description": f"Fetch {report_type} reports with filters={filters}"
    }))


def delete_old_reports(report_type: str, days: int = 30) -> dict:
    """
    Delete reports older than `days` days from the correct table.
    """
    table = REPORT_TYPE_TABLE_MAP.get(report_type.lower())
    if not table:
        return {
            "status": "error",
            "error" : f"Unknown report type '{report_type}'."
        }

    sql = (
        f"DELETE FROM {table} "
        f"WHERE created_at < NOW() - INTERVAL '{days} days'"
    )

    return execute_db_query(json.dumps({
        "operation"  : "DELETE",
        "table"      : table,
        "sql"        : sql,
        "description": f"Delete {report_type} reports older than {days} days"
    }))


def update_report_score(report_type: str, url: str, score: int | float) -> dict:
    """
    Update the score for a specific URL in the correct table.
    """
    table = REPORT_TYPE_TABLE_MAP.get(report_type.lower())
    if not table:
        return {
            "status": "error",
            "error" : f"Unknown report type '{report_type}'."
        }

    safe_url = str(url).replace("'", "''")
    sql      = (
        f"UPDATE {table} "
        f"SET score = {float(score)}, updated_at = NOW() "
        f"WHERE url = '{safe_url}'"
    )

    return execute_db_query(json.dumps({
        "operation"  : "UPDATE",
        "table"      : table,
        "sql"        : sql,
        "description": f"Update {report_type} score for {url} → {score}"
    }))