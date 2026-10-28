import sqlite3
from datetime import datetime

DB = "siteguard.db"


def run_safety_agent():
    print("\n" + "=" * 45)
    print("       SITEGUARD AI SAFETY AGENT")
    print("=" * 45)

    with sqlite3.connect(DB) as con:
        hazards = con.execute("""
            SELECT id, title, location, description,
                   severity, status, reported_at,
                   acknowledged_by
            FROM hazards
            ORDER BY id DESC
        """).fetchall()

    if not hazards:
        print("\nNo hazards found. Site is awaiting reports.")
        return

    critical_count = 0
    pending_count = 0
    open_count = 0

    print("\nAGENT ANALYSIS REPORT")
    print("-" * 45)

    for h in hazards:
        hid, title, location, description, severity, status, reported, acknowledged = h

        if status != "Resolved":
            open_count += 1

        if status != "Resolved" and not acknowledged:
            pending_count += 1

        print(f"\nHazard ID: {hid}")
        print(f"Title: {title}")
        print(f"Location: {location}")
        print(f"Severity: {severity}")
        print(f"Status: {status}")

        if status == "Resolved":
            print("Agent Decision: Hazard marked resolved.")

        elif severity in ("Critical", "High"):
            critical_count += 1
            print("Agent Decision: URGENT ATTENTION REQUIRED!")
            print("Recommendation: Keep people away if safe,")
            print("notify the site supervisor immediately,")
            print("and follow official safety procedures.")

        else:
            print("Agent Decision: Review and follow site")
            print("safety procedures.")

        if status != "Resolved" and not acknowledged:
            print("Alert: Supervisor acknowledgement pending.")

    print("\n" + "=" * 45)
    print("           SAFETY SUMMARY")
    print("=" * 45)
    print(f"Total hazards: {len(hazards)}")
    print(f"Open hazards: {open_count}")
    print(f"Pending acknowledgement: {pending_count}")
    print(f"High/Critical open hazards: {critical_count}")
    print("\nAgent analysis completed.")
    print("Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))


if __name__ == "__main__":
    run_safety_agent()