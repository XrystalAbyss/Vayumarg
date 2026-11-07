"""Minimal database audit script for Vayumarg F0."""

import json
import os

os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from vayumarg.database.engine import audit_database_integrity, get_default_engine


def main() -> None:
    engine = get_default_engine()
    audit_data = audit_database_integrity(engine)
    print(json.dumps(audit_data, indent=2))


if __name__ == "__main__":
    main()
