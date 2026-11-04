"""
Pre-compiled regular expression patterns used across domain models and extraction pipelines.
"""

import re

# Calendar year pattern matching 1900-2099
RE_CALENDAR_YEAR: re.Pattern[str] = re.compile(r"\b(19\d{2}|20\d{2})\b")

# Strips all non-alphanumeric characters
RE_NON_ALPHANUMERIC: re.Pattern[str] = re.compile(r"[^a-z0-9]")

# Normalizes contiguous whitespace
RE_WHITESPACE: re.Pattern[str] = re.compile(r"\s+")

# Matches standard resume bullet point leading markers
RE_BULLET_PREFIX: re.Pattern[str] = re.compile(r"^[•\-*–\d.)\s]+")

# Matches trailing corporate entity suffixes (e.g., inc, llc, ltd)
RE_CORP_SUFFIX: re.Pattern[str] = re.compile(r"(inc|llc|ltd|corp|co|gmbh|sa)$")

# Matches common geographic city suffixes in job titles
RE_JOB_TITLE_GEO_DASH: re.Pattern[str] = re.compile(
    r"\s*-\s*(nyc|new york|sf|san francisco|toronto|boston|austin|seattle|chicago|london|berlin|munich|madrid|dublin|bengaluru|singapore|sydney|remote)\b",
    re.IGNORECASE,
)

# Matches trailing geographic or remote parentheses in job titles
RE_JOB_TITLE_GEO_PARENS: re.Pattern[str] = re.compile(
    r"\s*\((remote\s+[a-z]+|remote|us|usa|emea|apac|latam|canada)\)\s*$",
    re.IGNORECASE,
)
