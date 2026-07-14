"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('auth_provider', sa.String(50), default='local'),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('repository_url', sa.String(500), nullable=True),
        sa.Column('local_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), default='pending', index=True),
        sa.Column('current_agent', sa.String(50), nullable=True),
        sa.Column('workflow_state', sa.String(50), default='initialized'),
        sa.Column('workflow_data', JSONB, default={}),
        sa.Column('budget_limit', sa.Numeric(10, 4), default=0.10),
        sa.Column('current_cost', sa.Numeric(10, 6), default=0),
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('result_json', JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])

    # Agent Runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='running'),
        sa.Column('input_json', JSONB, nullable=True),
        sa.Column('output_json', JSONB, nullable=True),
        sa.Column('tokens_input', sa.Integer, default=0),
        sa.Column('tokens_output', sa.Integer, default=0),
        sa.Column('cost_usd', sa.Numeric(10, 6), default=0),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_agent_runs_task_id', 'agent_runs', ['task_id'])

    # User Preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('preferred_provider', sa.String(50), default='deepseek'),
        sa.Column('preferred_model', sa.String(100), default='deepseek/deepseek-chat'),
        sa.Column('temperature', sa.Numeric(3, 2), default=0.2),
        sa.Column('max_tokens', sa.Integer, default=4096),
        sa.Column('default_budget_limit', sa.Numeric(10, 4), default=0.10),
        sa.Column('daily_budget_limit', sa.Numeric(10, 4), default=1.00),
        sa.Column('theme', sa.String(20), default='light'),
        sa.Column('editor_font_size', sa.Integer, default=14),
        sa.Column('show_token_counts', sa.Boolean, default=True),
        sa.Column('email_notifications', sa.Boolean, default=False),
        sa.Column('task_completion_notifications', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('user_preferences')
    op.drop_table('agent_runs')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('users')
