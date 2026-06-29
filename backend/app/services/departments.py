DEPARTMENTS = [
    {
        "name": "Roads & Infrastructure Department",
        "issue_types": ["pothole", "road_damage", "sidewalk", "other"],
        "contact_email": "roads@mcmc-demo.gov",
        "jurisdiction_area": "All public roads and sidewalks in Metro City",
    },
    {
        "name": "Sanitation & Waste Management Department",
        "issue_types": ["garbage", "illegal_dumping", "overflowing_bin"],
        "contact_email": "sanitation@mcmc-demo.gov",
        "jurisdiction_area": "Waste collection and street cleaning in Metro City",
    },
    {
        "name": "Electrical & Street Lighting Department",
        "issue_types": ["streetlight", "broken_light", "electrical_hazard"],
        "contact_email": "electrical@mcmc-demo.gov",
        "jurisdiction_area": "Public lighting and electrical infrastructure",
    },
    {
        "name": "Water Supply Department",
        "issue_types": ["water_leak", "burst_pipe", "water_quality"],
        "contact_email": "water@mcmc-demo.gov",
        "jurisdiction_area": "Public water supply mains and hydrants",
    },
    {
        "name": "Sewerage & Drainage Department",
        "issue_types": ["sewage", "blocked_drain", "manhole", "flooding"],
        "contact_email": "sewerage@mcmc-demo.gov",
        "jurisdiction_area": "Sewer lines, drains, and manholes",
    },
]

ISSUE_KEYWORDS: dict[str, list[str]] = {
    "pothole": ["pothole", "hole", "road damage", "crack", "asphalt", "pavement"],
    "garbage": ["garbage", "trash", "waste", "dump", "litter", "bin", "rubbish"],
    "streetlight": ["streetlight", "street light", "lamp", "lighting", "dark", "bulb"],
    "water_leak": ["water leak", "leak", "pipe", "burst", "flooding water", "hydrant"],
    "sewage": ["sewage", "sewer", "drain", "drainage", "manhole", "overflow", "stench", "canal", "storm water"],
}

DEPARTMENT_BY_ISSUE = {
    "pothole": "Roads & Infrastructure Department",
    "garbage": "Sanitation & Waste Management Department",
    "streetlight": "Electrical & Street Lighting Department",
    "water_leak": "Water Supply Department",
    "sewage": "Sewerage & Drainage Department",
    "other": "Roads & Infrastructure Department",
}
