#!/usr/bin/env python3
"""
Downloads simplified Florida state and county GeoJSON boundaries,
and generates placeholder demographic and voter data.
"""

import json
import urllib.request
from pathlib import Path
import random

PUBLIC_DIR = Path("public")

# URLs for Florida boundaries (generalized to keep file size small)
# State outline
STATE_URL = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
# Counties
COUNTIES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

def get_json(url):
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    PUBLIC_DIR.mkdir(exist_ok=True)
    
    states_data = get_json(STATE_URL)
    fl_feature = None
    for f in states_data['features']:
        if f['properties'].get('name') == 'Florida':
            fl_feature = f
            break
            
    if fl_feature:
        fl_geojson = {"type": "FeatureCollection", "features": [fl_feature]}
        with open(PUBLIC_DIR / "florida.geojson", "w") as f:
            json.dump(fl_geojson, f)
        print("Wrote florida.geojson")
    else:
        print("Florida not found in states data!")

    counties_data = get_json(COUNTIES_URL)
    fl_counties = []
    # Florida state FIPS is 12
    for f in counties_data['features']:
        if f['id'].startswith('12'):
            fl_counties.append(f)
            
    # Generate placeholder data for Demo and Voter layers based on counties
    # (Since we don't have tracts easily available, we'll use counties for demo too for the prototype)
    demo_features = []
    voter_features = []
    
    for c in fl_counties:
        county_name = c['properties'].get('NAME', 'Unknown')
        
        # Demographic Placeholder
        demo_f = {
            "type": "Feature",
            "geometry": c["geometry"],
            "properties": {
                "name": county_name,
                "pct_hispanic": round(random.uniform(5, 65), 1),
                "pct_spanish": round(random.uniform(2, 60), 1),
                "pct_young": round(random.uniform(10, 35), 1),
                "total_pop": random.randint(10000, 1500000)
            }
        }
        demo_features.append(demo_f)
        
        # Voter Placeholder
        total_reg = random.randint(5000, 800000)
        pct_dem = round(random.uniform(20, 60), 1)
        pct_rep = round(random.uniform(30, 70), 1)
        
        # Normalize to leave room for NPA
        total_partisan = pct_dem + pct_rep
        if total_partisan > 90:
            pct_dem = pct_dem * (90 / total_partisan)
            pct_rep = pct_rep * (90 / total_partisan)
            
        pct_unaff = round(100 - pct_dem - pct_rep, 1)
        
        voter_f = {
            "type": "Feature",
            "geometry": c["geometry"],
            "properties": {
                "county": county_name,
                "pct_dem": round(pct_dem, 1),
                "pct_rep": round(pct_rep, 1),
                "pct_unaffiliated": pct_unaff,
                "total_reg": total_reg
            }
        }
        voter_features.append(voter_f)

    with open(PUBLIC_DIR / "florida-demo.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": demo_features}, f)
    print("Wrote florida-demo.geojson (placeholder)")

    with open(PUBLIC_DIR / "florida-voters.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": voter_features}, f)
    print("Wrote florida-voters.geojson (placeholder)")

if __name__ == "__main__":
    main()
