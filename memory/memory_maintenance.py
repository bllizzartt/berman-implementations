"""
Memory Maintenance - Daily review, summarize, archive

Automated daily memory maintenance tasks:
- Review recent memories
- Generate summaries
- Archive old data
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class MemoryMaintenance:
    """Daily memory maintenance tasks"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or "/Users/cortana/.openclaw/workspace"
        self.memory_path = Path(self.workspace_path) / "memory"
        self.archive_path = self.memory_path / "archive"
        
        # Ensure directories exist
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
    
    def daily_review(self) -> Dict:
        """Review today's memory and generate insights"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_mem_path = self.memory_path / f"{today}.md"
        
        review = {
            "date": today,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "insights": [],
            "suggestions": []
        }
        
        # Check if today's memory exists
        if not today_mem_path.exists():
            review["status"] = "no_memory"
            review["suggestions"].append("Create today's memory file")
            return review
        
        content = today_mem_path.read_text()
        
        # Analyze content
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        review["word_count"] = word_count
        review["line_count"] = line_count
        
        # Generate insights
        if word_count < 50:
            review["insights"].append("Memory is quite brief - consider adding more details")
        elif word_count > 1000:
            review["insights"].append("Comprehensive memory - good job capturing the day")
        
        # Check for action items
        action_patterns = ["todo", "task", "remember to", "don't forget", "must"]
        for pattern in action_patterns:
            if pattern.lower() in content.lower():
                review["insights"].append(f"Contains action items related to '{pattern}'")
        
        # Check for decisions
        if any(word in content.lower() for word in ["decided", "chose", "agreed", "concluded"]):
            review["insights"].append("Contains decisions that were made")
        
        # Generate suggestions
        if "MEMORY.md" in content:
            review["suggestions"].append("Consider adding to long-term memory")
        
        review["status"] = "complete"
        
        return review
    
    def summarize_daily(self) -> Dict:
        """Generate summary of recent memories"""
        summaries = []
        
        # Get memories from last 7 days
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            mem_file = self.memory_path / f"{date}.md"
            
            if mem_file.exists():
                content = mem_file.read_text()
                summary = self._extract_summary(content, date)
                summaries.append(summary)
        
        # Generate combined summary
        combined = {
            "period": f"Last {len(summaries)} days",
            "generated": datetime.now().isoformat(),
            "summaries": summaries,
            "highlights": []
        }
        
        # Extract highlights
        for summary in summaries:
            if "decisions" in summary.get("tags", []):
                combined["highlights"].append({
                    "date": summary["date"],
                    "type": "decision",
                    "content": summary["content"][:200]
                })
        
        # Save summary
        summary_path = self.memory_path / f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_path.write_text(self._format_summary(combined))
        
        return combined
    
    def _extract_summary(self, content: str, date: str) -> Dict:
        """Extract key summary from memory content"""
        lines = content.strip().split('\n')
        
        # Find first meaningful paragraph
        summary_text = ""
        tags = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if len(line) > 20:
                summary_text = line
                break
        
        # Detect tags based on content
        content_lower = content.lower()
        if "decided" in content_lower or "chose" in content_lower:
            tags.append("decisions")
        if "todo" in content_lower or "task" in content_lower:
            tags.append("tasks")
        if "meeting" in content_lower or "call" in content_lower:
            tags.append("communication")
        if "learned" in content_lower or "discovered" in content_lower:
            tags.append("learning")
        
        return {
            "date": date,
            "content": summary_text,
            "word_count": len(content.split()),
            "tags": tags
        }
    
    def _format_summary(self, combined: Dict) -> str:
        """Format summary as markdown"""
        lines = [
            f"# Daily Summary - {combined['period']}",
            f"*Generated: {combined['generated']}*",
            "",
            "## Daily Summaries",
            ""
        ]
        
        for summary in combined["summaries"]:
            lines.append(f"### {summary['date']}")
            lines.append(f"**Words:** {summary['word_count']}")
            lines.append(f"**Tags:** {', '.join(summary['tags']) if summary['tags'] else 'None'}")
            lines.append("")
            lines.append(f">{summary['content'][:300]}")
            lines.append("")
        
        if combined["highlights"]:
            lines.append("## Highlights")
            lines.append("")
            for h in combined["highlights"]:
                lines.append(f"- **{h['date']}** ({h['type']}): {h['content']}")
        
        return '\n'.join(lines)
    
    def archive_old_memories(self, days: int = 30) -> Dict:
        """Archive memories older than N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        archived = []
        
        # Find old memories
        for mem_file in self.memory_path.glob("*.md"):
            if mem_file.stem < cutoff_date and mem_file.stem != "MEMORY":
                content = mem_file.read_text()
                
                # Create archive entry
                archive_entry = {
                    "original_date": mem_file.stem,
                    "archived_date": datetime.now().isoformat(),
                    "content": content,
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
                
                # Save to archive
                archive_file = self.archive_path / f"{mem_file.stem}.json"
                archive_file.write_text(json.dumps(archive_entry, indent=2))
                
                # Remove original
                mem_file.unlink()
                archived.append(mem_file.stem)
        
        return {
            "archived_count": len(archived),
            "cutoff_date": cutoff_date,
            "archived_files": archived
        }
    
    def cleanup_duplicates(self) -> Dict:
        """Find and clean up duplicate entries"""
        seen_hashes = {}
        duplicates = []
        
        for mem_file in self.memory_path.glob("*.md"):
            if mem_file.stem == "MEMORY":
                continue
            
            content = mem_file.read_text()
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash in seen_hashes:
                duplicates.append({
                    "original": seen_hashes[content_hash],
                    "duplicate": mem_file.stem,
                    "action": "kept_oldest"
                })
            else:
                seen_hashes[content_hash] = mem_file.stem
        
        return {
            "checked_files": len(seen_hashes),
            "duplicates_found": len(duplicates),
            "duplicates": duplicates
        }
    
    def run_daily_tasks(self) -> Dict:
        """Run all daily maintenance tasks"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {}
        }
        
        # Daily review
        results["tasks"]["daily_review"] = self.daily_review()
        
        # Generate summary
        results["tasks"]["summarize"] = self.summarize_daily()
        
        # Check for old memories (archive after 30 days)
        archive_result = self.archive_old_memories(days=30)
        results["tasks"]["archive"] = archive_result
        
        # Check for duplicates
        results["tasks"]["cleanup"] = self.cleanup_duplicates()
        
        # Overall status
        results["status"] = "success" if all(
            t.get("status") == "complete" or t.get("archived_count", 0) >= 0
            for t in results["tasks"].values()
        ) else "warnings"
        
        return results


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Maintenance")
    parser.add_argument("--daily", action="store_true", help="Run daily tasks")
    parser.add_argument("--review", action="store_true", help="Review today's memory")
    parser.add_argument("--summarize", action="store_true", help="Generate summary")
    parser.add_argument("--archive", type=int, default=30, help="Archive memories older than N days")
    parser.add_argument("--cleanup", action="store_true", help="Clean up duplicates")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    maintenance = MemoryMaintenance(args.workspace)
    
    if args.daily:
        results = maintenance.run_daily_tasks()
        print(f"Daily tasks completed: {results['status']}")
        for task, result in results["tasks"].items():
            print(f"  - {task}: OK")
    elif args.review:
        review = maintenance.daily_review()
        print(f"Review: {review['status']}")
        for insight in review.get("insights", []):
            print(f"  💡 {insight}")
        for suggestion in review.get("suggestions", []):
            print(f"  → {suggestion}")
    elif args.summarize:
        summary = maintenance.summarize_daily()
        print(f"Summary generated for {summary['period']}")
        print(f"Summarized {len(summary['summaries'])} days")
    elif args.archive:
        result = maintenance.archive_old_memories(days=args.archive)
        print(f"Archived {result['archived_count']} files")
    elif args.cleanup:
        result = maintenance.cleanup_duplicates()
        print(f"Checked {result['checked_files']} files")
        print(f"Found {result['duplicates_found']} duplicates")
    else:
        results = maintenance.run_daily_tasks()
        print(f"Daily tasks: {results['status']}")


if __name__ == "__main__":
    main()
