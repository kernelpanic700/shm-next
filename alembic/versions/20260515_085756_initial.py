"""Initial migration — all tables.

Revision ID: initial
Revises:
Create Date: 2026-05-15T08:57:56.816810

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Abonents ---
    op.create_table(
        'abonents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('account_number', sa.String(20), nullable=False),
        sa.Column('balance', sa.Numeric(precision=12, scale=4), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('allow_negative', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('tariff_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('account_number'),
        sa.Index('idx_abonents_status', 'status'),
        sa.Index('idx_abonents_balance', 'balance'),
        sa.Index('idx_abonents_account', 'account_number'),
    )

    # --- Tariffs ---
    op.create_table(
        'tariffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('services', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('price', sa.Numeric(precision=12, scale=4), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('billing_period', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.Index('idx_tariffs_active', 'is_active'),
        sa.Index('idx_tariffs_name', 'name'),
    )

    # --- Services ---
    op.create_table(
        'user_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='INIT'),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cost', sa.Numeric(precision=12, scale=4), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.Index('idx_services_abonent', 'abonent_id'),
        sa.Index('idx_services_status', 'status'),
        sa.Index('idx_services_type', 'service_type'),
    )

    # --- Payments ---
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='NEW'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', name='idx_payments_external'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.Index('idx_payments_abonent', 'abonent_id'),
        sa.Index('idx_payments_status', 'status'),
    )

    # --- Withdraws ---
    op.create_table(
        'withdraws',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('strategy', sa.String(20), nullable=False, server_default='honest'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(2000), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.ForeignKeyConstraint(['service_id'], ['user_services.id']),
        sa.Index('idx_withdraws_abonent', 'abonent_id'),
        sa.Index('idx_withdraws_status', 'status'),
    )

    # --- Tariff Services ---
    op.create_table(
        'tariff_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tariff_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cost', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('unit', sa.String(20), nullable=False, server_default='day'),
        sa.Column('is_optional', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tariff_id'], ['tariffs.id']),
        sa.UniqueConstraint('tariff_id', 'service_type', name='uq_tariff_service_type'),
        sa.Index('idx_tariff_services_tariff', 'tariff_id'),
    )

    # --- Sessions ---
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(2000), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.Index('idx_sessions_abonent', 'abonent_id'),
        sa.Index('idx_sessions_expires', 'expires_at'),
        sa.Index('idx_sessions_active', 'is_active'),
    )

    # --- Invoices ---
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.Index('idx_invoices_abonent', 'abonent_id'),
        sa.Index('idx_invoices_status', 'status'),
        sa.Index('idx_invoices_due_date', 'due_date'),
    )

    # --- Discounts ---
    op.create_table(
        'discounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(2000), nullable=False, server_default=''),
        sa.Column('discount_type', sa.String(20), nullable=False, server_default='percent'),
        sa.Column('value', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('max_uses', sa.Integer, nullable=True),
        sa.Column('used_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_discounts_active', 'is_active'),
        sa.Index('idx_discounts_type', 'discount_type'),
    )

    # --- Bonus Entries ---
    op.create_table(
        'bonus_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('reason', sa.String(500), nullable=False, server_default=''),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_bonus_entries_abonent', 'abonent_id'),
        sa.Index('idx_bonus_entries_active', 'is_active'),
        sa.Index('idx_bonus_entries_expires', 'expires_at'),
    )

    # --- Spool Tasks ---
    op.create_table(
        'spool_tasks',
        sa.Column('id', sa.Integer, autoincrement=True, nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='50'),
        sa.Column('status', sa.String(20), nullable=False, server_default='NEW'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('execute_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON, nullable=True),
        sa.Column('error_message', sa.String(2000), nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_spool_status', 'status'),
        sa.Index('idx_spool_priority', 'priority'),
        sa.Index('idx_spool_action_type', 'action_type'),
    )

    # --- Audit Logs ---
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=False),
        sa.Column('old_values', sa.JSON, nullable=True),
        sa.Column('new_values', sa.JSON, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_audit_actor', 'actor_id'),
        sa.Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

    # --- Notifications ---
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('abonent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['abonent_id'], ['abonents.id']),
        sa.Index('idx_notifications_abonent', 'abonent_id'),
        sa.Index('idx_notifications_status', 'status'),
    )

    # --- Webhooks ---
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('events', sa.JSON, nullable=False),
        sa.Column('secret', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('version', sa.BigInteger, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_webhooks_active', 'is_active'),
    )


def downgrade() -> None:
    op.drop_table('webhooks')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('spool_tasks')
    op.drop_table('bonus_entries')
    op.drop_table('discounts')
    op.drop_table('invoices')
    op.drop_table('sessions')
    op.drop_table('tariff_services')
    op.drop_table('withdraws')
    op.drop_table('payments')
    op.drop_table('user_services')
    op.drop_table('tariffs')
    op.drop_table('abonents')
