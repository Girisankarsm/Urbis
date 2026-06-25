from app.services.authority_discovery import (
    _pick_best_email,
    _score_email,
)
from app.services.geocoding import GeoArea


def test_score_email_prefers_gov_in():
    area = GeoArea(
        display_name="Thiruvananthapuram, Kerala, India",
        city="Thiruvananthapuram",
        state="Kerala",
        country="India",
        municipality="TMC",
        lat=8.5,
        lng=76.9,
    )
    assert _score_email("secretary@tmcofficials.in", area, "pothole") > _score_email(
        "fake@mcmc-demo.gov", area, "pothole"
    )


def test_pick_best_email_trivandrum_contacts():
    area = GeoArea(
        display_name="Thiruvananthapuram, Kerala, India",
        city="Thiruvananthapuram",
        state="Kerala",
        country="India",
        municipality="TMC",
        lat=8.5,
        lng=76.9,
    )
    emails = [
        "secretary@tmcofficials.in",
        "thiruvananthapuramtmc@gmail.com",
        "roads@mcmc-demo.gov",
        "noreply@example.com",
    ]
    assert _pick_best_email(emails, area, "garbage") == "thiruvananthapuramtmc@gmail.com"
    assert _pick_best_email(emails, area, "pothole") == "secretary@tmcofficials.in"
