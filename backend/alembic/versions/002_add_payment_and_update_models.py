"""Add Payment model and update MintTransaction and NFTMetadata

Revision ID: 002_payment_updates
Revises: 001_initial
Create Date: 2025-11-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_payment_updates"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column(
            "telegram_payment_charge_id", sa.String(length=255), nullable=True
        ),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["result_id"],
            ["quiz_results.id"],
            name=op.f("fk_payments_result_id_quiz_results"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_payments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
    )
    op.create_index(
        op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_payments_result_id"), "payments", ["result_id"], unique=False
    )

    # Update mint_transactions table
    op.add_column(
        "mint_transactions",
        sa.Column("payment_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "mint_transactions",
        sa.Column("ipfs_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "mint_transactions",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_mint_transactions_payment_id_payments"),
        "mint_transactions",
        "payments",
        ["payment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_mint_transactions_payment_id"),
        "mint_transactions",
        ["payment_id"],
        unique=False,
    )

    # Update nft_metadata table - restructure from quiz-based to result-based
    # First, drop existing foreign key and indexes
    op.drop_index(op.f("ix_nft_metadata_quiz_id"), table_name="nft_metadata")
    op.drop_constraint(
        op.f("fk_nft_metadata_quiz_id_quizzes"),
        "nft_metadata",
        type_="foreignkey",
    )

    # Drop old columns
    op.drop_column("nft_metadata", "quiz_id")
    op.drop_column("nft_metadata", "result_type")

    # Add new columns
    op.add_column(
        "nft_metadata",
        sa.Column("result_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "nft_metadata",
        sa.Column("metadata_url", sa.String(length=512), nullable=False),
    )

    # Rename attributes_json to attributes
    op.alter_column(
        "nft_metadata",
        "attributes_json",
        new_column_name="attributes",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )

    # Create new foreign key and indexes
    op.create_foreign_key(
        op.f("fk_nft_metadata_result_id_quiz_results"),
        "nft_metadata",
        "quiz_results",
        ["result_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_nft_metadata_result_id"),
        "nft_metadata",
        ["result_id"],
        unique=True,
    )


def downgrade() -> None:
    """Revert migration changes."""
    # Revert nft_metadata changes
    op.drop_index(op.f("ix_nft_metadata_result_id"), table_name="nft_metadata")
    op.drop_constraint(
        op.f("fk_nft_metadata_result_id_quiz_results"),
        "nft_metadata",
        type_="foreignkey",
    )

    # Rename attributes back to attributes_json
    op.alter_column(
        "nft_metadata",
        "attributes",
        new_column_name="attributes_json",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )

    # Remove new columns
    op.drop_column("nft_metadata", "metadata_url")
    op.drop_column("nft_metadata", "result_id")

    # Restore old columns
    op.add_column(
        "nft_metadata",
        sa.Column("quiz_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "nft_metadata",
        sa.Column("result_type", sa.String(length=100), nullable=False),
    )

    # Restore foreign key and index
    op.create_foreign_key(
        op.f("fk_nft_metadata_quiz_id_quizzes"),
        "nft_metadata",
        "quizzes",
        ["quiz_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_nft_metadata_quiz_id"),
        "nft_metadata",
        ["quiz_id"],
        unique=False,
    )

    # Revert mint_transactions changes
    op.drop_index(
        op.f("ix_mint_transactions_payment_id"), table_name="mint_transactions"
    )
    op.drop_constraint(
        op.f("fk_mint_transactions_payment_id_payments"),
        "mint_transactions",
        type_="foreignkey",
    )
    op.drop_column("mint_transactions", "retry_count")
    op.drop_column("mint_transactions", "ipfs_hash")
    op.drop_column("mint_transactions", "payment_id")

    # Drop payments table
    op.drop_index(op.f("ix_payments_result_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_table("payments")
