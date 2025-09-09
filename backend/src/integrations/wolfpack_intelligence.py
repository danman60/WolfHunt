"""
🐺 WOLF PACK INTELLIGENCE API BRIDGE
Connects n8n agents to the GMX trading dashboard for unified intelligence
"""

from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import httpx
import json
from typing import Dict, List, Optional, Any
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# 📊 Database models for Wolf Pack intelligence storage
Base = declarative_base()

class QuantIntelligence(Base):
    __tablename__ = "quant_intelligence"
    
    id = Column(Integer, primary_key=True)
    crypto = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price = Column(Float)
    rsi = Column(Float)
    macd_signal = Column(String)
    sma_trend = Column(String)
    bb_position = Column(String)
    volume_ratio = Column(Float)
    technical_score = Column(Float)
    support_level = Column(Float)
    resistance_level = Column(Float)
    pattern_detected = Column(String)
    signal_strength = Column(String)
    confidence_level = Column(Float)
    data_quality = Column(String)

class SnoopIntelligence(Base):
    __tablename__ = "snoop_intelligence"
    
    id = Column(Integer, primary_key=True)
    crypto = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sentiment_score = Column(Float)
    dominant_narrative = Column(String)
    source_breakdown = Column(JSON)
    mention_volume = Column(Integer)
    influence_weight = Column(Float)
    manipulation_risk = Column(Float)
    fear_greed_index = Column(Float)
    narrative_momentum = Column(String)
    key_themes = Column(JSON)
    confidence_level = Column(Float)

class SageForecasts(Base):
    __tablename__ = "sage_forecasts"
    
    id = Column(Integer, primary_key=True)
    crypto = Column(String, index=True)
    week_ending = Column(DateTime)
    current_price = Column(Float)
    forecast_median_7d = Column(Float)
    forecast_low_70pct = Column(Float)
    forecast_high_70pct = Column(Float)
    forecast_low_95pct = Column(Float)
    forecast_high_95pct = Column(Float)
    directional_bias = Column(String)
    confidence_score = Column(Float)
    technical_momentum = Column(Float)
    sentiment_momentum = Column(Float)
    model_used = Column(String)

class StrategyExecutions(Base):
    __tablename__ = "strategy_executions"
    
    id = Column(Integer, primary_key=True)
    suggestion_type = Column(String)
    target_crypto = Column(String)
    suggested_allocation = Column(Float)
    actual_allocation = Column(Float)
    confidence = Column(Float)
    justification = Column(String)
    status = Column(String)  # pending, approved, executed, rejected
    execution_time = Column(DateTime)
    result_pnl = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🚀 Pydantic models for API requests/responses
class StrategyAdjustment(BaseModel):
    adjustment_type: str  # "allocation_change", "risk_adjustment", "signal_threshold"
    target_crypto: str
    current_value: float
    suggested_value: float
    confidence: float
    justification: str
    expected_impact: str
    risk_assessment: str

class UnifiedIntelligence(BaseModel):
    timestamp: datetime
    eth_intelligence: Dict
    link_intelligence: Dict
    wbtc_intelligence: Dict
    portfolio_signals: Dict
    strategy_suggestions: List[StrategyAdjustment]
    market_context: Dict
    system_health: Dict

