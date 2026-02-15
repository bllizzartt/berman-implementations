# 🧠 Berman Implementations

Matthew Berman's AI strategies implemented: memory management, calendar automation, Polymarket trading.

## 📚 Modules

### 1. Memory System (`memory/`)

**Problem:** Context windows compress memory, lose fidelity

**Solution:**
- Weekly compression of old memories
- Key facts extraction to long-term storage
- Semantic search across all memories

```bash
cd memory

# Compress memories older than 4 weeks
python3 memory_compressor.py --weekly-summary

# Extract key facts
python3 key_facts_extractor.py --extract

# Search memories
python3 memory_search.py "your query"
```

### 2. Calendar Automation (`calendar/`)

**Features:**
- Google Calendar sync
- Smart scheduling (high energy = hard tasks)
- Email triage

```bash
cd calendar

# View upcoming events
python3 calendar_sync.py --events 7

# Optimize your schedule
python3 smart_scheduler.py --optimize

# Triage unread emails
python3 email_automation.py --triage
```

**Setup:** Requires Google OAuth credentials

### 3. Polymarket Trading (`polymarket/`)

**Features:**
- Market analysis
- Automated trading (with safety limits)
- Portfolio tracking

```bash
cd polymarket

# List markets
python3 polymarket_api.py --markets

# Find opportunities
python3 market_analyzer.py --opportunities
```

**Safety Limits:**
- Max 5% per trade
- €50 daily loss limit
- Manual approval >€100

**Setup:** Add Polymarket API key

## 🧪 Test Everything

```bash
./test_all.sh
```

## 🎯 Next Steps

1. **Memory:** Set up weekly cron job for compression
2. **Calendar:** Connect Google OAuth
3. **Polymarket:** Add API key, start with small trades

## 📖 Berman's Strategies

Based on:
- Isolated AI environments (✅ dedicated Mac Mini)
- Persistent memory management
- Integration = power
- "Vibe coding" with AI assistants

---
Implement cutting-edge AI strategies ⚡
