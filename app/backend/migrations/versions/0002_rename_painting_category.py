"""rename task category 'painting' to 'general'

Revision ID: 0002_rename_painting_category
Revises: 0001_initial_schema
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_rename_painting_category"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename(old: str, new: str) -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(f"ALTER TYPE task_category RENAME VALUE '{old}' TO '{new}'")
    else:
        # Non-native enums (SQLite in tests) are plain strings: rewrite the rows.
        op.execute(f"UPDATE tasks SET category = '{new}' WHERE category = '{old}'")


def upgrade() -> None:
    _rename("painting", "general")


def downgrade() -> None:
    _rename("general", "painting")