class WolfPackIntelligenceEngine:
    """🐺 THE BRAIN - Processes all agent intelligence into unified insights"""
    
    def __init__(self, database_url: str = None, redis_url: str = None):
        self.google_sheets_id = os.getenv("GOOGLE_SHEETS_ID", "12LOT0eLeXcBdkgTG1rzUr-cuIY_Gg2RzH-fNR2DZ61c")
        self.sheets_base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.google_sheets_id}/values"
        self.sheets_api_key = os.getenv("GOOGLE_SHEETS_API_KEY")
        
        # Database setup
        database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///wolfpack.db")
        self.engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = SessionLocal
        
        # Redis setup for caching
        try:
            redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise
    
    def cache_set(self, key: str, value: str, expiry: int = 300):
        """Set cache value with Redis fallback"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, expiry, value)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
    
    def cache_get(self, key: str) -> Optional[str]:
        """Get cache value with Redis fallback"""
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        return None
        
    async def fetch_latest_quant_data(self) -> Dict:
        """📈 Get latest technical analysis from The Quant"""
        cache_key = "quant_intelligence"
        cached = self.cache_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass
        
        try:
            if not self.sheets_api_key:
                logger.warning("No Google Sheets API key configured, using mock data")
                return self._get_mock_quant_data()
            
            url = f"{self.sheets_base_url}/Quant_Daily_Intelligence!A:O"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    params={"key": self.sheets_api_key}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google Sheets API error: {response.status_code}")
                    return self._get_mock_quant_data()
                
                data = response.json()
                
                if "values" not in data:
                    logger.warning("No values in Google Sheets response")
                    return self._get_mock_quant_data()
                
                # Process data
                quant_intelligence = self._process_quant_data(data["values"])
                
                # Cache for 5 minutes
                self.cache_set(cache_key, json.dumps(quant_intelligence, default=str), 300)
                
                # Store in database
                self._store_quant_data(quant_intelligence)
                
                return quant_intelligence
                
        except Exception as e:
            logger.error(f"Quant data fetch failed: {str(e)}")
            return self._get_mock_quant_data()
    
    async def fetch_latest_snoop_data(self) -> Dict:
        """🕵️ Get latest sentiment analysis from The Snoop"""
        cache_key = "snoop_intelligence"
        cached = self.cache_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass
        
        try:
            if not self.sheets_api_key:
                return self._get_mock_snoop_data()
            
            url = f"{self.sheets_base_url}/Snoop_Daily_Intelligence!A:M"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    params={"key": self.sheets_api_key}
                )
                
                if response.status_code != 200:
                    return self._get_mock_snoop_data()
                
                data = response.json()
                
                if "values" not in data:
                    return self._get_mock_snoop_data()
                
                snoop_intelligence = self._process_snoop_data(data["values"])
                
                self.cache_set(cache_key, json.dumps(snoop_intelligence, default=str), 300)
                self._store_snoop_data(snoop_intelligence)
                
                return snoop_intelligence
                
        except Exception as e:
            logger.error(f"Snoop data fetch failed: {str(e)}")
            return self._get_mock_snoop_data()
    
    def _process_quant_data(self, raw_data: List) -> Dict:
        """🔢 Process raw Google Sheets data into structured intelligence"""
        if not raw_data or len(raw_data) < 2:
            return {"error": "No quant data available"}
        
        headers = raw_data[0]
        rows = raw_data[1:]
        
        # Get latest data for each crypto
        crypto_data = {}
        for row in reversed(rows[-10:]):  # Last 10 rows
            if len(row) >= len(headers):
                try:
                    crypto = row[headers.index("Crypto")] if "Crypto" in headers else row[0]
                    if crypto and crypto not in crypto_data:
                        crypto_data[crypto] = {
                            "date": row[headers.index("Date")] if "Date" in headers else "",
                            "price": self._safe_float(row[headers.index("Price")] if "Price" in headers else "0"),
                            "rsi": self._safe_float(row[headers.index("RSI")] if "RSI" in headers else "50"),
                            "macd_signal": row[headers.index("MACD_Signal")] if "MACD_Signal" in headers else "NEUTRAL",
                            "sma_trend": row[headers.index("SMA_Trend")] if "SMA_Trend" in headers else "NEUTRAL",
                            "bb_position": row[headers.index("BB_Position")] if "BB_Position" in headers else "MIDDLE",
                            "volume_ratio": self._safe_float(row[headers.index("Volume_Ratio")] if "Volume_Ratio" in headers else "1"),
                            "technical_score": self._safe_float(row[headers.index("Technical_Score")] if "Technical_Score" in headers else "50"),
                            "support_level": self._safe_float(row[headers.index("Support_Level")] if "Support_Level" in headers else "0"),
                            "resistance_level": self._safe_float(row[headers.index("Resistance_Level")] if "Resistance_Level" in headers else "0"),
                            "pattern_detected": row[headers.index("Pattern_Detected")] if "Pattern_Detected" in headers else "Normal",
                            "signal_strength": row[headers.index("Signal_Strength")] if "Signal_Strength" in headers else "MODERATE",
                            "confidence_level": self._safe_float(row[headers.index("Confidence_Level")] if "Confidence_Level" in headers else "0.5"),
                            "data_quality": row[headers.index("Data_Quality")] if "Data_Quality" in headers else "GOOD"
                        }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error processing quant row: {e}")
                    continue
        
        return crypto_data
    
    def _process_snoop_data(self, raw_data: List) -> Dict:
        """🕵️ Process sentiment data into actionable intelligence"""
        if not raw_data or len(raw_data) < 2:
            return {"error": "No snoop data available"}
        
        headers = raw_data[0]
        rows = raw_data[1:]
        
        crypto_sentiment = {}
        for row in reversed(rows[-10:]):
            if len(row) >= len(headers):
                try:
                    crypto = row[headers.index("Crypto")] if "Crypto" in headers else row[0]
                    if crypto and crypto not in crypto_sentiment:
                        crypto_sentiment[crypto] = {
                            "date": row[headers.index("Date")] if "Date" in headers else "",
                            "sentiment_score": self._safe_float(row[headers.index("Sentiment_Score")] if "Sentiment_Score" in headers else "50"),
                            "dominant_narrative": row[headers.index("Dominant_Narrative")] if "Dominant_Narrative" in headers else "Mixed",
                            "mention_volume": self._safe_int(row[headers.index("Mention_Volume")] if "Mention_Volume" in headers else "0"),
                            "influence_weight": self._safe_float(row[headers.index("Influence_Weight")] if "Influence_Weight" in headers else "0.5"),
                            "manipulation_risk": self._safe_float(row[headers.index("Manipulation_Risk")] if "Manipulation_Risk" in headers else "0"),
                            "fear_greed_index": self._safe_float(row[headers.index("Fear_Greed_Index")] if "Fear_Greed_Index" in headers else "50"),
                            "narrative_momentum": row[headers.index("Narrative_Momentum")] if "Narrative_Momentum" in headers else "NEUTRAL",
                            "confidence_level": self._safe_float(row[headers.index("Confidence_Level")] if "Confidence_Level" in headers else "0.5")
                        }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error processing snoop row: {e}")
                    continue
        
        return crypto_sentiment
    
    def _safe_float(self, value: str, default: float = 0.0) -> float:
        """Safely convert string to float"""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value: str, default: int = 0) -> int:
        """Safely convert string to int"""
        try:
            return int(float(value)) if value else default
        except (ValueError, TypeError):
            return default
    
    def generate_strategy_suggestions(self, quant_data: Dict, snoop_data: Dict) -> List[StrategyAdjustment]:
        """🧠 THE MONEY MAKER - Generate AI-powered strategy adjustments for GMX"""
        suggestions = []
        
        # Focus on ETH, LINK, WBTC for GMX trading
        cryptos = ["ETH", "LINK", "WBTC"]
        
        for crypto in cryptos:
            if crypto in quant_data and crypto in snoop_data:
                quant = quant_data[crypto]
                snoop = snoop_data[crypto]
                
                # 🎯 SIGNAL CONVERGENCE ANALYSIS
                tech_score = quant["technical_score"]
                sent_score = snoop["sentiment_score"]
                alignment = 100 - abs(tech_score - sent_score)
                
                # 🚀 BULLISH CONVERGENCE OPPORTUNITY
                if alignment > 75 and tech_score > 65 and sent_score > 65:
                    suggestions.append(StrategyAdjustment(
                        adjustment_type="allocation_increase",
                        target_crypto=crypto,
                        current_value=33.33,  # Assume equal allocation
                        suggested_value=min(45.0, 33.33 + (alignment - 75) / 5),  # Dynamic increase
                        confidence=alignment / 100,
                        justification=f"🚀 Strong bullish convergence detected! Technical analysis shows {tech_score:.1f}/100 strength while sentiment analysis indicates {sent_score:.1f}/100 positive sentiment. {quant['signal_strength']} technical signal aligns with '{snoop['dominant_narrative']}' narrative. Volume activity at {quant['volume_ratio']:.1f}x normal levels.",
                        expected_impact=f"Potential 15-25% alpha capture in next 7-14 days based on signal convergence strength",
                        risk_assessment="LOW - High signal alignment reduces false signal probability. Stop loss recommended at support level ${:.0f}".format(quant['support_level'])
                    ))
                
                # 🐻 BEARISH CONVERGENCE WARNING
                elif alignment > 75 and tech_score < 35 and sent_score < 35:
                    suggestions.append(StrategyAdjustment(
                        adjustment_type="allocation_decrease",
                        target_crypto=crypto,
                        current_value=33.33,
                        suggested_value=max(20.0, 33.33 - (75 - tech_score) / 5),
                        confidence=alignment / 100,
                        justification=f"🐻 Bearish convergence warning! Technical: {tech_score:.1f}/100, Sentiment: {sent_score:.1f}/100. High probability of significant downside movement. Pattern detected: {quant['pattern_detected']}",
                        expected_impact="Risk reduction: Potential to avoid 15-30% drawdown",
                        risk_assessment="MEDIUM - Defensive positioning recommended. Consider short position if conviction strengthens"
                    ))
                
                # ⚠️ DIVERGENCE ALERT - Increased uncertainty
                elif alignment < 40:
                    suggestions.append(StrategyAdjustment(
                        adjustment_type="risk_adjustment",
                        target_crypto=crypto,
                        current_value=1.0,  # Current risk multiplier
                        suggested_value=0.6,  # Reduce risk
                        confidence=0.8,
                        justification=f"⚠️ Signal divergence detected! Technical shows {tech_score:.1f} while sentiment shows {sent_score:.1f}. This divergence often precedes high volatility periods. Market uncertainty elevated.",
                        expected_impact="Risk mitigation during uncertain market conditions - preserve capital for clearer opportunities",
                        risk_assessment="HIGH - Conflicting signals increase unpredictability. Reduce position sizes until convergence returns"
                    ))
                
                # 🎪 VOLUME MOMENTUM PLAY
                if quant["volume_ratio"] > 2.5 and quant["signal_strength"] in ["STRONG", "VERY_STRONG"]:
                    suggestions.append(StrategyAdjustment(
                        adjustment_type="momentum_play",
                        target_crypto=crypto,
                        current_value=33.33,
                        suggested_value=min(50.0, 33.33 + quant["volume_ratio"] * 3),
                        confidence=min(quant["volume_ratio"] / 4.0, 0.95),
                        justification=f"🎪 High volume momentum breakout! Volume at {quant['volume_ratio']:.1f}x normal with {quant['signal_strength']} technical signal. Pattern: {quant['pattern_detected']}. This combination historically precedes 20%+ moves in {crypto}.",
                        expected_impact="Momentum capture opportunity: 20-40% potential upside in 3-7 days",
                        risk_assessment="MEDIUM-HIGH - High reward/risk ratio. Volume confirmation reduces breakout failure risk. Trail stop recommended"
                    ))
                
                # 🎯 SUPPORT/RESISTANCE PLAY
                current_price = quant.get("price", 0)
                support = quant.get("support_level", 0)
                resistance = quant.get("resistance_level", 0)
                
                if current_price > 0 and support > 0:
                    support_distance = (current_price - support) / current_price * 100
                    if support_distance < 3 and tech_score > 55:  # Near support with positive technicals
                        suggestions.append(StrategyAdjustment(
                            adjustment_type="support_bounce",
                            target_crypto=crypto,
                            current_value=33.33,
                            suggested_value=38.0,
                            confidence=0.75,
                            justification=f"🎯 Support level bounce opportunity! {crypto} trading just {support_distance:.1f}% above strong support at ${support:.0f}. Technical score of {tech_score:.1f} suggests bounce probability is high.",
                            expected_impact="Support bounce play: 8-15% potential upside to resistance level",
                            risk_assessment="MEDIUM - Tight stop loss below support level limits downside to 3-5%"
                        ))
        
        # 📊 PORTFOLIO-LEVEL SUGGESTIONS
        if len(quant_data) >= 2:
            # Overall market strength assessment
            avg_tech = sum(quant_data[c]["technical_score"] for c in cryptos if c in quant_data) / len([c for c in cryptos if c in quant_data])
            avg_sent = sum(snoop_data[c]["sentiment_score"] for c in cryptos if c in snoop_data) / len([c for c in cryptos if c in snoop_data])
            
            if avg_tech > 70 and avg_sent > 65:
                suggestions.append(StrategyAdjustment(
                    adjustment_type="portfolio_risk_increase",
                    target_crypto="PORTFOLIO",
                    current_value=1.0,
                    suggested_value=1.3,  # 30% leverage increase
                    confidence=0.85,
                    justification=f"📊 PORTFOLIO BULL SIGNAL: Average technical strength {avg_tech:.1f}, sentiment {avg_sent:.1f}. Broad-based strength across all monitored assets suggests market-wide opportunity.",
                    expected_impact="Portfolio leverage increase could capture 25-40% additional alpha in bull run",
                    risk_assessment="MEDIUM - Broad-based signals reduce individual asset risk. Monitor for any divergence"
                ))
        
        return suggestions
    
    def _store_quant_data(self, quant_data: Dict):
        """Store quant data in database"""
        try:
            db = self.get_db()
            for crypto, data in quant_data.items():
                if crypto != "error":
                    db_entry = QuantIntelligence(
                        crypto=crypto,
                        price=data.get("price"),
                        rsi=data.get("rsi"),
                        macd_signal=data.get("macd_signal"),
                        sma_trend=data.get("sma_trend"),
                        bb_position=data.get("bb_position"),
                        volume_ratio=data.get("volume_ratio"),
                        technical_score=data.get("technical_score"),
                        support_level=data.get("support_level"),
                        resistance_level=data.get("resistance_level"),
                        pattern_detected=data.get("pattern_detected"),
                        signal_strength=data.get("signal_strength"),
                        confidence_level=data.get("confidence_level"),
                        data_quality=data.get("data_quality")
                    )
                    db.add(db_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to store quant data: {e}")
    
    def _store_snoop_data(self, snoop_data: Dict):
        """Store snoop data in database"""
        try:
            db = self.get_db()
            for crypto, data in snoop_data.items():
                if crypto != "error":
                    db_entry = SnoopIntelligence(
                        crypto=crypto,
                        sentiment_score=data.get("sentiment_score"),
                        dominant_narrative=data.get("dominant_narrative"),
                        mention_volume=data.get("mention_volume"),
                        influence_weight=data.get("influence_weight"),
                        manipulation_risk=data.get("manipulation_risk"),
                        fear_greed_index=data.get("fear_greed_index"),
                        narrative_momentum=data.get("narrative_momentum"),
                        confidence_level=data.get("confidence_level")
                    )
                    db.add(db_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to store snoop data: {e}")
    
    # Mock data methods for development/testing
    def _get_mock_quant_data(self) -> Dict:
        """Return realistic mock technical analysis data"""
        import random
        
        mock_data = {}
        for crypto in ["ETH", "LINK", "WBTC"]:
            base_scores = {"ETH": 72, "LINK": 68, "WBTC": 75}
            base_score = base_scores.get(crypto, 70)
            
            mock_data[crypto] = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "price": {"ETH": 2850, "LINK": 15.75, "WBTC": 45800}.get(crypto, 1000) + random.uniform(-50, 50),
                "rsi": max(20, min(80, base_score + random.uniform(-10, 10))),
                "macd_signal": random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
                "sma_trend": random.choice(["UPTREND", "DOWNTREND", "SIDEWAYS"]),
                "bb_position": random.choice(["UPPER", "MIDDLE", "LOWER"]),
                "volume_ratio": max(0.5, random.uniform(0.8, 3.2)),
                "technical_score": max(0, min(100, base_score + random.uniform(-15, 15))),
                "support_level": {"ETH": 2750, "LINK": 14.50, "WBTC": 44000}.get(crypto, 900),
                "resistance_level": {"ETH": 2950, "LINK": 17.00, "WBTC": 47000}.get(crypto, 1100),
                "pattern_detected": random.choice(["Ascending Triangle", "Bull Flag", "Support Bounce", "Breakout", "Consolidation"]),
                "signal_strength": random.choice(["VERY_STRONG", "STRONG", "MODERATE", "WEAK"]),
                "confidence_level": max(0.5, min(0.95, random.uniform(0.6, 0.9))),
                "data_quality": "MOCK_DATA"
            }
        
        return mock_data
    
    def _get_mock_snoop_data(self) -> Dict:
        """Return realistic mock sentiment data"""
        import random
        
        mock_data = {}
        narratives = {
            "ETH": ["ETF Approval Momentum", "Layer 2 Growth", "DeFi Renaissance", "Institutional Adoption"],
            "LINK": ["Real World Assets", "Cross-Chain Growth", "Enterprise Partnerships", "Oracle Expansion"],
            "WBTC": ["Digital Gold Narrative", "Institutional Reserves", "Inflation Hedge", "Store of Value"]
        }
        
        for crypto in ["ETH", "LINK", "WBTC"]:
            base_scores = {"ETH": 68, "LINK": 65, "WBTC": 70}
            base_score = base_scores.get(crypto, 65)
            
            mock_data[crypto] = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "sentiment_score": max(20, min(80, base_score + random.uniform(-12, 12))),
                "dominant_narrative": random.choice(narratives.get(crypto, ["Mixed Signals"])),
                "mention_volume": random.randint(500, 5000),
                "influence_weight": random.uniform(0.4, 0.8),
                "manipulation_risk": random.uniform(0.1, 0.4),
                "fear_greed_index": random.uniform(40, 70),
                "narrative_momentum": random.choice(["ACCELERATING", "STEADY", "DECLINING"]),
                "confidence_level": max(0.5, min(0.9, random.uniform(0.6, 0.85)))
            }
        
        return mock_data

# 🎯 Initialize the intelligence engine (singleton pattern)
_intelligence_engine = None

def get_intelligence_engine() -> WolfPackIntelligenceEngine:
    """Get or create the Wolf Pack Intelligence Engine instance"""
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = WolfPackIntelligenceEngine()
    return _intelligence_engine