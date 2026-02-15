"""
Memory Compressor - Weekly compression of MEMORY.md

Reduces context window load by compressing historical memories
into summaries while preserving key information.
"""

import os
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import hashlib


class MemoryCompressor:
    """Compresses and archives old memories"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or "/Users/cortana/.openclaw/workspace"
        self.memory_path = Path(self.workspace_path) / "memory"
        self.archive_path = self.memory_path / "archive"
        self.weekly_path = self.memory_path / "weekly"
        self.long_term_memory_path = self.memory_path / "long_term_memory.json"
        
        # Ensure directories exist
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.weekly_path.mkdir(parents=True, exist_ok=True)
    
    def compress_weekly(self, weeks: int = 4) -> Dict:
        """Compress memories from N weeks ago"""
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        memories_to_compress = []
        
        # Find all daily memory files
        if self.memory_path.exists():
            for mem_file in self.memory_path.glob("*.md"):
                if mem_file.stem == "MEMORY":  # Skip main MEMORY.md
                    continue
                
                try:
                    file_date = datetime.strptime(mem_file.stem, "%Y-%m-%d")
                    if file_date < cutoff_date:
                        memories_to_compress.append(mem_file)
                except ValueError:
                    continue
        
        # Read and compress memories
        compressed_data = {
            "compressed_date": datetime.now().isoformat(),
            "weeks_archived": weeks,
            "files_archived": len(memories_to_compress),
            "summaries": []
        }
        
        for mem_file in memories_to_compress:
            content = mem_file.read_text()
            summary = self._summarize_memory(content)
            compressed_data["summaries"].append({
                "date": mem_file.stem,
                "summary": summary,
                "word_count": len(content.split()),
                "original_hash": hashlib.md5(content.encode()).hexdigest()
            })
        
        # Save compressed archive
        archive_filename = f"archive_{cutoff_date.strftime('%Y-%m-%d')}.json.gz"
        archive_path = self.archive_path / archive_filename
        
        with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
            json.dump(compressed_data, f, indent=2, ensure_ascii=False)
        
        # Remove old files
        for mem_file in memories_to_compress:
            mem_file.unlink()
        
        # Update main MEMORY.md with summary
        self._update_main_memory(compressed_data)
        
        return compressed_data
    
    def _summarize_memory(self, content: str, max_length: int = 500) -> str:
        """Create a concise summary of memory content"""
        # Simple extraction-based summarization
        lines = content.strip().split('\n')
        
        # Extract key sentences (first sentence of each paragraph)
        key_points = []
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue  # Skip headers
            if len(line) > 20:
                key_points.append(line)
        
        # Join and truncate
        summary = ' '.join(key_points)
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary or "No significant events recorded"
    
    def _update_main_memory(self, compressed_data: Dict):
        """Update main MEMORY.md with archive summary"""
        memory_path = Path(self.workspace_path) / "MEMORY.md"
        
        archive_entry = f"""
## Archived Week ({compressed_data['compressed_date']})

**Archived:** {compressed_data['files_archived']} daily entries

### Key Events:
"""
        for summary in compressed_data['summaries'][:5]:  # Top 5 events
            archive_entry += f"- **{summary['date']}**: {summary['summary']}\n"
        
        archive_entry += f"\n*Full archive available in: `memory/archive/`*\n"
        
        if memory_path.exists():
            existing = memory_path.read_text()
            # Find last archive section and append, or add at end
            if "## Archived" in existing:
                parts = existing.split("## Archived")
                memory_path.write_text(parts[0] + archive_entry + "\n".join(parts[1:]))
            else:
                memory_path.write_text(existing + archive_entry)
        else:
            memory_path.write_text("# Memory\n\n" + archive_entry)
    
    def extract_weekly_summary(self) -> str:
        """Generate weekly summary for the current week"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        summaries = []
        
        if self.memory_path.exists():
            for mem_file in sorted(self.memory_path.glob("*.md"), reverse=True):
                if mem_file.stem == "MEMORY":
                    continue
                
                try:
                    file_date = datetime.strptime(mem_file.stem, "%Y-%m-%d")
                    if file_date >= week_ago:
                        content = mem_file.read_text()
                        day_summary = self._summarize_memory(content, max_length=200)
                        summaries.append({
                            "date": mem_file.stem,
                            "summary": day_summary
                        })
                except ValueError:
                    continue
        
        # Generate weekly report
        report = f"# Weekly Summary ({week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')})\n\n"
        
        if summaries:
            for s in summaries:
                report += f"## {s['date']}\n{s['summary']}\n\n"
        else:
            report += "*No memories recorded this week*\n"
        
        # Save to weekly folder
        weekly_file = self.weekly_path / f"summary_{now.strftime('%Y-%W')}.md"
        weekly_file.write_text(report)
        
        return report


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Compressor")
    parser.add_argument("--weeks", type=int, default=4, help="Weeks to compress")
    parser.add_argument("--weekly-summary", action="store_true", help="Generate weekly summary")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    compressor = MemoryCompressor(args.workspace)
    
    if args.weekly_summary:
        result = compressor.extract_weekly_summary()
        print(result)
    else:
        result = compressor.compress_weekly(args.weeks)
        print(f"Compressed {result['files_archived']} files")
        print(f"Archive: {result['compressed_date']}")


if __name__ == "__main__":
    main()
