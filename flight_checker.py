"""
Air India ORD → BLR Daily Cheapest Fare Checker
Uses SerpAPI (Google Flights) to find cheapest Air India fares
across flexible dates and sends a formatted HTML email digest.
"""

import os
import smtplib
import requests
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Config ────────────────────────────────────────────────────────────────────
SERPAPI_KEY   = os.environ["SERPAPI_KEY"]
SMTP_USER     = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
TO_EMAIL      = os.environ["TO_EMAIL"]

ORIGIN        = "ORD"
DESTINATION   = "BLR"
AIRLINE_NAME  = "Air India"
CURRENCY      = "USD"
DATE_STEP     = 3     # probe every 3 days
DAYS_AHEAD    = 90
TOP_RESULTS   = 5

SERPAPI_URL   = "https://serpapi.com/search.json"


def search_flights(departure_date: str) -> list:
    params = {
        "engine": "google_flights",
        "departure_id": ORIGIN,
        "arrival_id": DESTINATION,
        "outbound_date": departure_date,
        "type": "2",
        "currency": CURRENCY,
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(SERPAPI_URL, params=params, timeout=20)
    if resp.status_code != 200:
        print(f"[WARN] {resp.status_code} for {departure_date}")
        return []
    data = resp.json()
    return data.get("best_flights", []) + data.get("other_flights", [])


def extract_air_india(flights: list, departure_date: str):
    best = None
    for flight in flights:
        legs = flight.get("flights", [])
        if not legs:
            continue
        airlines = [leg.get("airline", "") for leg in legs]
        if not all(AIRLINE_NAME in a for a in airlines):
            continue
        price = flight.get("price")
        if not price:
            continue
        mins = flight.get("total_duration", 0)
        dur  = f"{mins//60}h {mins%60}m" if mins else "N/A"
        stops = len(legs) - 1
        via   = [leg["arrival_airport"]["id"] for leg in legs[:-1]]
        r = {
            "date": departure_date,
            "price": float(price),
            "currency": CURRENCY,
            "duration": dur,
            "stops": stops,
            "via": via,
            "dep_time": legs[0]["departure_airport"].get("time", ""),
            "arr_time": legs[-1]["arrival_airport"].get("time", ""),
        }
        if best is None or r["price"] < best["price"]:
            best = r
    return best


def find_fares() -> list:
    today   = datetime.today()
    cursor  = today + timedelta(days=7)
    results = []
    print(f"Scanning {DAYS_AHEAD // DATE_STEP} dates for Air India ORD→BLR...\n")
    while cursor <= today + timedelta(days=DAYS_AHEAD):
        d = cursor.strftime("%Y-%m-%d")
        print(f"  {d}...", end=" ", flush=True)
        fare = extract_air_india(search_flights(d), d)
        if fare:
            print(f"✓ ${fare['price']:.2f} ({fare['duration']})")
            results.append(fare)
        else:
            print("✗ No AI")
        cursor += timedelta(days=DATE_STEP)
    results.sort(key=lambda x: x["price"])
    return results[:TOP_RESULTS]


def build_html(results: list) -> str:
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    if not results:
        body = "<p style='color:#666'>No Air India flights found today. Try again tomorrow.</p>"
    else:
        rows = ""
        for i, r in enumerate(results):
            bg    = "#eaf6ff" if i == 0 else ("white" if i % 2 == 0 else "#fafafa")
            badge = "&nbsp;🏆 Best Deal" if i == 0 else ""
            via   = "Non-stop" if r["stops"] == 0 else f"{r['stops']} stop(s) via {', '.join(r['via'])}"
            rows += f"""<tr style="background:{bg}">
              <td style="padding:12px 10px;border-bottom:1px solid #eee"><strong>{r['date']}</strong></td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee">{r['dep_time']}{badge}</td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee">
                <strong style="font-size:17px;color:#1a6eb5">${r['price']:.2f}</strong>
                <span style="color:#aaa;font-size:12px"> USD</span></td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee">{r['duration']}</td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee">{r['arr_time']}</td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee;color:#555;font-size:13px">{via}</td>
            </tr>"""
        body = f"""<p style="margin:0 0 16px">Top <strong>{len(results)} cheapest Air India fares</strong> in the next 90 days:</p>
        <table width="100%" cellspacing="0" style="border-collapse:collapse;font-size:14px">
          <thead><tr style="background:#f0f0f0;color:#333;font-size:13px">
            <th style="padding:10px;text-align:left">Date</th>
            <th style="padding:10px;text-align:left">Departs ORD</th>
            <th style="padding:10px;text-align:left">Price</th>
            <th style="padding:10px;text-align:left">Duration</th>
            <th style="padding:10px;text-align:left">Arrives BLR</th>
            <th style="padding:10px;text-align:left">Stops</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>"""

    headline = f"Best: ${results[0]['price']:.0f} on {results[0]['date']}" if results else "No fares today"
    return f"""<html><body style="font-family:Arial,sans-serif;max-width:720px;margin:30px auto;color:#222">
      <div style="background:#E8413C;color:white;padding:24px 28px;border-radius:10px 10px 0 0">
        <div style="font-size:24px;font-weight:bold">✈️ Air India · ORD → BLR</div>
        <div style="font-size:14px;margin-top:4px;opacity:.9">Daily Fare Alert · {today_str}</div>
        <div style="margin-top:10px;background:rgba(255,255,255,.15);display:inline-block;
                    padding:6px 14px;border-radius:20px;font-weight:bold">{headline}</div>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:24px 28px;border-radius:0 0 10px 10px">
        {body}
        <hr style="margin:20px 0;border:none;border-top:1px solid #eee">
        <p style="font-size:12px;color:#999;margin:0">
          Powered by SerpAPI · Google Flights · Economy · 1 adult ·
          Book at <a href="https://www.airindia.com" style="color:#E8413C">airindia.com</a>.
          Fares are indicative and subject to change.
        </p>
      </div>
    </body></html>"""


def send_email(results: list) -> None:
    subject = (
        f"✈️ Air India ORD→BLR | Best: ${results[0]['price']:.0f} on {results[0]['date']}"
        if results else "✈️ Air India ORD→BLR | No fares found today"
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(build_html(results), "html"))
    print(f"\nSending to {TO_EMAIL}...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(SMTP_USER, TO_EMAIL, msg.as_string())
        print("✓ Email sent.")
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email: {e}") from e


if __name__ == "__main__":
    print(f"=== Air India ORD→BLR [{datetime.now().strftime('%Y-%m-%d %H:%M UTC')}] ===\n")
    try:
        fares = find_fares()
        print(f"\n{len(fares)} Air India fare(s) found.")
        send_email(fares)
        print("=== Done ✓ ===")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
