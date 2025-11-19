"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-11-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('telegram_id', name=op.f('uq_users_telegram_id'))
    )
    op.create_index(op.f('ix_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_quizzes_created_by_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_quizzes'))
    )
    op.create_index(op.f('ix_created_by'), 'quizzes', ['created_by'], unique=False)

    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_questions_quiz_id_quizzes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_questions'))
    )
    op.create_index(op.f('ix_quiz_id'), 'questions', ['quiz_id'], unique=False)

    # Create answers table
    op.create_table(
        'answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(length=512), nullable=False),
        sa.Column('result_type', sa.String(length=100), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_answers_question_id_questions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_answers'))
    )
    op.create_index(op.f('ix_question_id'), 'answers', ['question_id'], unique=False)

    # Create result_types table
    op.create_table(
        'result_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('type_key', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_result_types_quiz_id_quizzes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_result_types'))
    )
    op.create_index(op.f('ix_result_types_quiz_id'), 'result_types', ['quiz_id'], unique=False)

    # Create quiz_results table
    op.create_table(
        'quiz_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('answers_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result_type', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('nft_minted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nft_address', sa.String(length=255), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_quiz_results_quiz_id_quizzes'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_quiz_results_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_results'))
    )
    op.create_index(op.f('ix_quiz_results_user_id'), 'quiz_results', ['user_id'], unique=False)
    op.create_index(op.f('ix_quiz_results_quiz_id'), 'quiz_results', ['quiz_id'], unique=False)

    # Create mint_transactions table
    op.create_table(
        'mint_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nft_address', sa.String(length=255), nullable=True),
        sa.Column('transaction_hash', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('metadata_uri', sa.String(length=512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['result_id'], ['quiz_results.id'], name=op.f('fk_mint_transactions_result_id_quiz_results'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mint_transactions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mint_transactions')),
        sa.UniqueConstraint('result_id', name=op.f('uq_mint_transactions_result_id'))
    )
    op.create_index(op.f('ix_mint_transactions_result_id'), 'mint_transactions', ['result_id'], unique=True)
    op.create_index(op.f('ix_mint_transactions_user_id'), 'mint_transactions', ['user_id'], unique=False)

    # Create nft_metadata table
    op.create_table(
        'nft_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('result_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=512), nullable=False),
        sa.Column('attributes_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_nft_metadata_quiz_id_quizzes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_nft_metadata'))
    )
    op.create_index(op.f('ix_nft_metadata_quiz_id'), 'nft_metadata', ['quiz_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_nft_metadata_quiz_id'), table_name='nft_metadata')
    op.drop_table('nft_metadata')

    op.drop_index(op.f('ix_mint_transactions_user_id'), table_name='mint_transactions')
    op.drop_index(op.f('ix_mint_transactions_result_id'), table_name='mint_transactions')
    op.drop_table('mint_transactions')

    op.drop_index(op.f('ix_quiz_results_quiz_id'), table_name='quiz_results')
    op.drop_index(op.f('ix_quiz_results_user_id'), table_name='quiz_results')
    op.drop_table('quiz_results')

    op.drop_index(op.f('ix_result_types_quiz_id'), table_name='result_types')
    op.drop_table('result_types')

    op.drop_index(op.f('ix_question_id'), table_name='answers')
    op.drop_table('answers')

    op.drop_index(op.f('ix_quiz_id'), table_name='questions')
    op.drop_table('questions')

    op.drop_index(op.f('ix_created_by'), table_name='quizzes')
    op.drop_table('quizzes')

    op.drop_index(op.f('ix_telegram_id'), table_name='users')
    op.drop_table('users')
