"""
Core utility functions and input sanitization helpers.
"""

import uuid

from fastapi import HTTPException, status


def parse_uuid_or_400(val: str | None, field_name: str = "id") -> uuid.UUID:
    """
    Safely parse a string into a UUID or raise HTTP 400 Bad Request.

    Args:
        val: The string value to parse.
        field_name: The name of the field for the error message.

    Returns:
        Validated uuid.UUID instance.

    Raises:
        HTTPException(status_code=400) if the string is not a valid UUID format.
    """
    if not val or not str(val).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field_name}' must be a non-empty UUID string.",
        )
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, AttributeError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} UUID format.",
        ) from err
