"""Usage / metering models.

This module contains aggregated usage counters (tokens, request counts, etc.)
for AI gateway / infra-style accounting.

Design notes:
- `usage_date` should be a UTC date (no time) to avoid timezone ambiguity.
- Uniqueness on (user_id, usage_date) enables safe upserts.
"""

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    BigInteger,
    Integer,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db.base import Base, IDMixin, TimestampMixin


class UserDailyTokenUsage(Base, IDMixin, TimestampMixin):
    """Aggregate token usage per user per day (UTC)."""

    __tablename__ = "user_daily_token_usage"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # ondelete=“CASCADE”的意思是：如果这个 user_id 被删除，那么和他相关的 usage 行也自动删除。
    # nullable=False是：如果写 user_id=None， 数据库会直接报错。
    usage_date = Column(Date, nullable=False, index=True)  # UTC date

    # Aggregate counters
    total_tokens = Column(BigInteger, default=0, nullable=False)
    prompt_tokens = Column(BigInteger, default=0, nullable=False)
    completion_tokens = Column(BigInteger, default=0, nullable=False)
    request_count = Column(Integer, default=0, nullable=False)

    # Optional breakdown (per model/provider/route/etc.)
    breakdown = Column(JSONB, default=dict, nullable=False)
    # JSONB 是 PostgreSQL 的一种字段类型，JSON 的二进制存储版本（Binary JSON）。

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_user_daily_token_usage_user_date"),
        Index("ix_user_daily_token_usage_date_user", "usage_date", "user_id"),
    )
    # UniqueConstraint那行的意思是：user_id + usage_date 这两个字段的组合必须唯一，即，一个用户一天只能有一行 usage。
    # name="uq_user_daily_token_usage_user_date"是： 给这个约束一个名字。

    user = relationship("User", back_populates="daily_token_usage")

    def __repr__(self) -> str:
        return (
            f"<UserDailyTokenUsage(user_id={self.user_id}, usage_date={self.usage_date}, "
            f"total_tokens={self.total_tokens}, request_count={self.request_count})>"
        )
    # 这是 Python 类的“调试显示方法”。打印的时候，即，print(usage)的时候，
    # 如果没有 __repr__，只能看到<UserDailyTokenUsage object at 0x...>
    # 如果有__repr__的话，就可以看到更可读的内容 比如 <UserDailyTokenUsage(user_id=1, usage_date=2026-02-19, total_tokens=1234, request_count=10)>。