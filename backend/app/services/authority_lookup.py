"""Resolve government authority contact for a geographic area and issue type."""

from __future__ import annotations

import logging
import re

from app.models import ClassificationResult, Location
from app.services.departments import DEPARTMENT_BY_ISSUE, DEPARTMENTS, ISSUE_KEYWORDS
from app.services.geocoding import GeoArea

logger = logging.getLogger(__name__)

# Public-facing municipal complaint contacts (demo / fallback when web search unavailable)
REGIONAL_CONTACTS: dict[str, dict[str, tuple[str, str]]] = {
    "bengaluru": {
        "pothole": ("BBMP Roads & Infrastructure", "complaints@bbmp.gov.in"),
        "garbage": ("BBMP Solid Waste Management", "swm@bbmp.gov.in"),
        "streetlight": ("BBMP Electrical", "electrical@bbmp.gov.in"),
        "water_leak": ("BWSSB Water Supply", "contactus@bwssb.org"),
        "sewage": ("BWSSB Sewerage", "contactus@bwssb.org"),
        "other": ("BBMP Control Room", "complaints@bbmp.gov.in"),
    },
    "bangalore": {
        "pothole": ("BBMP Roads & Infrastructure", "complaints@bbmp.gov.in"),
        "garbage": ("BBMP Solid Waste Management", "swm@bbmp.gov.in"),
        "streetlight": ("BBMP Electrical", "electrical@bbmp.gov.in"),
        "water_leak": ("BWSSB Water Supply", "contactus@bwssb.org"),
        "sewage": ("BWSSB Sewerage", "contactus@bwssb.org"),
        "other": ("BBMP Control Room", "complaints@bbmp.gov.in"),
    },
    "mumbai": {
        "pothole": ("BMC Roads Department", "customercare@mcgm.gov.in"),
        "garbage": ("BMC Solid Waste Management", "customercare@mcgm.gov.in"),
        "streetlight": ("BMC Electrical", "customercare@mcgm.gov.in"),
        "water_leak": ("BMC Water Supply", "customercare@mcgm.gov.in"),
        "sewage": ("BMC Sewerage", "customercare@mcgm.gov.in"),
        "other": ("BMC Control Room", "customercare@mcgm.gov.in"),
    },
    "delhi": {
        "pothole": ("MCD Roads", "mcd@mcddelhi.gov.in"),
        "garbage": ("MCD Sanitation", "mcd@mcddelhi.gov.in"),
        "streetlight": ("MCD Electrical", "mcd@mcddelhi.gov.in"),
        "water_leak": ("Delhi Jal Board", "djb@delhi.gov.in"),
        "sewage": ("Delhi Jal Board Sewerage", "djb@delhi.gov.in"),
        "other": ("MCD Control Room", "mcd@mcddelhi.gov.in"),
    },
    "chennai": {
        "pothole": ("Greater Chennai Corporation Roads", "gcccomplaints@gccservices.in"),
        "garbage": ("GCC Sanitation", "gcccomplaints@gccservices.in"),
        "streetlight": ("GCC Electrical", "gcccomplaints@gccservices.in"),
        "water_leak": ("Metrowater Chennai", "metrowater@chennaimetrorail.org"),
        "sewage": ("GCC Sewerage", "gcccomplaints@gccservices.in"),
        "other": ("GCC Control Room", "gcccomplaints@gccservices.in"),
    },
    "hyderabad": {
        "pothole": ("GHMC Roads", "ghmccomplaints@ghmc.gov.in"),
        "garbage": ("GHMC Sanitation", "ghmccomplaints@ghmc.gov.in"),
        "streetlight": ("GHMC Electrical", "ghmccomplaints@ghmc.gov.in"),
        "water_leak": ("HMWSSB Water", "customercare@hmwssb.gov.in"),
        "sewage": ("HMWSSB Sewerage", "customercare@hmwssb.gov.in"),
        "other": ("GHMC Control Room", "ghmccomplaints@ghmc.gov.in"),
    },
}


def _classify_issue_type(description: str) -> str:
    text = description.lower()
    scores = {k: 0 for k in ISSUE_KEYWORDS}
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[issue_type] += 2 if " " in kw else 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def _city_key(area: GeoArea) -> str:
    for candidate in (area.city, area.municipality, area.state):
        if candidate:
            return candidate.lower().strip()
    return ""


def lookup_authority(area: GeoArea, description: str, issue_type: str | None = None) -> ClassificationResult:
    issue = issue_type or _classify_issue_type(description)
    city_key = _city_key(area)

    # Try regional government contacts first
    for key, contacts in REGIONAL_CONTACTS.items():
        if key in city_key or key in area.display_name.lower():
            dept_name, email = contacts.get(issue, contacts["other"])
            return ClassificationResult(
                issue_type=issue,
                department=dept_name,
                department_email=email,
                confidence=0.85,
                reasoning=(
                    f"Matched regional authority for {area.city or area.municipality} "
                    f"({area.state}, {area.country}). Routed to {dept_name}."
                ),
            )

    # Generic Metro City fallback
    dept_name = DEPARTMENT_BY_ISSUE.get(issue, DEPARTMENT_BY_ISSUE["other"])
    dept = next(d for d in DEPARTMENTS if d["name"] == dept_name)
    area_label = area.city or area.municipality or area.display_name

    return ClassificationResult(
        issue_type=issue,
        department=f"{dept['name']} ({area_label})",
        department_email=dept["contact_email"],
        confidence=0.6,
        reasoning=f"No specific regional contact found for {area_label}. Using default municipal routing.",
    )


def merge_lemma_classification(
    lemma_result: dict,
    area: GeoArea,
    description: str,
) -> ClassificationResult:
    email = lemma_result.get("department_email", "")
    if email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return ClassificationResult(
            issue_type=lemma_result.get("issue_type") or _classify_issue_type(description),
            department=lemma_result.get("department") or "Municipal Authority",
            department_email=email,
            confidence=float(lemma_result.get("confidence", 0.8)),
            reasoning=lemma_result.get("reasoning", "Lemma agent identified authority via knowledge base and web search."),
        )
    return lookup_authority(area, description, lemma_result.get("issue_type"))
