"""
Smart Scheduler - Auto-schedule based on energy levels

Schedules tasks and events based on energy patterns and preferences.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class SmartScheduler:
    """Intelligent scheduling based on energy levels"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/Users/cortana/.openclaw/workspace/.scheduler_config"
        self.workspace_path = "/Users/cortana/.openclaw/workspace"
        self.calendar_path = Path(self.workspace_path) / "projects/berman-implementations/calendar"
        
        # Ensure directory exists
        self.calendar_path.mkdir(parents=True, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
        
        # Energy patterns
        self.energy_patterns = self.config.get("energy_patterns", {
            "morning": {"hours": (6, 12), "energy": "high", "suitable": ["gym", "deep_work", "creative"]},
            "afternoon": {"hours": (12, 17), "energy": "medium", "suitable": ["meetings", "admin", "reviews"]},
            "evening": {"hours": (17, 22), "energy": "low", "suitable": ["light_work", "learning", "personal"]}
        })
        
        # Task templates
        self.task_templates = self.config.get("task_templates", {
            "gym": {"duration_minutes": 60, "preferred_energy": "high", "flexible": True},
            "deep_work": {"duration_minutes": 90, "preferred_energy": "high", "flexible": False},
            "meetings": {"duration_minutes": 30, "preferred_energy": "medium", "flexible": True},
            "creative": {"duration_minutes": 60, "preferred_energy": "high", "flexible": True},
            "admin": {"duration_minutes": 30, "preferred_energy": "low", "flexible": True},
            "learning": {"duration_minutes": 45, "preferred_energy": "medium", "flexible": True}
        })
    
    def _load_config(self) -> Dict:
        """Load scheduler configuration"""
        if not Path(self.config_path).exists():
            default_config = {
                "energy_patterns": self.energy_patterns,
                "task_templates": self.task_templates,
                "focus_block_minutes": 90,
                "meeting_buffer_minutes": 15,
                "default_work_hours": {"start": 9, "end": 18}
            }
            Path(self.config_path).write_text(json.dumps(default_config, indent=2))
            return default_config
        
        try:
            return json.loads(Path(self.config_path).read_text())
        except json.JSONDecodeError:
            return {}
    
    def optimize_schedule(self, tasks: List[Dict], constraints: Dict = None) -> List[Dict]:
        """Optimize schedule based on energy and constraints"""
        constraints = constraints or {}
        
        # Sort tasks by priority and energy requirements
        optimized = []
        
        for task in tasks:
            task_type = task.get("type", "general")
            template = self.task_templates.get(task_type, {"duration_minutes": 60, "preferred_energy": "medium"})
            
            task["optimal_time"] = self._find_optimal_slot(
                task, template, constraints
            )
            optimized.append(task)
        
        # Sort by scheduled time
        optimized.sort(key=lambda x: x.get("optimal_time", {}).get("start", ""))
        
        return optimized
    
    def _find_optimal_slot(self, task: Dict, template: Dict, constraints: Dict) -> Dict:
        """Find optimal time slot for a task"""
        preferred_energy = template.get("preferred_energy", "medium")
        duration = template.get("duration_minutes", 60)
        flexible = template.get("flexible", True)
        
        # Get busy times from calendar
        busy_times = constraints.get("busy_times", [])
        
        # Find best energy period
        best_period = None
        for period_name, period_data in self.energy_patterns.items():
            if period_data["energy"] == preferred_energy:
                best_period = period_name
                break
        
        # If preferred not available, find next best
        if not best_period:
            energy_order = ["high", "medium", "low"]
            for level in energy_order:
                for period_name, period_data in self.energy_patterns.items():
                    if period_data["energy"] == level:
                        best_period = period_name
                        break
                if best_period:
                    break
        
        if not best_period:
            best_period = "morning"
        
        period_data = self.energy_patterns[best_period]
        hours = period_data["hours"]
        
        # Find first available slot
        start_hour = hours[0]
        work_hours = constraints.get("work_hours", self.config.get("default_work_hours", {"start": 9, "end": 18}))
        
        if flexible:
            start_hour = max(start_hour, work_hours["start"])
        else:
            start_hour = max(start_hour, work_hours["start"])
        
        # Simple slot finding
        slot_start = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        # Advance to next available day if needed
        for day in range(7):
            current = slot_start + timedelta(days=day)
            current = current.replace(hour=start_hour)
            
            # Check each hour
            for hour in range(start_hour, min(hours[1], work_hours["end"])):
                check_time = current.replace(hour=hour)
                
                # Check if slot is free
                is_free = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy.get("start"))
                    busy_end = datetime.fromisoformat(busy.get("end"))
                    
                    if check_time < busy_end and (check_time + timedelta(minutes=duration)) > busy_start:
                        is_free = False
                        break
                
                if is_free:
                    return {
                        "start": check_time.isoformat(),
                        "end": (check_time + timedelta(minutes=duration)).isoformat(),
                        "energy_period": best_period,
                        "energy_level": period_data["energy"]
                    }
        
        # No slot found, return tentative time
        tentative = datetime.now().replace(hour=start_hour) + timedelta(days=1)
        return {
            "start": tentative.isoformat(),
            "end": (tentative + timedelta(minutes=duration)).isoformat(),
            "energy_period": best_period,
            "energy_level": period_data["energy"],
            "note": "No optimal slot found, tentative booking"
        }
    
    def schedule_gym_for_high_energy(self, busy_times: List[Dict] = None) -> Dict:
        """Schedule gym session during high energy hours"""
        gym_task = {
            "name": "Gym Session",
            "type": "gym",
            "required": True
        }
        
        constraints = {
            "busy_times": busy_times or [],
            "work_hours": self.config.get("default_work_hours", {"start": 9, "end": 18})
        }
        
        result = self.optimize_schedule([gym_task], constraints)[0]
        
        return {
            "task": "Gym Session",
            "scheduled_time": result.get("optimal_time", {}).get("start"),
            "duration": self.task_templates["gym"]["duration_minutes"],
            "reason": "High energy period - optimal for workout"
        }
    
    def block_focus_time(self, duration_minutes: int = None, before_event: str = None) -> Dict:
        """Block focus time before important events"""
        duration = duration_minutes or self.config.get("focus_block_minutes", 90)
        
        # Find upcoming important event
        focus_task = {
            "name": "Focus Block",
            "type": "deep_work",
            "flexible": False
        }
        
        result = self.optimize_schedule([focus_task])[0]
        
        return {
            "task": "Focus Time",
            "scheduled_time": result.get("optimal_time", {}).get("start"),
            "duration": duration,
            "reason": "Deep work block - energy optimized"
        }
    
    def auto_decline_conflicts(self, events: List[Dict], rules: Dict = None) -> List[Dict]:
        """Identify conflicting events and suggest declines"""
        rules = rules or {
            "decline_if": [
                {"overlap": True, "type": "optional"},
                {"overlap": True, "type": "personal", "priority": "low"}
            ]
        }
        
        suggestions = []
        
        # Simple conflict detection
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events):
                if i >= j:
                    continue
                
                # Check overlap
                if self._events_overlap(event1, event2):
                    # Determine which to decline
                    decline = self._decide_decline(event1, event2, rules)
                    if decline:
                        suggestions.append(decline)
        
        return suggestions
    
    def _events_overlap(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events overlap"""
        start1 = event1.get("start", {}).get("dateTime", "")
        end1 = event1.get("end", {}).get("dateTime", "")
        start2 = event2.get("start", {}).get("dateTime", "")
        end2 = event2.get("end", {}).get("dateTime", "")
        
        if not all([start1, end1, start2, end2]):
            return False
        
        from datetime import datetime
        s1 = datetime.fromisoformat(start1)
        e1 = datetime.fromisoformat(end1)
        s2 = datetime.fromisoformat(start2)
        e2 = datetime.fromisoformat(end2)
        
        return s1 < e2 and e1 > s2
    
    def _decide_decline(self, event1: Dict, event2: Dict, rules: Dict) -> Optional[Dict]:
        """Decide which event to decline"""
        # Simple logic: decline optional or lower priority
        e1_required = event1.get("required", False)
        e2_required = event2.get("required", False)
        
        if not e1_required and e2_required:
            return {
                "event_to_decline": event1.get("id"),
                "reason": "Optional event conflicts with required",
                "suggested_reply": "Sorry, I have a conflict at that time"
            }
        elif e1_required and not e2_required:
            return {
                "event_to_decline": event2.get("id"),
                "reason": "Optional event conflicts with required",
                "suggested_reply": "Sorry, I have a conflict at that time"
            }
        
        return None
    
    def get_energy_forecast(self, days: int = 7) -> List[Dict]:
        """Get energy forecast for upcoming days"""
        forecast = []
        
        for day in range(days):
            date = (datetime.now() + timedelta(days=day))
            day_name = date.strftime("%A")
            
            # Default energy pattern by day
            pattern = self.energy_patterns.get("morning", {"energy": "high"})
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day_name,
                "morning": pattern["energy"],
                "afternoon": "medium",
                "evening": "low",
                "recommendations": self._get_day_recommendations(day_name)
            })
        
        return forecast
    
    def _get_day_recommendations(self, day: str) -> List[str]:
        """Get recommendations for a specific day"""
        recommendations = []
        
        if day in ["Monday", "Tuesday", "Wednesday"]:
            recommendations.extend([
                "Good day for deep work",
                "Schedule important meetings in afternoon"
            ])
        elif day == "Thursday":
            recommendations.append("Good for planning and reviews")
        elif day in ["Friday", "Saturday", "Sunday"]:
            recommendations.extend([
                "Good for lighter tasks",
                "Personal projects recommended"
            ])
        
        return recommendations
    
    def suggest_schedule_changes(self, current_events: List[Dict], 
                                preferences: Dict = None) -> List[Dict]:
        """Suggest schedule improvements"""
        suggestions = []
        
        for i, event in enumerate(current_events):
            event_type = event.get("type", "general")
            template = self.task_templates.get(event_type, {})
            
            current_energy = self._get_event_energy(event)
            preferred_energy = template.get("preferred_energy", "medium")
            
            if current_energy != preferred_energy and not template.get("flexible", True):
                suggestions.append({
                    "event_id": event.get("id"),
                    "current_time": event.get("start", {}).get("dateTime", ""),
                    "current_energy": current_energy,
                    "preferred_energy": preferred_energy,
                    "suggestion": f"Consider rescheduling to {preferred_energy} energy period"
                })
        
        return suggestions
    
    def _get_event_energy(self, event: Dict) -> str:
        """Get the energy level for an event's time"""
        start = event.get("start", {}).get("dateTime", "")
        if not start:
            return "unknown"
        
        from datetime import datetime
        hour = datetime.fromisoformat(start).hour
        
        for period_name, period_data in self.energy_patterns.items():
            hours = period_data["hours"]
            if hours[0] <= hour < hours[1]:
                return period_data["energy"]
        
        return "low"


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Scheduler")
    parser.add_argument("--optimize", action="store_true", help="Optimize schedule")
    parser.add_argument("--forecast", action="store_true", help="Show energy forecast")
    parser.add_argument("--schedule-gym", action="store_true", help="Schedule gym")
    parser.add_argument("--focus-block", action="store_true", help="Block focus time")
    parser.add_argument("--suggest", action="store_true", help="Suggest changes")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    scheduler = SmartScheduler(args.workspace)
    
    if args.forecast:
        forecast = scheduler.get_energy_forecast()
        print("\n📅 Energy Forecast")
        for day in forecast:
            print(f"\n{day['date']} ({day['day']}):")
            print(f"  Morning: {day['morning']} | Afternoon: {day['afternoon']} | Evening: {day['evening']}")
            for rec in day.get('recommendations', []):
                print(f"  💡 {rec}")
    elif args.schedule_gym:
        result = scheduler.schedule_gym_for_high_energy()
        print(f"\n🏋️ Gym Session")
        print(f"Scheduled: {result['scheduled_time']}")
        print(f"Reason: {result['reason']}")
    elif args.focus_block:
        result = scheduler.block_focus_time()
        print(f"\n🔒 Focus Time")
        print(f"Blocked: {result['scheduled_time']}")
        print(f"Duration: {result['duration']} min")
    elif args.suggest:
        suggestions = scheduler.suggest_schedule_changes([])
        if suggestions:
            print("\n📝 Suggestions:")
            for s in suggestions:
                print(f"  - {s['suggestion']}")
        else:
            print("\n✅ No suggestions - schedule looks optimal!")
    elif args.optimize:
        print("\n⚡ Optimizing schedule...")
        result = scheduler.optimize_schedule([])
        print("Done!")


if __name__ == "__main__":
    main()
