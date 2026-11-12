"""Fetch the current air quality for Monterrey and rewrite one block of README.md.

Data: Open-Meteo air quality API (CAMS model output, no key needed).
It's a modeled estimate for the grid cell, not a reading from a monitoring station.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

LAT, LON = 25.6866, -100.3161  # downtown Monterrey
URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
    f"?latitude={LAT}&longitude={LON}"
    "&current=us_aqi,pm2_5,pm10&timezone=America%2FMonterrey"
)
README = Path(__file__).resolve().parent.parent / "README.md"
BLOCK = re.compile(r"(<!-- AIR:START -->\n).*?(\n<!-- AIR:END -->)", re.S)

# upper bound of each US AQI band
BANDS = [
    (50, "good"),
    (100, "moderate"),
    (150, "unhealthy for sensitive groups"),
    (200, "unhealthy"),
    (300, "very unhealthy"),
]


def band(aqi: float) -> str:
    for limit, label in BANDS:
        if aqi <= limit:
            return label
    return "hazardous"


def fetch() -> dict:
    with urllib.request.urlopen(URL, timeout=30) as resp:
        return json.load(resp)["current"]


def render(current: dict) -> str:
    aqi = round(current["us_aqi"])
    when = datetime.fromisoformat(current["time"])
    stamp = f"{when.day} {when:%b %Y, %H:%M}"
    return (
        f"> **US AQI {aqi}, {band(aqi)}.** "
        f"PM2.5 at {current['pm2_5']:.1f} µg/m³ and PM10 at {current['pm10']:.1f} µg/m³, "
        f"as of {stamp} local time. "
        "Modeled estimate from [Open-Meteo](https://open-meteo.com/en/docs/air-quality-api), "
        "not a station reading."
    )


def main() -> int:
    line = render(fetch())
    text = README.read_text(encoding="utf-8")
    new_text, n = BLOCK.subn(lambda m: m.group(1) + line + m.group(2), text)
    if n != 1:
        print("Could not find the AIR:START / AIR:END markers in README.md", file=sys.stderr)
        return 1
    README.write_text(new_text, encoding="utf-8")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
