"""
Memory Search - Semantic search across all memory files

Provides fast, semantic-like search across all memory files
using keyword matching and ranking.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json


class MemorySearch:
    """Search across all memory files"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or "/Users/cortana/.openclaw/workspace"
        self.memory_path = Path(self.workspace_path) / "memory"
        self.long_term_memory_path = Path(self.workspace_path) / "long_term_memory.json"
        
        # Build search index
        self.index = {}
        self._build_index()
    
    def _build_index(self):
        """Build search index from all memory files"""
        self.index = {
            "files": {},
            "keywords": {},
            "last_updated": datetime.now().isoformat()
        }
        
        if not self.memory_path.exists():
            return
        
        # Index all memory files
        for mem_file in self.memory_path.glob("*.md"):
            content = mem_file.read_text()
            file_info = {
                "path": str(mem_file),
                "name": mem_file.name,
                "date": mem_file.stem if mem_file.stem != "MEMORY" else None,
                "content": content,
                "word_count": len(content.split())
            }
            
            # Index by date
            if mem_file.stem != "MEMORY":
                self.index["files"][mem_file.stem] = file_info
            
            # Index keywords
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            for word in set(words):
                if word not in self.index["keywords"]:
                    self.index["keywords"][word] = []
                self.index["keywords"][word].append({
                    "file": mem_file.name,
                    "count": words.count(word)
                })
        
        # Index long-term memory
        if self.long_term_memory_path.exists():
            try:
                ltm = json.loads(self.long_term_memory_path.read_text())
                self.index["long_term_memory"] = ltm
            except json.JSONDecodeError:
                pass
    
    def search(self, query: str, limit: int = 10, include_long_term: bool = True) -> List[Dict]:
        """Search memory files for query"""
        results = []
        query_lower = query.lower()
        query_words = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)
        
        # Search in indexed files
        for date, file_info in sorted(self.index.get("files", {}).items(), reverse=True):
            score = self._calculate_relevance(file_info["content"], query_words, query_lower)
            if score > 0:
                # Find matching snippets
                snippets = self._find_snippets(file_info["content"], query_words)
                results.append({
                    "type": "daily_memory",
                    "date": date,
                    "file": file_info["name"],
                    "score": score,
                    "snippets": snippets[:3],
                    "word_count": file_info["word_count"]
                })
        
        # Search long-term memory
        if include_long_term and "long_term_memory" in self.index:
            ltm_results = self._search_long_term_memory(query, query_words)
            results.extend(ltm_results)
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit]
    
    def _calculate_relevance(self, content: str, query_words: List[str], query_lower: str) -> float:
        """Calculate relevance score for a document"""
        if not query_words:
            return 0
        
        content_lower = content.lower()
        score = 0.0
        
        # Exact phrase match (high weight)
        if query_lower in content_lower:
            score += 10.0
        
        # Word matches
        content_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', content_lower))
        
        for word in query_words:
            if word in content_words:
                score += 2.0
            # Partial matches
            for cw in content_words:
                if word in cw or cw in word:
                    score += 0.5
        
        # Title/header matches (higher weight)
        header_matches = len(re.findall(r'^#+ .*' + '|'.join(query_words) + r'.*$', content_lower, re.MULTILINE))
        score += header_matches * 3.0
        
        return score
    
    def _find_snippets(self, content: str, query_words: List[str], context_chars: int = 100) -> List[str]:
        """Find matching snippets around query words"""
        snippets = []
        content_lower = content.lower()
        
        for word in query_words:
            pattern = rf'.{{0,{context_chars}}}\b{re.escape(word)}\b.{{0,{context_chars}}}'
            matches = re.findall(pattern, content_lower)
            
            for match in matches:
                # Clean up snippet
                snippet = match.strip()
                if len(snippet) > context_chars * 2:
                    snippet = snippet[:context_chars] + "..."
                snippets.append("..." + snippet + "...")
        
        # Remove duplicates
        return list(dict.fromkeys(snippets))
    
    def _search_long_term_memory(self, query: str, query_words: List[str]) -> List[Dict]:
        """Search in long-term memory"""
        results = []
        ltm = self.index.get("long_term_memory", {})
        
        if not ltm or "facts" not in ltm:
            return results
        
        for category, facts in ltm["facts"].items():
            for fact in facts:
                content = fact.get("content", "")
                content_lower = content.lower()
                
                # Calculate relevance
                score = self._calculate_relevance(content, query_words, query.lower())
                
                if score > 0:
                    results.append({
                        "type": "long_term_fact",
                        "category": category,
                        "content": content,
                        "date_extracted": fact.get("date_extracted"),
                        "score": score,
                        "snippets": [content[:200]]
                    })
        
        return results
    
    def search_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get memories within a date range"""
        results = []
        
        for date, file_info in self.index.get("files", {}).items():
            if start_date <= date <= end_date:
                results.append({
                    "date": date,
                    "word_count": file_info["word_count"],
                    "preview": file_info["content"][:500]
                })
        
        return results
    
    def get_recent_memories(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get most recent memories"""
        from datetime import datetime, timedelta
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        results = []
        
        for date in sorted(self.index.get("files", {}).keys(), reverse=True):
            if date >= cutoff:
                file_info = self.index["files"][date]
                results.append({
                    "date": date,
                    "word_count": file_info["word_count"],
                    "preview": file_info["content"][:300]
                })
        
        return results[:limit]
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics"""
        stats = {
            "total_daily_memories": len(self.index.get("files", {})),
            "indexed_keywords": len(self.index.get("keywords", {})),
            "index_last_updated": self.index.get("last_updated"),
        }
        
        # Add long-term memory stats
        if "long_term_memory" in self.index:
            ltm = self.index["long_term_memory"]
            total_facts = sum(len(facts) for facts in ltm.get("facts", {}).values())
            stats["long_term_facts"] = total_facts
            stats["ltm_last_updated"] = ltm.get("last_updated")
        
        return stats


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Search")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--recent", type=int, help="Show recent memories (days)")
    parser.add_argument("--stats", action="store_true", help="Show memory stats")
    parser.add_argument("--date-range", nargs=2, metavar=("START", "END"), help="Date range filter")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    search = MemorySearch(args.workspace)
    
    if args.stats:
        stats = search.get_memory_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
    elif args.recent:
        memories = search.get_recent_memories(days=args.recent, limit=args.limit)
        for mem in memories:
            print(f"[{mem['date']}] {mem['preview'][:100]}...")
    elif args.date_range:
        memories = search.search_by_date_range(args.date_range[0], args.date_range[1])
        for mem in memories:
            print(f"[{mem['date']}] {mem['preview'][:100]}...")
    elif args.query:
        results = search.search(args.query, limit=args.limit)
        print(f"Found {len(results)} results:\n")
        for r in results:
            date = r.get("date", r.get("category", "unknown"))
            score = r.get("score", 0)
            print(f"  Score: {score:.1f} | {date}")
            for snippet in r.get("snippets", [])[:2]:
                print(f"    {snippet[:100]}")
            print()
    else:
        print("Usage: memory_search.py <query> [--limit N] [--recent days]")


if __name__ == "__main__":
    main()
