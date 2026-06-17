"""
Healing Reporter — generates reports showing what was healed and how.

Supports multiple output formats:
- Console (pretty-printed with colors)
- JSON (machine-readable)
- HTML (shareable reports)
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from self_healing.healer import Healer, HealingConfig

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports",
)


class HealingReporter:
    """Generates and outputs healing reports in various formats."""

    def __init__(self, healer: Healer, config: HealingConfig):
        self.healer = healer
        self.config = config

    def get_summary(self) -> dict:
        """Get healing statistics as a dictionary."""
        total = self.healer.total_lookups
        primary = self.healer.primary_successes
        healed = self.healer.healed_count
        failed = self.healer.failed_count
        failures = healed + failed
        healing_rate = (healed / failures * 100) if failures > 0 else 0

        return {
            "total_lookups": total,
            "primary_successes": primary,
            "healed": healed,
            "failed": failed,
            "healing_rate": round(healing_rate, 1),
            "events": [
                {
                    "original": f"{e.original_by}='{e.original_value}'",
                    "healed_with": (
                        f"{e.healed_by}='{e.healed_value}'" if e.success else None
                    ),
                    "success": e.success,
                    "confidence": round(e.confidence, 2),
                    "candidates_tried": e.candidates_tried,
                    "page_url": e.page_url,
                }
                for e in self.healer.healing_events
            ],
        }

    def print_console_report(self) -> None:
        """Print a formatted report to the console."""
        summary = self.get_summary()

        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║              SELF-HEALING REPORT                        ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║ Total find_element calls:  {summary['total_lookups']:<28} ║")
        print(f"║ Successful (primary):      {summary['primary_successes']:<28} ║")
        print(f"║ Healed (fallback):         {summary['healed']:<28} ║")
        print(f"║ Failed (unrecoverable):    {summary['failed']:<28} ║")
        print(
            f"║ Healing rate:              "
            f"{summary['healing_rate']}% of failures recovered"
            f"{' ' * (17 - len(str(summary['healing_rate'])))}║"
        )
        print("╠══════════════════════════════════════════════════════════╣")

        if summary["events"]:
            print("║                                                          ║")
            print("║ HEALING EVENTS:                                          ║")

            for event in summary["events"]:
                print(
                    "║ ┌──────────────────────────────────────────────────────┐ ║"
                )

                status = "✅" if event["success"] else "❌"
                print(f"║ │ {status} Original: {event['original']:<42} │ ║")

                if event["success"]:
                    print(
                        f"║ │   Healed via: {event['healed_with']:<38} │ ║"
                    )
                    print(
                        f"║ │   Confidence: {event['confidence']:<38} │ ║"
                    )
                    print(
                        f"║ │   💡 Update your locator to: "
                        f"{event['healed_with']:<22} │ ║"
                    )
                else:
                    print(
                        f"║ │   ⚠️  Could not heal. Tried "
                        f"{event['candidates_tried']} alternatives."
                        f"{' ' * 14}│ ║"
                    )

                print(
                    "║ └──────────────────────────────────────────────────────┘ ║"
                )

        print("╚══════════════════════════════════════════════════════════╝")
        print()

    def save_report(self, path: Optional[str] = None) -> str:
        """Save the report to a file in the configured format."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.config.report_format == "json":
            return self._save_json(path, timestamp)
        elif self.config.report_format == "html":
            return self._save_html(path, timestamp)
        else:
            return self._save_json(path, timestamp)

    def _save_json(self, path: Optional[str], timestamp: str) -> str:
        """Save report as JSON."""
        if not path:
            path = os.path.join(REPORTS_DIR, f"healing_report_{timestamp}.json")

        summary = self.get_summary()
        summary["generated_at"] = timestamp

        with open(path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Report saved to: {path}")
        return path

    def _save_html(self, path: Optional[str], timestamp: str) -> str:
        """Save report as HTML."""
        if not path:
            path = os.path.join(REPORTS_DIR, f"healing_report_{timestamp}.html")

        summary = self.get_summary()
        html = self._generate_html(summary, timestamp)

        with open(path, "w") as f:
            f.write(html)

        logger.info(f"Report saved to: {path}")
        return path

    def _generate_html(self, summary: dict, timestamp: str) -> str:
        """Generate an HTML report."""
        events_html = ""
        for event in summary["events"]:
            status_class = "success" if event["success"] else "failure"
            status_icon = "✅" if event["success"] else "❌"
            healed_info = ""
            if event["success"]:
                healed_info = f"""
                <p class="healed">Healed via: <code>{event['healed_with']}</code></p>
                <p class="confidence">Confidence: {event['confidence']}</p>
                <p class="suggestion">💡 Update your locator to: <code>{event['healed_with']}</code></p>
                """
            else:
                healed_info = f"""
                <p class="failed">Could not heal. Tried {event['candidates_tried']} alternatives.</p>
                """

            events_html += f"""
            <div class="event {status_class}">
                <h3>{status_icon} {event['original']}</h3>
                {healed_info}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Healing Report — {timestamp}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #00d4aa; border-bottom: 2px solid #00d4aa; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin: 24px 0; }}
        .stat {{ background: #16213e; padding: 16px; border-radius: 8px; text-align: center; }}
        .stat .number {{ font-size: 2em; font-weight: bold; color: #00d4aa; }}
        .stat .label {{ color: #aaa; margin-top: 4px; }}
        .event {{ background: #16213e; padding: 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #666; }}
        .event.success {{ border-left-color: #00d4aa; }}
        .event.failure {{ border-left-color: #ff6b6b; }}
        .event h3 {{ margin: 0 0 8px 0; }}
        code {{ background: #0a0a1a; padding: 2px 6px; border-radius: 4px; color: #ffd700; }}
        .suggestion {{ color: #00d4aa; }}
        .failed {{ color: #ff6b6b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🩺 Self-Healing Report</h1>
        <p>Generated: {timestamp}</p>

        <div class="stats">
            <div class="stat">
                <div class="number">{summary['total_lookups']}</div>
                <div class="label">Total Lookups</div>
            </div>
            <div class="stat">
                <div class="number">{summary['primary_successes']}</div>
                <div class="label">Primary Success</div>
            </div>
            <div class="stat">
                <div class="number">{summary['healed']}</div>
                <div class="label">Healed</div>
            </div>
            <div class="stat">
                <div class="number">{summary['failed']}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat">
                <div class="number">{summary['healing_rate']}%</div>
                <div class="label">Healing Rate</div>
            </div>
        </div>

        <h2>Healing Events</h2>
        {events_html if events_html else '<p>No healing events occurred.</p>'}
    </div>
</body>
</html>"""
