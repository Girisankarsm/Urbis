# Verified authority research prompt
#
# Use this prompt offline (Cursor, Claude, etc.) to research ONE city at a time,
# then add rows to backend/app/data/verified_authorities.json.
#
# Rules:
# - DO NOT guess emails — only include published addresses with source_url
# - Prefer email > portal > helpline > CPGRAMS (national fallback is already in JSON)
# - issue types: pothole, garbage, streetlight, water_leak, sewage, other
#
# --- PROMPT (replace [CITY NAME]) ---
#
# I'm building a civic complaint routing system for Indian cities. For the city of
# [CITY NAME], find and verify the REAL, currently published contact channels for
# these issue types: pothole, garbage, streetlight, water_leak, sewage, other.
#
# For each issue type, search the official municipal corporation website and any
# government grievance portal, then report back:
#
# 1. Department name (exact, as published)
# 2. Channel type — pick only what actually exists:
#    - "email" — ONLY if you find a real published email (cite source URL)
#    - "portal" — grievance/PGR system URL
#    - "helpline" — civic complaint phone number
# 3. Source URL for each claim — no source, no entry
#
# Output as JSON matching verified_authorities.json city entry format.
