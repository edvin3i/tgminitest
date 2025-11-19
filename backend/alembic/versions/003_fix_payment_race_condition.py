"""Fix payment race condition with partial unique index

Revision ID: 003_fix_payment_race_condition
Revises: 002_payment_updates
Create Date: 2025-11-19

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_fix_payment_race_condition"
down_revision: str | None = "002_payment_updates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply migration changes."""
    # Add partial unique index to prevent duplicate active payments for same result
    # This prevents race condition where multiple payments could be created for same result_id
    op.execute(
        """
        CREATE UNIQUE INDEX ix_payments_result_id_unique_active
        ON payments (result_id)
        WHERE status IN ('pending', 'paid');
        """
    )


def downgrade() -> None:
    """Revert migration changes."""
    op.execute("DROP INDEX IF EXISTS ix_payments_result_id_unique_active;")
