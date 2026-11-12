"""Fetch the latest air quality reading for Monterrey and rewrite one block of README.md.

Data: OpenAQ (station measurements). Needs API_KEY in the environment or in a .env file.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openaq import OpenAQ

SENSOR_ID = 14189968  # the sensor used in measurements.py
CENTER = (25.68435, -100.31721)  # downtown Monterrey, same search as first_request.py
RADIUS_M = 12000

README = Path(__file__).resolve().parent.parent / "README.md"
BLOCK = re.compile(r"(<!-- AIR:START -->\n).*?(\n<!-- AIR:END -->)", re.S)


def station_name(client: OpenAQ) -> str | None:
    """Name of the location that hosts SENSOR_ID, if it's within the search radius."""
    response = client.locations.list(coordinates=CENTER, radius=RADIUS_M, limit=100)
    for location in response.results:
        if any(sensor.id == SENSOR_ID for sensor in location.sensors):
            return location.name
    return None


def render(sensor, station: str | None) -> str:
    when = datetime.fromisoformat(sensor.latest.datetime.local)
    label = sensor.parameter.display_name or sensor.parameter.name
    where = f" at the {station} station" if station else ""
    return (
        f"> **{label} at {sensor.latest.value:.1f} {sensor.parameter.units}**{where}, "
        f"measured {when.day} {when:%b %Y, %H:%M} local time. "
        "Station data via [OpenAQ](https://openaq.org)."
    )


def main() -> int:
    load_dotenv()
    client = OpenAQ(api_key=os.getenv("API_KEY"))
    try:
        sensor = client.sensors.get(SENSOR_ID).results[0]
        if sensor.latest is None:
            print(f"Sensor {SENSOR_ID} has no latest reading; README left as is.", file=sys.stderr)
            return 1
        line = render(sensor, station_name(client))
    finally:
        client.close()

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
