"""UserProfile model storing constraints, visa status, and tone directives."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.cv_block import CVBlock


class UserProfile(Base, UUIDMixin, TimestampMixin):
    """Stores user career profile, work authorization constraints, and preferences."""

    __tablename__ = "user_profile"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    visa_status: Mapped[str] = mapped_column(
        String(100), default="None", nullable=False
    )
    remote_preference: Mapped[str] = mapped_column(
        String(50), default="Remote", nullable=False
    )
    tone_directives: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    target_locations: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Relationships
    cv_blocks: Mapped[list["CVBlock"]] = relationship(
        "CVBlock",
        back_populates="user_profile",
        cascade="all, delete-orphan",
    )
