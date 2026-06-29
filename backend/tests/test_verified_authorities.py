"""Verified authority directory tests."""

from app.services.authority_lookup import lookup_authority
from app.services.geocoding import GeoArea
from app.services.verified_authorities import list_verified_cities, lookup_verified_authority, resolve_verified_city_key


def test_resolve_chengalpattu_from_urapakkam():
    area = GeoArea(
        display_name="Urapakkam, Vandalur, Chengalpattu, Tamil Nadu, India",
        city="Chengalpattu",
        district="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        municipality="Chengalpattu",
        lat=12.85,
        lng=80.08,
    )
    assert resolve_verified_city_key(area) == "chengalpattu"


def test_verified_chengalpattu_garbage_email():
    area = GeoArea(
        display_name="Urapakkam, Chengalpattu, Tamil Nadu, India",
        city="Chengalpattu",
        district="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        municipality="Chengalpattu",
        lat=12.85,
        lng=80.08,
    )
    result = lookup_verified_authority(area, "garbage on street", "garbage")
    assert result is not None
    assert result.authority_source == "verified"
    assert result.contact_channel == "email"
    assert result.department_email == "commr.chengalpattu@tn.gov.in"
    assert result.source_url.startswith("https://")


def test_verified_chengalpattu_drainage_portal():
    area = GeoArea(
        display_name="Urapakkam, Chengalpattu, Tamil Nadu, India",
        city="Chengalpattu",
        district="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        municipality="Chengalpattu",
        lat=12.85,
        lng=80.08,
    )
    result = lookup_authority(area, "Drainage issue in urapakkam")
    assert result.issue_type == "sewage"
    assert result.authority_source == "verified"
    assert result.contact_channel == "portal"
    assert result.contact_value == "https://gdp.tn.gov.in"


def test_verified_chennai_garbage():
    area = GeoArea(
        display_name="T. Nagar, Chennai, Tamil Nadu, India",
        city="Chennai",
        state="Tamil Nadu",
        country="India",
        municipality="Greater Chennai Corporation",
        lat=13.04,
        lng=80.23,
    )
    result = lookup_authority(area, "garbage pile")
    assert result.authority_source == "verified"
    assert result.department_email == "seswm@chennaicorporation.gov.in"


def test_cpgrams_fallback_for_unknown_country():
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
    assert result.authority_source == "cpgrams"
    assert result.contact_channel == "portal"
    assert "pgportal.gov.in" in result.contact_value


def test_list_verified_cities_includes_major_metros():
    cities = list_verified_cities()
    assert "chennai" in cities
    assert "chengalpattu" in cities
    assert "bengaluru" in cities
