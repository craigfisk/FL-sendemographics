#!/usr/bin/env python3
"""
Build public/florida-voters.geojson — no external dependencies required.

Uses a base counties GeoJSON and joins placeholder voter registration data,
then writes the output GeoJSON.

Usage:
    python3 scripts/build_fl_voter_layer.py

Updating voter registration data:
    1. Go to the Florida Division of Elections website.
    2. Download the most recent voter registration report by county.
    3. Update VOTER_REG below with (dem_registered, rep_registered, unaffiliated_registered, total_registered).
    4. Re-run this script to regenerate public/florida-voters.geojson.
"""

import json, sys
from pathlib import Path

# Assume scaffold_fl_data.py has already pulled a base counties file into florida-demo.geojson 
# We'll use the geometry from that file as our base for counties.
BASE_PATH = Path("public/florida-demo.geojson")
OUTPUT_PATH   = Path("public/florida-voters.geojson")

# ---------------------------------------------------------------------------
# Voter registration data (PLACEHOLDER)
# Key:   county_name_upper
# Value: (dem_registered, rep_registered, unaffiliated_registered, total_registered)
# ---------------------------------------------------------------------------
VOTER_REG: dict[str, tuple[int, int, int, int]] = {
    "MIAMI-DADE": (500000, 400000, 300000, 1200000),
    "BROWARD":    (600000, 250000, 300000, 1150000),
    "PALM BEACH": (380000, 280000, 250000, 910000),
    "HILLSBOROUGH":(330000, 290000, 240000, 860000),
    "ORANGE":     (340000, 210000, 230000, 780000),
    "PINELLAS":   (230000, 240000, 190000, 660000),
    "DUVAL":      (260000, 220000, 150000, 630000),
    # Add other Florida counties here...
}

def main() -> None:
    if not BASE_PATH.exists():
        sys.exit(f"Base file not found: {BASE_PATH}. Run scaffold_fl_data.py first.")

    raw = json.loads(BASE_PATH.read_text())
    features = raw.get("features", [])

    output_features = []
    unmatched = []

    for feat in features:
        geom = feat.get("geometry")
        props = feat.get("properties", {})
        
        # In our placeholder, the county name is stored in "name"
        raw_name = str(props.get("name", "")).strip().upper()

        pair = VOTER_REG.get(raw_name)
        if pair is None:
            unmatched.append(raw_name)
            # Use the random placeholder data already in the file if it exists, or None
            pct_dem = props.get("pct_dem")
            pct_rep = props.get("pct_rep")
            pct_unaff = props.get("pct_unaffiliated")
        else:
            dem, rep, unaff, total = pair
            pct_dem   = round(dem   / total * 100, 1) if total > 0 else None
            pct_rep   = round(rep   / total * 100, 1) if total > 0 else None
            pct_unaff = round(unaff / total * 100, 1) if total > 0 else None

        output_features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "county":          props.get("name", ""),
                "pct_dem":         pct_dem,
                "pct_unaffiliated": pct_unaff,
                "pct_rep":         pct_rep,
            },
        })

    out_fc = {"type": "FeatureCollection", "features": output_features}
    OUTPUT_PATH.write_text(json.dumps(out_fc))

    matched = len(output_features) - len(unmatched)
    print(f"\nFlorida Counties: {len(output_features)}")
    print(f"Matched to VOTER_REG: {matched}/{len(output_features)}")

    if unmatched:
        print("\nUnmatched — add these keys to VOTER_REG (with actual dem/rep/unaff/total counts):")
        # Print just a few as an example
        for key in sorted(set(unmatched))[:10]:
            print(f'    "{key}": (dem, rep, unaff, total),')
        if len(unmatched) > 10:
            print(f"    ... and {len(unmatched)-10} more.")

    print(f"\nOutput written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
