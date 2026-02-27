"""
Get ALL emails from Gmail and identify which ones need action.

This script:
1. Scrolls through entire Gmail inbox using the working scroll method
2. Extracts ALL emails (sender, subject, date, snippet)
3. Analyzes emails to find ones that need action
4. Creates a comprehensive summary
"""

from browser_agent.browser import Browser
import time
import json

def get_all_emails_and_analyze():
    print("=== Getting ALL Gmail Emails and Analyzing ===\n")

    web = Browser(use_chrome_profile=True)
    web.open_browser(headless=False)
    web.go_to("https://gmail.com")
    time.sleep(3)

    print("📧 Extracting ALL emails from inbox...")
    print("   This will scroll through all 351 emails and collect data\n")

    # Use the method we created to extract all emails
    result = web.scroll_gmail_and_extract_all_emails(max_scrolls=100)

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        web.close()
        return

    print(f"\n✅ Successfully extracted {result['total_unique_emails']} unique emails!")
    print(f"   Completed in {result['iterations']} scroll iterations")
    print(f"   Found {len(result['contacts'])} unique contacts")

    # Save all emails to file
    with open('all_emails.json', 'w') as f:
        json.dump(result['emails'], f, indent=2)
    print(f"\n💾 Saved all emails to: all_emails.json")

    # Analyze emails to find ones that need action
    print("\n\n🔍 Analyzing emails to find ones that need action...\n")

    action_keywords = [
        'action needed', 'action required', 'please review', 'please respond',
        'urgent', 'important', 'deadline', 'expiring', 'expires', 'reminder',
        'complete your', 'finish', 'required', 'asap', 'approval needed',
        'waiting for', 'pending', 'needs your', 'confirm', 'verify',
        'respond by', 'due date', 'overdue', 'follow up'
    ]

    emails_need_action = []
    for email in result['emails']:
        subject_lower = email['subject'].lower()
        snippet_lower = email['snippet'].lower()

        # Check if any action keyword appears in subject or snippet
        for keyword in action_keywords:
            if keyword in subject_lower or keyword in snippet_lower:
                emails_need_action.append({
                    'sender': email['sender'],
                    'subject': email['subject'],
                    'date': email['date'],
                    'reason': keyword,
                    'snippet': email['snippet'][:150]
                })
                break  # Only add once per email

    print(f"📋 Found {len(emails_need_action)} emails that may need action:\n")

    # Display emails that need action
    for i, email in enumerate(emails_need_action[:20], 1):  # Show first 20
        print(f"{i}. FROM: {email['sender']}")
        print(f"   SUBJECT: {email['subject']}")
        print(f"   DATE: {email['date']}")
        print(f"   REASON: Contains '{email['reason']}'")
        print(f"   PREVIEW: {email['snippet']}")
        print()

    if len(emails_need_action) > 20:
        print(f"... and {len(emails_need_action) - 20} more emails that need action\n")

    # Save action-needed emails to file
    with open('emails_need_action.json', 'w') as f:
        json.dump(emails_need_action, f, indent=2)
    print(f"💾 Saved action-needed emails to: emails_need_action.json")

    # Create summary statistics
    print("\n\n📊 EMAIL SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total unique emails: {result['total_unique_emails']}")
    print(f"Total unique contacts: {len(result['contacts'])}")
    print(f"Emails needing action: {len(emails_need_action)}")
    print(f"Scroll iterations: {result['iterations']}")

    # Count emails by sender (top 10)
    sender_counts = {}
    for email in result['emails']:
        sender = email['sender']
        sender_counts[sender] = sender_counts.get(sender, 0) + 1

    top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    print("\n📨 TOP 10 MOST FREQUENT SENDERS:")
    for i, (sender, count) in enumerate(top_senders, 1):
        print(f"   {i}. {sender}: {count} emails")

    # Save contacts to file
    with open('all_contacts.json', 'w') as f:
        json.dump(result['contacts'], f, indent=2)
    print(f"\n💾 Saved all contacts to: all_contacts.json")

    print("\n\n✅ Analysis complete!")
    print("\nFiles created:")
    print("  1. all_emails.json - All extracted emails")
    print("  2. emails_need_action.json - Emails that need action")
    print("  3. all_contacts.json - All unique contacts")

    web.close()

if __name__ == "__main__":
    get_all_emails_and_analyze()
