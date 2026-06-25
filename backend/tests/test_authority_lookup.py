from app.services.authority_lookup import lookup_authority
from app.services.geocoding import GeoArea


def test_lookup_authority_bengaluru_pothole():
    area = GeoArea(
        display_name="Bengaluru, Karnataka, India",
        city="Bengaluru",
        state="Karnataka",
        country="India",
        municipality="BBMP",
        lat=12.97,
        lng=77.59,
    )
    result = lookup_authority(area, "large pothole on main road")
    assert result.issue_type == "pothole"
    assert "BBMP" in result.department
    assert result.department_email.endswith(".gov.in") or "@" in result.department_email


def test_lookup_authority_defaults_to_other():
    area = GeoArea(
        display_name="Unknown Town",
        city="Unknown Town",
        state="",
        country="India",
        municipality="",
        lat=0.0,
        lng=0.0,
    )
    result = lookup_authority(area, "random issue")
    assert result.issue_type == "other"
    assert result.department_email
