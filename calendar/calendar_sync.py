"""
Calendar Sync - Google Calendar API integration

Provides calendar synchronization and event management
using the Google Calendar API.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class CalendarSync:
    """Google Calendar synchronization"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/Users/cortana/.openclaw/workspace/.calendar_config"
        self.workspace_path = "/Users/cortana/.openclaw/workspace"
        self.calendar_path = Path(self.workspace_path) / "projects/berman-implementations/calendar"
        
        # Ensure directory exists
        self.calendar_path.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = self._load_config()
        
        # Calendar events cache
        self.events_cache_path = self.calendar_path / "events_cache.json"
    
    def _load_config(self) -> Dict:
        """Load calendar configuration"""
        if not Path(self.config_path).exists():
            return {
                "google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "default_calendar": "primary",
                "sync_interval_minutes": 15
            }
        
        try:
            return json.loads(Path(self.config_path).read_text())
        except json.JSONDecodeError:
            return {}
    
    def get_events(self, days: int = 7, calendar_id: str = None) -> List[Dict]:
        """Get upcoming events for N days"""
        calendar_id = calendar_id or self.config.get("default_calendar", "primary")
        
        # Return cached events if available and fresh
        cached = self._get_cached_events(calendar_id)
        if cached and cached.get("expires") > datetime.now().isoformat():
            return self._filter_by_days(cached["events"], days)
        
        # In production, this would call Google Calendar API
        # For now, return sample structure
        events = self._sample_events()
        
        self._cache_events(calendar_id, events)
        
        return self._filter_by_days(events, days)
    
    def _filter_by_days(self, events: List[Dict], days: int) -> List[Dict]:
        """Filter events within N days"""
        cutoff = (datetime.now() + timedelta(days=days)).isoformat()
        return [e for e in events if e.get("end", {}).get("dateTime", "") < cutoff]
    
    def _sample_events(self) -> List[Dict]:
        """Return sample events for demonstration"""
        now = datetime.now()
        
        return [
            {
                "id": "1",
                "summary": "Team Standup",
                "description": "Daily team sync",
                "start": {"dateTime": (now + timedelta(days=0, hours=1)).isoformat()},
                "end": {"dateTime": (now + timedelta(days=0, hours=1, minutes=30)).isoformat()},
                "location": "Remote",
                "status": "confirmed",
                "source": "google"
            },
            {
                "id": "2",
                "summary": "Gym Session",
                "description": "Morning workout",
                "start": {"dateTime": (now + timedelta(days=0, hours=5)).isoformat()},
                "end": {"dateTime": (now + timedelta(days=0, hours=6)).isoformat()},
                "location": "Gym",
                "status": "confirmed",
                "source": "google"
            },
            {
                "id": "3",
                "summary": "Project Review",
                "description": "Review project进展",
                "start": {"dateTime": (now + timedelta(days=1, hours=2)).isoformat()},
                "end": {"dateTime": (now + timedelta(days=1, hours=3)).isoformat()},
                "location": "Conference Room A",
                "status": "confirmed",
                "source": "google"
            }
        ]
    
    def _get_cached_events(self, calendar_id: str) -> Optional[Dict]:
        """Get cached events"""
        if not self.events_cache_path.exists():
            return None
        
        try:
            cache = json.loads(self.events_cache_path.read_text())
            if cache.get("calendar_id") == calendar_id:
                return cache
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _cache_events(self, calendar_id: str, events: List[Dict]):
        """Cache events"""
        cache = {
            "calendar_id": calendar_id,
            "cached_at": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(minutes=self.config.get("sync_interval_minutes", 15))).isoformat(),
            "events": events
        }
        
        self.events_cache_path.write_text(json.dumps(cache, indent=2))
    
    def create_event(self, summary: str, start: datetime, end: datetime, 
                    description: str = "", location: str = "", 
                    calendar_id: str = None) -> Dict:
        """Create a new calendar event"""
        calendar_id = calendar_id or self.config.get("default_calendar", "primary")
        
        event = {
            "id": f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
            "location": location,
            "status": "confirmed",
            "source": "berman-bot"
        }
        
        # In production: call Google Calendar API
        # POST https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events
        
        # Update cache
        self._cache_events(calendar_id, self.get_events() + [event])
        
        return event
    
    def update_event(self, event_id: str, updates: Dict) -> Dict:
        """Update an existing event"""
        # In production: call Google Calendar API
        # PATCH https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{eventId}
        
        return {"id": event_id, **updates, "updated": datetime.now().isoformat()}
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        # In production: call Google Calendar API
        # DELETE https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events/{eventId}
        
        return True
    
    def find_free_slots(self, duration_minutes: int = 60, 
                       days: int = 7) -> List[Dict]:
        """Find free time slots"""
        events = self.get_events(days)
        
        # Simple slot finder
        slots = []
        current = datetime.now()
        current = current.replace(hour=6, minute=0, second=0, microsecond=0)  # Start at 6 AM
        
        for day in range(days):
            day_start = current + timedelta(days=day)
            day_end = day_start.replace(hour=22, minute=0)  # End at 10 PM
            
            # Check each hour
            slot_time = day_start
            while slot_time + timedelta(minutes=duration_minutes) <= day_end:
                is_free = True
                
                for event in events:
                    event_start = event.get("start", {}).get("dateTime", "")
                    event_end = event.get("end", {}).get("dateTime", "")
                    
                    if event_start and event_end:
                        # Check overlap
                        if (slot_time.isoformat() < event_end and 
                            (slot_time + timedelta(minutes=duration_minutes)).isoformat() > event_start):
                            is_free = False
                            break
                
                if is_free:
                    slots.append({
                        "start": slot_time.isoformat(),
                        "end": (slot_time + timedelta(minutes=duration_minutes)).isoformat(),
                        "duration": duration_minutes
                    })
                
                slot_time += timedelta(hours=1)
        
        return slots
    
    def get_busy_times(self, days: int = 7) -> List[Dict]:
        """Get busy time periods"""
        events = self.get_events(days)
        
        busy = []
        for event in events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")
            if start and end:
                busy.append({
                    "start": start,
                    "end": end,
                    "summary": event.get("summary", "")
                })
        
        return busy
    
    def sync_external_calendar(self, source: str = "outlook") -> Dict:
        """Sync with external calendar (Outlook, etc.)"""
        # In production: implement OAuth flow and API calls
        
        return {
            "source": source,
            "synced_at": datetime.now().isoformat(),
            "events_imported": 0,
            "status": "pending_oauth"
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calendar Sync")
    parser.add_argument("--sync", action="store_true", help="Sync calendar")
    parser.add_argument("--events", type=int, default=7, help="Show events for N days")
    parser.add_argument("--free-slots", action="store_true", help="Find free time slots")
    parser.add_argument("--create", nargs=4, metavar=("SUMMARY", "START", "END", "LOCATION"), help="Create event")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    calendar = CalendarSync(args.workspace)
    
    if args.sync:
        result = calendar.sync_external_calendar()
        print(f"Synced: {result['status']}")
    elif args.events:
        events = calendar.get_events(days=args.events)
        print(f"\nUpcoming Events (next {args.events} days):")
        for e in events:
            start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
            print(f"  [{start[:10]}] {e.get('summary', 'Untitled')}")
    elif args.free_slots:
        slots = calendar.find_free_slots()
        print("\nFree Time Slots:")
        for s in slots[:10]:
            print(f"  {s['start'][:16]} - {s['end'][:16]}")
    elif args.create:
        summary, start_str, end_str, location = args.create
        calendar.create_event(
            summary=summary,
            start=datetime.fromisoformat(start_str),
            end=datetime.fromisoformat(end_str),
            location=location
        )
        print(f"Created: {summary}")
    else:
        events = calendar.get_events()
        print(f"Upcoming: {len(events)} events")


if __name__ == "__main__":
    main()
