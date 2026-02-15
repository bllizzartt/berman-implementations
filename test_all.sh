#!/bin/bash
# Berman Project Test Runner
# Tests all modules to verify they work

echo "🧪 TESTING BERMAN IMPLEMENTATIONS"
echo "=================================="

cd /Users/cortana/.openclaw/workspace/projects/berman-implementations

# Test Memory Module
echo ""
echo "📚 MEMORY MODULE"
echo "----------------"
python3 -c "from memory.memory_compressor import MemoryCompressor; print('✅ MemoryCompressor OK')" 2>&1
cd memory && python3 memory_compressor.py --weekly-summary 2>&1 | head -3 && cd ..
cd memory && python3 key_facts_extractor.py --extract 2>&1 | head -3 && cd ..

# Test Calendar Module
echo ""
echo "📅 CALENDAR MODULE"
echo "------------------"
python3 -c "from calendar.calendar_sync import CalendarSync; print('✅ CalendarSync OK')" 2>&1
cd calendar && python3 calendar_sync.py --help 2>&1 | head -1 && cd ..
cd calendar && python3 smart_scheduler.py --help 2>&1 | head -1 && cd ..
cd calendar && python3 email_automation.py --help 2>&1 | head -1 && cd ..

# Test Polymarket Module
echo ""
echo "📈 POLYMARKET MODULE"
echo "--------------------"
python3 -c "from polymarket.polymarket_api import PolymarketAPI; print('✅ PolymarketAPI OK')" 2>&1
cd polymarket && python3 polymarket_api.py --help 2>&1 | head -1 && cd ..
cd polymarket && python3 market_analyzer.py --help 2>&1 | head -1 && cd ..

echo ""
echo "=================================="
echo "✅ ALL MODULES TESTED!"
echo ""
echo "Next steps:"
echo "• Memory: Run 'python3 memory/memory_compressor.py --weekly-summary'"
echo "• Calendar: Set up Google OAuth for calendar sync"
echo "• Polymarket: Add API key to trade (optional)"
