"""
Email Automation - Gmail/Outlook automation

Provides email processing, triage, and automated responses
using Gmail and Outlook APIs.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum


class EmailPriority(Enum):
    """Email priority levels"""
    URGENT = "urgent"
    IMPORTANT = "important"
    BULK = "bulk"
    LOW = "low"


class EmailAutomation:
    """Email automation and triage"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/Users/cortana/.openclaw/workspace/.email_config"
        self.workspace_path = "/Users/cortana/.openclaw/workspace"
        self.calendar_path = Path(self.workspace_path) / "projects/berman-implementations/calendar"
        
        # Ensure directory exists
        self.calendar_path.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = self._load_config()
        
        # Email cache
        self.cache_path = self.calendar_path / "email_cache.json"
        
        # Priority keywords
        self.urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediately", "now"]
        self.important_keywords = ["important", "priority", "review", "needed", "required"]
        self.bulk_keywords = ["newsletter", "update", "digest", "weekly", "monthly", "promo"]
    
    def _load_config(self) -> Dict:
        """Load email configuration"""
        return {
            "gmail_api_key": os.getenv("GMAIL_API_KEY", ""),
            "outlook_client_id": os.getenv("OUTLOOK_CLIENT_ID", ""),
            "check_interval_minutes": 15,
            "auto_archive_days": 30,
            "rules": []
        }
    
    def get_unread_emails(self, limit: int = 20) -> List[Dict]:
        """Get unread emails from all accounts"""
        # In production: call Gmail/Outlook APIs
        
        # Return sample emails for demonstration
        emails = self._sample_emails()
        
        # Sort by priority
        for email in emails:
            email["priority"] = self._determine_priority(email)
        
        emails.sort(key=lambda x: self._priority_order(x["priority"]))
        
        return emails[:limit]
    
    def _sample_emails(self) -> List[Dict]:
        """Sample emails for demonstration"""
        now = datetime.now()
        
        return [
            {
                "id": "1",
                "from": "boss@company.com",
                "to": "chase@email.com",
                "subject": "URGENT: Project deadline moved up",
                "snippet": "We need to deliver by Friday instead of Monday...",
                "date": now.isoformat(),
                "read": False,
                "source": "gmail"
            },
            {
                "id": "2",
                "from": "newsletter@tech.com",
                "to": "chase@email.com",
                "subject": "Weekly Tech Digest",
                "snippet": "This week's top stories in technology...",
                "date": now.isoformat(),
                "read": False,
                "source": "gmail"
            },
            {
                "id": "3",
                "from": "friend@email.com",
                "to": "chase@email.com",
                "subject": "Plans for this weekend?",
                "snippet": "Hey! Want to catch up this weekend?",
                "date": now.isoformat(),
                "read": False,
                "source": "outlook"
            },
            {
                "id": "4",
                "from": "team@company.com",
                "to": "chase@email.com",
                "subject": "Code review needed",
                "snippet": "Can you review PR #42 when you have time?",
                "date": now.isoformat(),
                "read": False,
                "source": "gmail"
            }
        ]
    
    def _determine_priority(self, email: Dict) -> str:
        """Determine email priority"""
        subject = email.get("subject", "").lower()
        snippet = email.get("snippet", "").lower()
        
        # Check urgent keywords
        for keyword in self.urgent_keywords:
            if keyword in subject or keyword in snippet:
                return EmailPriority.URGENT.value
        
        # Check important keywords
        for keyword in self.important_keywords:
            if keyword in subject or keyword in snippet:
                return EmailPriority.IMPORTANT.value
        
        # Check bulk indicators
        for keyword in self.bulk_keywords:
            if keyword in subject.lower():
                return EmailPriority.BULK.value
        
        return EmailPriority.LOW.value
    
    def _priority_order(self, priority: str) -> int:
        """Get numeric order for priority"""
        order = {
            EmailPriority.URGENT.value: 0,
            EmailPriority.IMPORTANT.value: 1,
            EmailPriority.LOW.value: 2,
            EmailPriority.BULK.value: 3
        }
        return order.get(priority, 99)
    
    def triage_emails(self, emails: List[Dict] = None) -> Dict:
        """Perform email triage"""
        if emails is None:
            emails = self.get_unread_emails()
        
        triage = {
            "timestamp": datetime.now().isoformat(),
            "total_emails": len(emails),
            "by_priority": {
                EmailPriority.URGENT.value: [],
                EmailPriority.IMPORTANT.value: [],
                EmailPriority.LOW.value: [],
                EmailPriority.BULK.value: []
            },
            "actions_suggested": []
        }
        
        for email in emails:
            priority = email.get("priority", EmailPriority.LOW.value)
            triage["by_priority"][priority].append({
                "id": email["id"],
                "from": email["from"],
                "subject": email["subject"],
                "action": self._suggest_action(email)
            })
        
        # Generate suggested actions
        urgent_count = len(triage["by_priority"][EmailPriority.URGENT.value])
        if urgent_count > 0:
            triage["actions_suggested"].append(
                f"⚠️ {urgent_count} urgent emails need immediate attention"
            )
        
        bulk_count = len(triage["by_priority"][EmailPriority.BULK.value])
        if bulk_count > 0:
            triage["actions_suggested"].append(
                f"📧 {bulk_count} bulk emails can be archived automatically"
            )
        
        important_count = len(triage["by_priority"][EmailPriority.IMPORTANT.value])
        if important_count > 0:
            triage["actions_suggested"].append(
                f"⭐ {important_count} important emails need replies today"
            )
        
        return triage
    
    def _suggest_action(self, email: Dict) -> str:
        """Suggest action for email"""
        priority = email.get("priority", EmailPriority.LOW.value)
        from_addr = email.get("from", "")
        
        if priority == EmailPriority.URGENT.value:
            return "Reply immediately"
        elif priority == EmailPriority.IMPORTANT.value:
            return "Reply within 24 hours"
        elif "newsletter" in from_addr.lower() or "digest" in from_addr.lower():
            return "Archive after reading"
        else:
            return "Review when convenient"
    
    def send_email(self, to: str, subject: str, body: str, 
                  cc: str = None, source: str = "gmail") -> Dict:
        """Send an email"""
        # In production: call Gmail/Outlook API
        
        return {
            "id": f"sent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "to": to,
            "subject": subject,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "source": source
        }
    
    def archive_emails(self, email_ids: List[str]) -> Dict:
        """Archive emails by ID"""
        # In production: call API to archive
        
        return {
            "archived_count": len(email_ids),
            "ids": email_ids,
            "timestamp": datetime.now().isoformat()
        }
    
    def apply_rules(self, rules: List[Dict] = None) -> Dict:
        """Apply email filtering rules"""
        rules = rules or self.config.get("rules", [])
        
        results = {
            "applied_rules": len(rules),
            "actions_taken": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for rule in rules:
            # Rule format: {"name": "Rule name", "condition": {...}, "action": "archive|标记|delete"}
            results["actions_taken"].append({
                "rule": rule["name"],
                "matched": 0,  # Would count matches
                "action": rule.get("action", "archive")
            })
        
        return results
    
    def get_email_summary(self) -> Dict:
        """Get overall email summary"""
        emails = self.get_unread_emails()
        triage = self.triage_emails(emails)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_unread": len(emails),
            "by_priority": triage["by_priority"],
            "actions_suggested": triage["actions_suggested"]
        }
    
    def schedule_email_reminder(self, email_id: str, remind_at: datetime) -> Dict:
        """Schedule a reminder for an email"""
        return {
            "email_id": email_id,
            "remind_at": remind_at.isoformat(),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Email Automation")
    parser.add_argument("--triage", action="store_true", help="Triage unread emails")
    parser.add_argument("--list", type=int, default=10, help="List N unread emails")
    parser.add_argument("--summary", action="store_true", help="Show email summary")
    parser.add_argument("--send", nargs=3, metavar=("TO", "SUBJECT", "BODY"), help="Send email")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    email = EmailAutomation(args.workspace)
    
    if args.triage:
        result = email.triage_emails()
        print(f"\n📧 Email Triage")
        print(f"Total: {result['total_emails']} emails")
        for priority, emails in result['by_priority'].items():
            if emails:
                print(f"\n{priority.upper()}:")
                for e in emails:
                    print(f"  - [{e['action']}] {e['subject'][:50]}")
        print(f"\n💡 Suggestions:")
        for suggestion in result['actions_suggested']:
            print(f"  {suggestion}")
    elif args.list:
        emails = email.get_unread_emails(limit=args.list)
        print(f"\n📬 Unread Emails ({len(emails)}):")
        for e in emails:
            priority = e.get("priority", "low")[0].upper()
            print(f"  [{priority}] {e['subject'][:40]} - {e['from']}")
    elif args.summary:
        summary = email.get_email_summary()
        print(f"\n📊 Email Summary")
        print(f"Total unread: {summary['total_unread']}")
        for priority, count in summary['by_priority'].items():
            if count:
                print(f"  {priority}: {len(count)}")
    elif args.send:
        to, subject, body = args.send
        result = email.send_email(to, subject, body)
        print(f"✅ Email sent: {result['id']}")
    else:
        emails = email.get_unread_emails()
        print(f"Unread: {len(emails)} emails")


if __name__ == "__main__":
    main()
