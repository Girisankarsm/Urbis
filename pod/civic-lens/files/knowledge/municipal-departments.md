# Metro City Municipal Corporation — Department Directory

Jurisdiction: **Metro City Municipal Corporation (MCMC)** — a generic demo municipality.

Use this knowledge base to route citizen-reported civic issues to the correct department.

## Roads & Infrastructure Department

- **Contact:** roads@mcmc-demo.gov
- **Jurisdiction:** All public roads, sidewalks, potholes, road damage
- **Issue types:** pothole, road_damage, sidewalk, traffic_sign

## Sanitation & Waste Management Department

- **Contact:** sanitation@mcmc-demo.gov
- **Jurisdiction:** Garbage collection, illegal dumping, street cleaning, public bins
- **Issue types:** garbage, illegal_dumping, overflowing_bin, street_cleaning

## Electrical & Street Lighting Department

- **Contact:** electrical@mcmc-demo.gov
- **Jurisdiction:** Streetlights, public lighting, electrical hazards on public property
- **Issue types:** streetlight, broken_light, electrical_hazard

## Water Supply Department

- **Contact:** water@mcmc-demo.gov
- **Jurisdiction:** Water leaks, burst pipes, low pressure, water quality on public mains
- **Issue types:** water_leak, burst_pipe, water_quality

## Sewerage & Drainage Department

- **Contact:** sewerage@mcmc-demo.gov
- **Jurisdiction:** Blocked drains, sewage overflow, manhole issues, flooding from drains
- **Issue types:** sewage, blocked_drain, manhole, flooding

## Routing rules

1. Match the citizen's description and photo context to the closest issue type.
2. If multiple departments could apply, prefer the most specific match (e.g. water leak → Water, not Roads).
3. Default unknown issues to Roads & Infrastructure with issue_type `other`.
4. All complaint emails should reference MCMC and request acknowledgment within 5 business days.
