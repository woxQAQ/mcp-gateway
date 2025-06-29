from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from myunla.models.base import Base, EnumColumn, random_id
from myunla.utils.utils import utc_now


class Role(StrEnum):
    NORMAL = "normal"
    ADMIN = "admin"


class AuditResource(StrEnum):
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

    id = Column(
        String(24), primary_key=True, default=lambda: "user" + random_id()
    )
    username = Column(
        String(256), unique=True, nullable=False
    )  # Unified with other user fields
    email = Column(String(254), unique=True, nullable=True)
    hashed_password = Column(String(128), nullable=False)
    role = Column(EnumColumn(Role), nullable=False, default=Role.NORMAL)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    date_joined = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )  # Unified naming with other time fields
    gmt_created = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint(email, name="uidx_user_email"),)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, value):
        self.hashed_password = value


class Tenant(Base):
    __tablename__ = "tenant"
    id = Column(
        String(24), primary_key=True, default=lambda: "tenant" + random_id()
    )
    name = Column(String(256), nullable=True)
    prefix = Column(String(256), nullable=True)
    description = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    gmt_created = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(name, name="uidx_tenant_name"),
        UniqueConstraint(prefix, name="uidx_tenant_prefix"),
    )


class UserTenant(Base):
    __tablename__ = "user_tenant"
    id = Column(
        String(24),
        primary_key=True,
        default=lambda: "user_tenant" + random_id(),
    )
    user_id = Column(String(24), nullable=False)
    tenant_id = Column(String(24), nullable=False)
    gmt_created = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            user_id,
            tenant_id,
            name="uidx_user_tenant_user_id_tenant_id",
        ),
    )


class McpConfig(Base):
    __tablename__ = "mcp_config"
    id = Column(
        String(24), primary_key=True, default=lambda: "mcp_config" + random_id()
    )
    name = Column(String(256), nullable=True)
    tenant_id = Column(String(24), nullable=False)
    routers = Column(JSON, nullable=False)
    servers = Column(JSON, nullable=False)
    tools = Column(JSON, nullable=False)
    http_servers = Column(JSON, nullable=False)
    gmt_created = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_updated = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            name, tenant_id, name="uidx_mcp_config_name_tenant_id"
        ),
        Index("idx_mcp_config_deleted_at", gmt_deleted),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: random_id())
    user_id = Column(String(36), nullable=True, comment="User ID")
    username = Column(String(255), nullable=True, comment="Username")
    resource_type = Column(
        EnumColumn(AuditResource), nullable=True, comment="Resource type"
    )
    resource_id = Column(
        String(255),
        nullable=True,
        comment="Resource ID (extracted at query time)",
    )
    api_name = Column(String(255), nullable=False, comment="API operation name")
    http_method = Column(
        String(10), nullable=False, comment="HTTP method (POST, PUT, DELETE)"
    )
    path = Column(String(512), nullable=False, comment="API path")
    status_code = Column(Integer, nullable=True, comment="HTTP status code")
    request_data = Column(Text, nullable=True, comment="Request data (JSON)")
    response_data = Column(Text, nullable=True, comment="Response data (JSON)")
    error_message = Column(
        Text, nullable=True, comment="Error message if failed"
    )
    ip_address = Column(String(45), nullable=True, comment="Client IP address")
    user_agent = Column(String(500), nullable=True, comment="User agent string")
    request_id = Column(
        String(255), nullable=False, comment="Request ID for tracking"
    )
    start_time = Column(
        BigInteger,
        nullable=False,
        comment="Request start time (milliseconds since epoch)",
    )
    end_time = Column(
        BigInteger,
        nullable=True,
        comment="Request end time (milliseconds since epoch)",
    )
    gmt_created = Column(
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
