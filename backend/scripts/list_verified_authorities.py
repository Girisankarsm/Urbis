#!/usr/bin/env python3
"""List cities in the verified authority directory."""

from app.services.verified_authorities import _load_data, list_verified_cities

if __name__ == "__main__":
    data = _load_data()
    print("Verified authority cities:")
    for city in list_verified_cities():
        entry = data["cities"][city]
        issues = ", ".join(sorted(entry.get("issues", {}).keys()))
        print(f"  - {city} ({entry.get('display_name', city)}): {issues}")
    print(f"\nNational fallback: {data.get('national_fallback', {}).get('value')}")
