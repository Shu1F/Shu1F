import argparse
import json
import math
import subprocess
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path


def fetch_contributions(username):
    end = datetime.now(timezone.utc)
    start = (end - timedelta(days=30)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    result = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={query}",
            "-f", f"username={username}",
            "-f", f"from={start.isoformat()}",
            "-f", f"to={end.isoformat()}",
        ],
        check=True, capture_output=True, text=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    if payload.get("errors"):
        raise ValueError(f"GitHub API returned errors: {payload['errors']}")
    weeks = payload["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]["weeks"]
    days = sorted(
        (
            day for week in weeks for day in week["contributionDays"]
            if start.date().isoformat() <= day["date"] <= end.date().isoformat()
        ),
        key=lambda day: day["date"],
    )
    expected_dates = [
        (start + timedelta(days=offset)).date().isoformat() for offset in range(31)
    ]
    if [day["date"] for day in days] != expected_dates:
        raise ValueError("Expected 31 consecutive days of GitHub contributions")
    if any(
        type(day["contributionCount"]) is not int or day["contributionCount"] < 0
        for day in days
    ):
        raise ValueError("Invalid GitHub contribution count")
    return days


def render_graph(username, days):
    left, right, top, bottom = 65, 965, 90, 270
    counts = [day["contributionCount"] for day in days]
    tick = max(1, math.ceil(max(counts) / 4))
    ceiling = tick * 4
    coordinates = [
        (
            left + index * (right - left) / (len(days) - 1),
            bottom - count * (bottom - top) / ceiling,
        )
        for index, count in enumerate(counts)
    ]
    points = " ".join(
        f"{horizontal:.1f},{vertical:.1f}" for horizontal, vertical in coordinates
    )
    title = escape(f"{username}'s Contribution Graph")
    description = escape(
        f"{sum(counts)} contributions from {days[0]['date']} to {days[-1]['date']} (UTC)"
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 340" '
        'role="img" aria-labelledby="title description">',
        f'<title id="title">{title}</title>',
        f'<desc id="description">{description}</desc>',
        '<rect width="1000" height="340" rx="12" fill="#1a1b27"/>',
        '<g font-family="Arial, sans-serif" fill="#a9b1d6">',
        f'<text x="32" y="37" font-size="22" fill="#70a5fd">{title}</text>',
        f'<text x="32" y="62" font-size="13">{description}</text>',
    ]
    for index in range(5):
        vertical = bottom - index * (bottom - top) / 4
        parts.extend([
            f'<path d="M{left},{vertical} H{right}" stroke="#292e42"/>',
            f'<text x="52" y="{vertical + 4}" text-anchor="end" '
            f'font-size="12">{index * tick}</text>',
        ])
    parts.extend([
        f'<polygon points="{left},{bottom} {points} {right},{bottom}" '
        'fill="#7aa2f7" opacity="0.12"/>',
        f'<polyline points="{points}" fill="none" stroke="#7aa2f7" '
        'stroke-width="2.5" stroke-linejoin="round"/>',
    ])
    for day, (horizontal, vertical) in zip(days, coordinates):
        label = escape(f"{day['date']}: {day['contributionCount']} contributions")
        parts.append(
            f'<circle cx="{horizontal:.1f}" cy="{vertical:.1f}" r="3" '
            f'fill="#bb9af7"><title>{label}</title></circle>'
        )
    for index in range(0, len(days), 5):
        horizontal = coordinates[index][0]
        label = escape(days[index]["date"][5:])
        parts.append(
            f'<text x="{horizontal:.1f}" y="295" text-anchor="middle" '
            f'font-size="12">{label}</text>'
        )
    parts.extend([
        '<text x="500" y="324" text-anchor="middle" font-size="12">'
        'Daily GitHub contributions · UTC</text>',
        '</g>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="Shu1F")
    parser.add_argument("--output", type=Path, default=Path("assets/activity-graph.svg"))
    arguments = parser.parse_args()
    graph = render_graph(arguments.username, fetch_contributions(arguments.username))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(graph, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"GitHub API request failed: {error.stderr.strip()}") from error
