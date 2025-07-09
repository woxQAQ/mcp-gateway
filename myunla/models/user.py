from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.mcp import Mcp
from myunla.models.base import Base, EnumColumn, random_id


def utc_now():
    return datetime.now(UTC)


class Role(Enum):
    NORMAL = "normal"
    ADMIN = "admin"


class AuditResource(Enum):
    """Audit resource types"""

    COLLECTION = "collection"
    DOCUMENT = "document"
    BOT = "bot"
    CHAT = "chat"
    MESSAGE = "message"
    API_KEY = "api_key"
    LLM_PROVIDER = "llm_provider"
    LLM_PROVIDER_MODEL = "llm_provider_model"
    MODEL_SERVICE_PROVIDER = "model_service_provider"
    USER = "user"
    CONFIG = "config"
    INVITATION = "invitation"
    AUTH = "auth"
    CHAT_COMPLETION = "chat_completion"
    SEARCH = "search"
    LLM = "llm"
    FLOW = "flow"
    SYSTEM = "system"


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        String(24), primary_key=True, default=lambda: "user" + random_id()
    )
    username: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False
    )  # Unified with other user fields
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[Role] = mapped_column(
        EnumColumn(Role), nullable=False, default=Role.NORMAL.value
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_staff: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )  # Unified naming with other time fields
    gmt_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_deleted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (UniqueConstraint(email, name="uidx_user_email"),)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, value):
        self.hashed_password = value


class Tenant(Base):
    __tablename__ = "tenant"
    id: Mapped[str] = mapped_column(
        String(24), primary_key=True, default=lambda: "tenant" + random_id()
    )
    name: Mapped[str] = mapped_column(String(256), nullable=True)
    prefix: Mapped[str] = mapped_column(String(256), nullable=True)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    gmt_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(name, name="uidx_tenant_name"),
        UniqueConstraint(prefix, name="uidx_tenant_prefix"),
    )


class UserTenant(Base):
    __tablename__ = "user_tenant"
    id: Mapped[str] = mapped_column(
        String(24),
        primary_key=True,
        default=lambda: "user_tenant" + random_id(),
    )
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    tenant_name: Mapped[str] = mapped_column(String(24), nullable=False)
    gmt_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            user_id,
            tenant_name,
            name="uidx_user_tenant_user_id_tenant_name",
        ),
    )


class McpConfig(Base):
    __tablename__ = "mcp_config"
    id: Mapped[str] = mapped_column(
        String(24), primary_key=True, default=lambda: "mcp_config" + random_id()
    )
    name: Mapped[str] = mapped_column(String(256), nullable=True)
    tenant_name: Mapped[str] = mapped_column(String(24), nullable=False)
    routers: Mapped[dict] = mapped_column(JSON, nullable=False)
    servers: Mapped[dict] = mapped_column(JSON, nullable=False)
    tools: Mapped[dict] = mapped_column(JSON, nullable=False)
    http_servers: Mapped[dict] = mapped_column(JSON, nullable=False)
    gmt_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_deleted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            name, tenant_name, name="uidx_mcp_config_name_tenant_name"
        ),
        Index("idx_mcp_config_deleted_at", gmt_deleted),
    )

    @classmethod
    def from_mcp(cls, obj: Mcp):
        return cls(
            name=obj.name,
            tenant_name=obj.tenant_name,
            routers=obj.routers,
            servers=obj.servers,
            tools=obj.tools,
            http_servers=obj.http_servers,
            gmt_created=utc_now(),
            gmt_updated=utc_now(),
        )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: random_id()
    )
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=True, comment="User ID"
    )
    username: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="Username"
    )
    resource_type: Mapped[AuditResource] = mapped_column(
        EnumColumn(AuditResource), nullable=True, comment="Resource type"
    )
    resource_id: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Resource ID (extracted at query time)",
    )
    api_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="API operation name"
    )
    http_method: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="HTTP method (POST, PUT, DELETE)"
    )
    path: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="API path"
    )
    status_code: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="HTTP status code"
    )
    request_data: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Request data (JSON)"
    )
    response_data: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Response data (JSON)"
    )
    error_message: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Error message if failed"
    )
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=True, comment="Client IP address"
    )
    user_agent: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="User agent string"
    )
    request_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Request ID for tracking"
    )
    start_time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Request start time (milliseconds since epoch)",
    )
    end_time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Request end time (milliseconds since epoch)",
    )
    gmt_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        comment="Created time",
    )

    # Index for better query performance
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_resource_type", "resource_type"),
        Index("idx_audit_api_name", "api_name"),
        Index("idx_audit_http_method", "http_method"),
        Index("idx_audit_status_code", "status_code"),
        Index("idx_audit_gmt_created", "gmt_created"),
        Index("idx_audit_resource_id", "resource_id"),
        Index("idx_audit_request_id", "request_id"),
        Index("idx_audit_start_time", "start_time"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, api={self.api_name}, method={self.http_method}, status={self.status_code})>"
