"""
UserProfile model storing constraints, visa status, and tone directives.

This table represents the central candidate profile in Career-OS. It anchors
the user's identity, work authorization constraints, target career aspirations,
and stylistic tone directives.

Constraint Modeling:
  - Work Authorization: ``visa_status`` (e.g. 'H-1B', 'F-1 OPT', 'Citizen')
    is evaluated by the Hunter agent to filter out job listings that do not offer
    sponsorship.
  - Tone Directives: Stored as JSON, capturing preferences like brevity,
    assertiveness, and technical depth synthesized by the Reflector agent.
  - Foreign Key Constraint Policy: The ``cv_blocks`` relationship enforces
    strict ``ON DELETE RESTRICT`` semantics per project rules. A user profile
    cannot be dropped while associated achievement blocks exist, preventing
    accidental cascading data loss of verified candidate history.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.cv_block import CVBlock


class UserProfile(Base, UUIDMixin, TimestampMixin):
    """
    Stores user career profile, work authorization constraints, and preferences.

    Attributes:
        full_name: Candidate full legal or professional name.
        email: Unique, indexed contact email address.
        visa_status: Work authorization category (e.g. 'None', 'H-1B', 'OPT').
        remote_preference: Workplace policy preference (e.g. 'Remote', 'Hybrid').
        tone_directives: JSON dictionary of stylistic and tone hyperparameters.
        target_roles: JSON list of job titles sought (e.g. ['Senior AI Engineer']).
        target_locations: JSON list of target cities or 'Remote'.
        cv_blocks: One-to-many relationship to career achievement chunks.
    """

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
    )
