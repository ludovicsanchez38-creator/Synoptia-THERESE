"""local_first_imap_caldav_fields

Adds IMAP/SMTP fields to email_accounts and provider/CalDAV fields to calendars.
Part of the "Local First" architecture.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Local First fields."""

    # =============================================
    # EMAIL ACCOUNTS - IMAP/SMTP fields
    # =============================================

    # Make OAuth fields nullable (already nullable in practice for SQLite)
    # SQLite doesn't support ALTER COLUMN, so we only add new columns

    # IMAP config
    with op.batch_alter_table("email_accounts") as batch_op:
        batch_op.add_column(sa.Column("imap_host", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"))
        batch_op.add_column(sa.Column("imap_username", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("imap_password", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("smtp_host", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"))
        batch_op.add_column(sa.Column("smtp_use_tls", sa.Boolean(), nullable=False, server_default="1"))

    # =============================================
    # CALENDARS - Provider/CalDAV fields
    # =============================================

    with op.batch_alter_table("calendars") as batch_op:
        # Provider config
        batch_op.add_column(sa.Column("provider", sa.String(), nullable=False, server_default="google"))
        batch_op.add_column(sa.Column("remote_id", sa.String(), nullable=True))

        # CalDAV config
        batch_op.add_column(sa.Column("caldav_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("caldav_username", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("caldav_password", sa.String(), nullable=True))

        # Sync status
        batch_op.add_column(sa.Column("sync_status", sa.String(), nullable=False, server_default="idle"))
        batch_op.add_column(sa.Column("last_sync_error", sa.String(), nullable=True))

        # Timestamps
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove Local First fields."""

    with op.batch_alter_table("calendars") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("last_sync_error")
        batch_op.drop_column("sync_status")
        batch_op.drop_column("caldav_password")
        batch_op.drop_column("caldav_username")
        batch_op.drop_column("caldav_url")
        batch_op.drop_column("remote_id")
        batch_op.drop_column("provider")

    with op.batch_alter_table("email_accounts") as batch_op:
        batch_op.drop_column("smtp_use_tls")
        batch_op.drop_column("smtp_port")
        batch_op.drop_column("smtp_host")
        batch_op.drop_column("imap_password")
        batch_op.drop_column("imap_username")
        batch_op.drop_column("imap_port")
        batch_op.drop_column("imap_host")
