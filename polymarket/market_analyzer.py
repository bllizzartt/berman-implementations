"""
Market Analyzer - Analyze prediction markets

Provides analysis and signals for Polymarket prediction markets.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class MarketAnalyzer:
    """Analyze prediction markets"""
    
    def __init__(self, api=None):
        self.api = api
        self.workspace_path = "/Users/cortana/.openclaw/workspace"
        
        # Analysis parameters
        self.min_volume_threshold = 100000  # $100K minimum volume
        self.min_confidence = 0.60  # 60% minimum confidence
        
        # Market categories for filtering
        self.high_activity_categories = ["Politics", "Crypto", "Economy"]
    
    def analyze_market(self, market: Dict) -> Dict:
        """Analyze a single market"""
        analysis = {
            "market_id": market.get("id"),
            "question": market.get("question"),
            "current_probability": market.get("probability", 0),
            "volume": market.get("volume", 0),
            "timestamp": datetime.now().isoformat(),
            "signals": [],
            "metrics": {},
            "recommendation": None
        }
        
        # Calculate metrics
        analysis["metrics"] = self._calculate_metrics(market)
        
        # Generate signals
        analysis["signals"] = self._generate_signals(market, analysis["metrics"])
        
        # Determine recommendation
        analysis["recommendation"] = self._get_recommendation(market, analysis["signals"], analysis["metrics"])
        
        return analysis
    
    def _calculate_metrics(self, market: Dict) -> Dict:
        """Calculate market metrics"""
        prob = market.get("probability", 0)
        volume = market.get("volume", 0)
        
        # Volatility estimate (based on probability distance from 50%)
        distance_from_50 = abs(prob - 0.5)
        volatility_score = 1 - (distance_from_50 * 2)  # Higher = more uncertain
        
        # Liquidity score (based on volume)
        liquidity_score = min(1.0, volume / 1000000)  # Cap at $1M
        
        # Market maturity (based on volume thresholds)
        if volume > 1000000:
            maturity = "mature"
        elif volume > 100000:
            maturity = "growing"
        else:
            maturity = "new"
        
        return {
            "volatility_score": round(volatility_score, 3),
            "liquidity_score": round(liquidity_score, 3),
            "distance_from_50": round(distance_from_50, 3),
            "maturity": maturity,
            "implied_odds": round(prob / (1 - prob) if prob > 0 and prob < 1 else 0, 2)
        }
    
    def _generate_signals(self, market: Dict, metrics: Dict) -> List[Dict]:
        """Generate trading signals"""
        signals = []
        prob = market.get("probability", 0)
        volume = market.get("volume", 0)
        
        # High volume signal
        if volume > 500000:
            signals.append({
                "type": "high_volume",
                "direction": "neutral",
                "strength": "strong",
                "message": f"High trading volume (${volume:,.0f})"
            })
        
        # Strong conviction signal
        if prob > 0.80 or prob < 0.20:
            signals.append({
                "type": "strong_conviction",
                "direction": "long" if prob > 0.5 else "short",
                "strength": "strong",
                "message": f"Strong market conviction ({prob:.0%})"
            })
        
        # Near 50% signal (uncertainty)
        if 0.45 < prob < 0.55:
            signals.append({
                "type": "uncertainty",
                "direction": "neutral",
                "strength": "medium",
                "message": "Market uncertain - wait for clarity"
            })
        
        # Volume trend signal (would need historical data)
        # This is a placeholder
        if volume > self.min_volume_threshold:
            signals.append({
                "type": "liquid",
                "direction": "neutral",
                "strength": "medium",
                "message": "Sufficient liquidity for trading"
            })
        
        return signals
    
    def _get_recommendation(self, market: Dict, signals: List[Dict], metrics: Dict) -> Dict:
        """Get trading recommendation"""
        prob = market.get("probability", 0)
        volume = market.get("volume", 0)
        
        recommendation = {
            "action": "watch",
            "confidence": 0,
            "reasoning": [],
            "risk_level": "medium"
        }
        
        # Check volume threshold
        if volume < self.min_volume_threshold:
            recommendation["action"] = "avoid"
            recommendation["reasoning"].append("Volume too low")
            return recommendation
        
        # Strong conviction with high volume
        if (prob > 0.75 or prob < 0.25) and volume > self.min_volume_threshold:
            recommendation["action"] = "consider_buy"
            recommendation["confidence"] = 0.7
            recommendation["reasoning"].append("Strong conviction with good volume")
            recommendation["risk_level"] = "low"
        
        # Moderate conviction
        elif (prob > 0.65 or prob < 0.35) and volume > self.min_volume_threshold * 0.5:
            recommendation["action"] = "watch"
            recommendation["confidence"] = 0.4
            recommendation["reasoning"].append("Moderate signal, wait for better entry")
            recommendation["risk_level"] = "medium"
        
        # Uncertain market
        else:
            recommendation["action"] = "watch"
            recommendation["confidence"] = 0.2
            recommendation["reasoning"].append("Market too uncertain")
            recommendation["risk_level"] = "high"
        
        return recommendation
    
    def analyze_all_markets(self, markets: List[Dict] = None) -> List[Dict]:
        """Analyze all available markets"""
        if markets is None:
            if self.api:
                markets = self.api.get_markets()
            else:
                # Use sample markets
                markets = self._get_sample_markets()
        
        analyses = []
        for market in markets:
            analysis = self.analyze_market(market)
            analyses.append(analysis)
        
        # Sort by volume
        analyses.sort(key=lambda x: x.get("volume", 0), reverse=True)
        
        return analyses
    
    def find_opportunities(self, markets: List[Dict] = None) -> List[Dict]:
        """Find trading opportunities"""
        analyses = self.analyze_all_markets(markets)
        
        opportunities = []
        for analysis in analyses:
            rec = analysis.get("recommendation", {})
            if rec.get("action") in ["consider_buy", "consider_sell"]:
                opportunities.append({
                    **analysis,
                    "expected_return": self._estimate_return(analysis)
                })
        
        return opportunities
    
    def _estimate_return(self, analysis: Dict) -> float:
        """Estimate potential return"""
        prob = analysis.get("current_probability", 0.5)
        metrics = analysis.get("metrics", {})
        
        # Simple estimation: if probability moves to 0.8
        if prob > 0.5:
            return round((0.8 - prob) * 100, 1)  # Percentage points
        else:
            return round((0.2 - prob) * 100, 1)
    
    def get_market_summary(self) -> Dict:
        """Get summary of all markets"""
        if self.api:
            markets = self.api.get_markets()
        else:
            markets = self._get_sample_markets()
        
        analyses = self.analyze_all_markets(markets)
        
        # Categorize
        by_category = {}
        by_recommendation = {
            "consider_buy": 0,
            "consider_sell": 0,
            "watch": 0,
            "avoid": 0
        }
        
        for analysis in analyses:
            # By recommendation
            rec = analysis.get("recommendation", {}).get("action", "watch")
            if rec in by_recommendation:
                by_recommendation[rec] += 1
        
        return {
            "total_markets": len(analyses),
            "by_recommendation": by_recommendation,
            "timestamp": datetime.now().isoformat()
        }
    
    def compare_markets(self, market_ids: List[str]) -> Dict:
        """Compare multiple markets"""
        comparisons = []
        
        for mid in market_ids:
            if self.api:
                market = self.api.get_market_details(mid)
            else:
                market = self._get_sample_markets()[0]
            
            analysis = self.analyze_market(market)
            comparisons.append(analysis)
        
        return {
            "markets": comparisons,
            "best_opportunity": max(comparisons, 
                                   key=lambda x: x.get("recommendation", {}).get("confidence", 0))
            if comparisons else None
        }
    
    def _get_sample_markets(self) -> List[Dict]:
        """Get sample markets"""
        return [
            {
                "id": "mkt_001",
                "question": "Who will win the 2024 US Presidential Election?",
                "probability": 0.52,
                "volume": 125000000,
                "categories": ["Politics", "Elections"]
            },
            {
                "id": "mkt_002",
                "question": "Will Bitcoin exceed $150,000 by end of 2025?",
                "probability": 0.35,
                "volume": 2500000,
                "categories": ["Crypto", "Bitcoin"]
            }
        ]


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Market Analyzer")
    parser.add_argument("--analyze", type=str, help="Analyze specific market")
    parser.add_argument("--all", action="store_true", help="Analyze all markets")
    parser.add_argument("--opportunities", action="store_true", help="Find opportunities")
    parser.add_argument("--summary", action="store_true", help="Show market summary")
    parser.add_argument("--compare", nargs="+", help="Compare markets")
    
    args = parser.parse_args()
    
    analyzer = MarketAnalyzer()
    
    if args.all:
        analyses = analyzer.analyze_all_markets()
        print("\n📊 Market Analysis")
        for a in analyses[:10]:
            rec = a.get("recommendation", {})
            print(f"\n{a.get('question', 'Unknown')[:50]}...")
            print(f"  Price: {a.get('current_probability', 0):.2%} | Volume: ${a.get('volume', 0):,.0f}")
            print(f"  Action: {rec.get('action', 'watch')} | Risk: {rec.get('risk_level', 'unknown')}")
            for sig in a.get('signals', [])[:2]:
                print(f"  📍 {sig['message']}")
    elif args.opportunities:
        opportunities = analyzer.find_opportunities()
        if opportunities:
            print("\n🎯 Trading Opportunities")
            for o in opportunities:
                print(f"\n  {o.get('question', 'Unknown')[:50]}...")
                print(f"  Action: {o.get('recommendation', {}).get('action', 'watch')}")
                print(f"  Expected Return: {o.get('expected_return', 0)}%")
        else:
            print("\nNo clear opportunities found")
    elif args.summary:
        summary = analyzer.get_market_summary()
        print("\n📊 Market Summary")
        print(f"Total Markets: {summary['total_markets']}")
        print(f"Consider Buy: {summary['by_recommendation'].get('consider_buy', 0)}")
        print(f"Watch: {summary['by_recommendation'].get('watch', 0)}")
        print(f"Avoid: {summary['by_recommendation'].get('avoid', 0)}")
    elif args.compare:
        result = analyzer.compare_markets(args.compare)
        print(f"\n📈 Comparison of {len(result.get('markets', []))} markets")


if __name__ == "__main__":
    main()
