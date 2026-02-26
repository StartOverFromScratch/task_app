"""create initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. tasks（origin_checklist_item_id の外部キーは後付け）
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("task_type", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=True),
        sa.Column("priority", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="todo"),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("done_criteria", sa.String, nullable=False),
        sa.Column("decision_criteria", sa.String, nullable=True),
        sa.Column("reversible", sa.Boolean, nullable=True),
        sa.Column("exploration_limit", sa.Integer, nullable=True),
        sa.Column("origin_checklist_item_id", sa.Integer, nullable=True),
        sa.Column("last_updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # 2. task_checklist_items
    op.create_table(
        "task_checklist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("text", sa.String, nullable=False),
        sa.Column("is_done", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("order_no", sa.Integer, nullable=False),
        sa.Column("extracted_task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=True),
    )

    # 3. origin_checklist_item_id の外部キーを後付け（循環参照解決）
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.create_foreign_key(
            "fk_tasks_origin_checklist_item_id",
            "task_checklist_items",
            ["origin_checklist_item_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 4. インデックス
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_last_updated_at", "tasks", ["last_updated_at"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_parent_id", "tasks", ["parent_id"])

    # 5. completion_logs
    op.create_table(
        "completion_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("completed_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("note", sa.String, nullable=True),
    )

    # 6. capture_items
    op.create_table(
        "capture_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("related_task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("text", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("capture_items")
    op.drop_table("completion_logs")
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_origin_checklist_item_id")
    op.drop_table("task_checklist_items")
    op.drop_table("tasks")
