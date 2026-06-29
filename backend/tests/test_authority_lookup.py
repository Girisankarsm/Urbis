from app.services.authority_lookup import lookup_authority, resolve_region_key
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


def test_lookup_authority_urapakkam_pothole():
    area = GeoArea(
        display_name="Urapakkam, Vandalur, Chengalpattu, Tamil Nadu, 603211, India",
        city="Chengalpattu",
        district="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        municipality="Chengalpattu",
        lat=12.85,
        lng=80.08,
    )
    result = lookup_authority(area, "large pothole on the road")
    assert result.issue_type == "pothole"
    assert "Chengalpattu" in result.department
    assert "Chennai" not in result.department
    assert result.department_email == "commr.chengalpattu@tn.gov.in"


def test_lookup_authority_urapakkam_drainage():
    area = GeoArea(
        display_name="Urapakkam, Vandalur, Chengalpattu, Tamil Nadu, 603211, India",
        city="Chengalpattu",
        district="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        municipality="Chengalpattu",
        lat=12.8578,
        lng=80.0658,
    )
    result = lookup_authority(area, "Drainage issue in urapakkam")
    assert result.issue_type == "sewage"
    assert "Chengalpattu" in result.department
    assert "Drainage" in result.department
    assert result.department_email == "commr.chengalpattu@tn.gov.in"


def test_lookup_authority_chennai_garbage_uses_gcc():
    area = GeoArea(
        display_name="T. Nagar, Chennai, Tamil Nadu, India",
        city="Chennai",
        district="Chennai",
        state="Tamil Nadu",
        country="India",
        municipality="Greater Chennai Corporation",
        lat=13.04,
        lng=80.23,
    )
    result = lookup_authority(area, "garbage pile on street")
    assert result.issue_type == "garbage"
    assert "Chennai" in result.department
    assert result.department_email == "seswm@chennaicorporation.gov.in"


def test_lookup_authority_pune_garbage():
    area = GeoArea(
        display_name="Shivajinagar, Pune, Maharashtra, India",
        city="Pune",
        state="Maharashtra",
        country="India",
        municipality="Pune",
        lat=18.53,
        lng=73.85,
    )
    result = lookup_authority(area, "garbage pile on street")
    assert result.issue_type == "garbage"
    assert result.department_email == "pmc@punecorporation.org"


def test_lookup_authority_metro_suburb_whitefield():
    area = GeoArea(
        display_name="Whitefield, Bengaluru Urban, Karnataka, India",
        city="",
        suburb="Whitefield",
        district="Bengaluru Urban",
        state="Karnataka",
        country="India",
        municipality="Bengaluru",
        lat=12.97,
        lng=77.75,
    )
    key, kind = resolve_region_key(area)
    assert key == "bengaluru"
    assert kind in {"city", "metro"}
    result = lookup_authority(area, "broken streetlight")
    assert "BBMP" in result.department


def test_lookup_authority_state_fallback_tirunelveli():
    area = GeoArea(
        display_name="Small Town, Tirunelveli, Tamil Nadu, India",
        city="Tirunelveli",
        district="Tirunelveli",
        state="Tamil Nadu",
        country="India",
        municipality="Tirunelveli",
        lat=8.73,
        lng=77.76,
    )
    key, kind = resolve_region_key(area)
    assert key == "tirunelveli"
    assert kind == "state"
    result = lookup_authority(area, "water leak on road")
    assert result.department_email == "rdma.tirunelveli@tn.gov.in"


def test_lookup_authority_defaults_to_other():
    area = GeoArea(
        display_name="Unknown Town",
        city="Unknown Town",
        state="",
        country="Atlantis",
        municipality="",
        lat=0.0,
        lng=0.0,
    )
    result = lookup_authority(area, "random issue")
    assert result.issue_type == "other"
    assert result.authority_source == "unknown"
