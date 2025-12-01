"""
Daily CRM Routine

Orchestrates daily workflow:
1. Recalculate priority scores
2. Sync email tracking for top contacts
3. Generate daily contact report

Run manually: python daily_crm_routine.py
Add to crontab: 0 8 * * * cd /path/to/signup-enrichment && source venv/bin/activate && python daily_crm_routine.py >> logs/daily_routine.log 2>&1
"""

import os
import subprocess
from datetime import datetime

# Load env
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")


def run_command(description, command, timeout=300):
    """
    Run a shell command and report results

    Args:
        description: Human-readable description
        command: Shell command to run
        timeout: Command timeout in seconds (default: 5 minutes)

    Returns:
        Boolean indicating success
    """
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"\n✓ {description} completed successfully")
            return True
        else:
            print(f"\n✗ {description} failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n✗ {description} timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"\n✗ {description} failed with error: {e}")
        return False


def main():
    start_time = datetime.now()

    print("\n" + "#" * 60)
    print("#" + " " * 58 + "#")
    print(f"#  Daily CRM Routine - {start_time.strftime('%Y-%m-%d %H:%M:%S')}  #")
    print("#" + " " * 58 + "#")
    print("#" * 60)

    results = []

    # Step 1: Calculate priority scores
    success = run_command(
        "Calculate Priority Scores",
        "python calculate_priority.py",
        timeout=120
    )
    results.append(("Priority Scores", success))

    # Step 2: Sync email tracking
    success = run_command(
        "Sync Email Tracking (Top 50)",
        "python sync_email_tracking.py --limit 50",
        timeout=600  # 10 minutes for 50 contacts
    )
    results.append(("Email Tracking", success))

    # Step 3: Generate daily report
    success = run_command(
        "Generate Daily Contact Report",
        "python get_daily_contacts.py",
        timeout=120
    )
    results.append(("Daily Report", success))

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "#" * 60)
    print("#" + " " * 58 + "#")
    print("#  DAILY ROUTINE SUMMARY" + " " * 35 + "#")
    print("#" + " " * 58 + "#")
    print("#" * 60)

    for step_name, step_success in results:
        status_icon = "✓" if step_success else "✗"
        status_text = "SUCCESS" if step_success else "FAILED"
        print(f"  {status_icon} {step_name}: {status_text}")

    print()
    print(f"  Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {int(duration // 60)}m {int(duration % 60)}s")

    all_success = all(success for _, success in results)
    if all_success:
        print("\n  ✓✓✓ All steps completed successfully! ✓✓✓")
    else:
        print("\n  ⚠⚠⚠ Some steps failed! Check logs above. ⚠⚠⚠")

    print("\n" + "#" * 60)

    return 0 if all_success else 1


if __name__ == '__main__':
    exit(main())
