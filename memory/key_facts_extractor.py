"""
Key Facts Extractor - Extract important facts from memories

Uses simple extraction and keyword matching to identify
important facts and store them in long_term_memory.json
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
import hashlib


class KeyFactsExtractor:
    """Extracts and manages key facts from memories"""
    
    # Keywords that indicate important information
    IMPORTANT_PATTERNS = [
        r'(?:important|critical|key|essential|must|should|remember)',
        r'(?:decid|decided|decision)',
        r'(?:prefer|preference|favorite)',
        r'(?:allergy|intolerant|sensitive)',
        r'(?:goal|objective|target)',
        r'(?:habit|routine|schedule)',
        r'(?:contact|email|phone|address)',
        r'(?:password|credential|api|key)',
        r'(?:project|task|todo|deadline)',
        r'(?:learning|learned|discovered)',
        r'(?:preferenc|preference)',
    ]
    
    # Categories for facts
    CATEGORIES = {
        "decisions": ["decided", "decision", "chose", "chosen", "agreed"],
        "preferences": ["prefer", "like", "love", "favorite", "enjoy"],
        "goals": ["goal", "objective", "target", "aim", "want to"],
        "constraints": ["must", "shouldn't", "can't", "never", "always avoid"],
        "learnings": ["learned", "discovered", "found out", "realized"],
        "contacts": ["email", "phone", "contact", "reach"],
        "projects": ["project", "task", "todo", "deadline"],
        "habits": ["habit", "routine", "schedule", "every day"],
    }
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or "/Users/cortana/.openclaw/workspace"
        self.memory_path = Path(self.workspace_path) / "memory"
        self.long_term_memory_path = Path(self.workspace_path) / "long_term_memory.json"
        self.facts_path = self.memory_path / "facts"
        
        # Ensure directories exist
        self.facts_path.mkdir(parents=True, exist_ok=True)
    
    def extract_all_facts(self) -> Dict:
        """Extract facts from all memory files"""
        all_facts = {
            "last_updated": datetime.now().isoformat(),
            "facts": {
                "decisions": [],
                "preferences": [],
                "goals": [],
                "constraints": [],
                "learnings": [],
                "contacts": [],
                "projects": [],
                "habits": [],
                "other": []
            },
            "metadata": {
                "files_processed": 0,
                "facts_extracted": 0
            }
        }
        
        if not self.memory_path.exists():
            return all_facts
        
        # Process all memory files
        for mem_file in sorted(self.memory_path.glob("*.md")):
            if mem_file.stem == "MEMORY":
                continue
            
            content = mem_file.read_text()
            facts = self._extract_facts_from_content(content, mem_file.stem)
            
            # Categorize and add to all_facts
            for category, category_facts in facts.items():
                all_facts["facts"][category].extend(category_facts)
            
            all_facts["metadata"]["files_processed"] += 1
        
        # Count total facts
        all_facts["metadata"]["facts_extracted"] = sum(
            len(facts) for facts in all_facts["facts"].values()
        )
        
        # Deduplicate facts
        self._deduplicate_facts(all_facts["facts"])
        
        # Save to long_term_memory.json
        self._save_long_term_memory(all_facts)
        
        # Save individual category files
        self._save_category_files(all_facts["facts"])
        
        return all_facts
    
    def _extract_facts_from_content(self, content: str, date: str) -> Dict[str, List[Dict]]:
        """Extract facts from a single memory file"""
        facts = {cat: [] for cat in self.CATEGORIES.keys()}
        facts["other"] = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip headers
            if line.startswith('#'):
                continue
            
            # Check if line contains important information
            if self._is_important(line):
                category = self._categorize(line)
                fact = {
                    "content": line,
                    "date_extracted": date,
                    "timestamp": datetime.now().isoformat(),
                    "hash": hashlib.md5(line.encode()).hexdigest()[:8]
                }
                facts[category].append(fact)
        
        return facts
    
    def _is_important(self, text: str) -> bool:
        """Check if text contains important information"""
        text_lower = text.lower()
        
        # Check for importance patterns
        for pattern in self.IMPORTANT_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        # Check for category keywords
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return True
        
        # Lines with colons often contain key-value info
        if ':' in text and len(text) < 200:
            return True
        
        return False
    
    def _categorize(self, text: str) -> str:
        """Determine the category of a fact"""
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return "other"
    
    def _deduplicate_facts(self, facts: Dict[str, List[Dict]]):
        """Remove duplicate facts within categories"""
        seen_hashes = {}
        
        for category in facts:
            unique_facts = []
            for fact in facts[category]:
                h = fact.get("hash", "")
                if h not in seen_hashes:
                    seen_hashes[h] = True
                    unique_facts.append(fact)
            facts[category] = unique_facts
    
    def _save_long_term_memory(self, all_facts: Dict):
        """Save facts to long_term_memory.json"""
        # Read existing if present
        existing = {}
        if self.long_term_memory_path.exists():
            try:
                existing = json.loads(self.long_term_memory_path.read_text())
            except json.JSONDecodeError:
                pass
        
        # Merge with existing, keeping most recent
        existing.update(all_facts)
        
        # Write updated memory
        self.long_term_memory_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False)
        )
    
    def _save_category_files(self, facts: Dict[str, List[Dict]]):
        """Save facts to individual category files"""
        for category, category_facts in facts.items():
            if category_facts:
                category_file = self.facts_path / f"{category}.json"
                category_file.write_text(
                    json.dumps({
                        "category": category,
                        "count": len(category_facts),
                        "facts": category_facts
                    }, indent=2, ensure_ascii=False)
                )
    
    def search_facts(self, query: str, category: str = None) -> List[Dict]:
        """Search facts by content"""
        results = []
        query_lower = query.lower()
        
        # Load long term memory
        if not self.long_term_memory_path.exists():
            return results
        
        try:
            memory = json.loads(self.long_term_memory_path.read_text())
        except json.JSONDecodeError:
            return results
        
        facts_to_search = memory["facts"]
        
        if category and category in facts_to_search:
            facts_to_search = {category: facts_to_search[category]}
        
        for cat, facts in facts_to_search.items():
            for fact in facts:
                if query_lower in fact.get("content", "").lower():
                    results.append({
                        **fact,
                        "category": cat
                    })
        
        return results
    
    def get_facts_summary(self) -> Dict:
        """Get summary of all stored facts"""
        if not self.long_term_memory_path.exists():
            return {"total_facts": 0, "categories": {}}
        
        try:
            memory = json.loads(self.long_term_memory_path.read_text())
        except json.JSONDecodeError:
            return {"total_facts": 0, "categories": {}}
        
        summary = {
            "last_updated": memory.get("last_updated"),
            "total_facts": sum(len(facts) for facts in memory["facts"].values()),
            "categories": {}
        }
        
        for category, facts in memory["facts"].items():
            summary["categories"][category] = len(facts)
        
        return summary


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Key Facts Extractor")
    parser.add_argument("--extract", action="store_true", help="Extract all facts")
    parser.add_argument("--search", type=str, help="Search facts")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--summary", action="store_true", help="Show facts summary")
    parser.add_argument("--workspace", type=str, help="Workspace path")
    
    args = parser.parse_args()
    
    extractor = KeyFactsExtractor(args.workspace)
    
    if args.extract:
        result = extractor.extract_all_facts()
        print(f"Extracted {result['metadata']['facts_extracted']} facts from {result['metadata']['files_processed']} files")
    elif args.search:
        results = extractor.search_facts(args.search, args.category)
        print(f"Found {len(results)} matching facts:")
        for r in results[:10]:
            print(f"  [{r.get('category', 'unknown')}] {r['content'][:100]}")
    elif args.summary:
        summary = extractor.get_facts_summary()
        print(f"Total facts: {summary['total_facts']}")
        for cat, count in summary.get('categories', {}).items():
            print(f"  {cat}: {count}")
    else:
        result = extractor.extract_all_facts()
        print(f"Extracted {result['metadata']['facts_extracted']} facts")


if __name__ == "__main__":
    main()
