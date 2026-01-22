"""
Safety Logger for X-Hive
Persistent warning and reminder system to prevent ban incidents.

Features:
- Startup warning banner (NEVER FORGET)
- Daily safety reminders
- Limit approaching alerts
- Weekly usage reports
- Ban incident memorial
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class BanIncident:
    """Ban incident record"""
    date: str  # ISO format
    reason: str
    account: str
    notes: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BanIncident":
        return cls(**data)


class SafetyLogger:
    """
    Safety warning and reminder system.
    
    CRITICAL: This system exists to ensure we NEVER FORGET the ban incident.
    """
    
    # ANSI color codes for terminal
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize safety logger"""
        self.storage_path = Path(storage_path or settings.DATA_PATH) / "safety_incidents.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ban incidents history
        self.incidents: List[BanIncident] = []
        
        # Last reminder time
        self.last_daily_reminder: Optional[datetime] = None
        
        self._load_incidents()
        logger.info("🔔 SafetyLogger initialized")
    
    def _load_incidents(self) -> None:
        """Load ban incidents from disk"""
        try:
            if not self.storage_path.exists():
                logger.info("No incident history found (clean slate)")
                return
            
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            self.incidents = [
                BanIncident.from_dict(inc)
                for inc in data.get("incidents", [])
            ]
            
            last_reminder_str = data.get("last_daily_reminder")
            if last_reminder_str:
                self.last_daily_reminder = datetime.fromisoformat(last_reminder_str)
            
            logger.info(f"📂 Loaded {len(self.incidents)} ban incidents")
        
        except Exception as e:
            logger.error(f"Failed to load incidents: {e}")
            self.incidents = []
    
    def _save_incidents(self) -> None:
        """Save ban incidents to disk"""
        try:
            data = {
                "saved_at": datetime.now().isoformat(),
                "incidents": [inc.to_dict() for inc in self.incidents],
                "last_daily_reminder": self.last_daily_reminder.isoformat() if self.last_daily_reminder else None
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Safety incidents saved")
        
        except Exception as e:
            logger.error(f"Failed to save incidents: {e}")
    
    def record_ban_incident(
        self,
        date: datetime,
        reason: str,
        account: str,
        notes: str = ""
    ) -> None:
        """
        Record a ban incident (MEMORIAL - NEVER FORGET).
        
        Args:
            date: Date of ban
            reason: Reason for ban
            account: Account identifier
            notes: Additional notes
        """
        incident = BanIncident(
            date=date.isoformat(),
            reason=reason,
            account=account,
            notes=notes
        )
        
        self.incidents.append(incident)
        self._save_incidents()
        
        logger.critical(f"🚨 BAN INCIDENT RECORDED: {reason} on {date.date()}")
    
    def print_startup_banner(self) -> None:
        """
        Print startup warning banner.
        
        CRITICAL: Called on EVERY worker startup.
        """
        print("\n" + "=" * 80)
        print(f"{self.BOLD}{self.RED}{'⚠️  X-HIVE SAFETY WARNING  ⚠️':^80}{self.RESET}")
        print("=" * 80)
        
        if self.incidents:
            print(f"\n{self.YELLOW}{self.BOLD}🚨 BAN HISTORY - NEVER FORGET:{self.RESET}\n")
            
            for idx, incident in enumerate(self.incidents, 1):
                incident_date = datetime.fromisoformat(incident.date)
                days_ago = (datetime.now() - incident_date).days
                
                print(f"{self.RED}  {idx}. {incident_date.strftime('%Y-%m-%d')}{self.RESET} "
                      f"({days_ago} days ago)")
                print(f"     Account: {self.YELLOW}{incident.account}{self.RESET}")
                print(f"     Reason: {incident.reason}")
                if incident.notes:
                    print(f"     Notes: {incident.notes}")
                print()
            
            print(f"{self.BOLD}{self.RED}THIS MUST NEVER HAPPEN AGAIN!{self.RESET}\n")
        else:
            print(f"\n{self.GREEN}✅ No ban incidents recorded (yet){self.RESET}\n")
        
        print(f"{self.CYAN}Safety Measures Active:{self.RESET}")
        print(f"  • Rate Limiting: {self.GREEN}✓{self.RESET} (Conservative limits)")
        print(f"  • Human Behavior: {self.GREEN}✓{self.RESET} (Random delays 2-8s)")
        print(f"  • Browser Stealth: {self.GREEN}✓{self.RESET} (Anti-fingerprinting)")
        print(f"  • Manual Approval: {self.YELLOW}○{self.RESET} (Optional - can enable)")
        
        print(f"\n{self.BOLD}Current Limits:{self.RESET}")
        print(f"  • Tweets: {self.CYAN}10/day{self.RESET}, {self.CYAN}3/hour{self.RESET}, min {self.CYAN}10min{self.RESET} interval")
        print(f"  • Replies: {self.CYAN}15/day{self.RESET}, {self.CYAN}5/hour{self.RESET}, min {self.CYAN}5min{self.RESET} interval")
        print(f"  • Likes: {self.CYAN}50/day{self.RESET}, {self.CYAN}20/hour{self.RESET}, min {self.CYAN}2min{self.RESET} interval")
        
        print(f"\n{self.BOLD}{self.YELLOW}⚠️  USE WITH EXTREME CAUTION  ⚠️{self.RESET}")
        print("=" * 80 + "\n")
        
        # Also log to file
        logger.critical("=" * 80)
        logger.critical("X-HIVE STARTUP - SAFETY WARNING DISPLAYED")
        if self.incidents:
            logger.critical(f"Ban incidents on record: {len(self.incidents)}")
        logger.critical("=" * 80)
    
    def check_daily_reminder(self) -> bool:
        """
        Check if daily reminder should be shown.
        
        Returns:
            True if reminder shown, False if already shown today
        """
        now = datetime.now()
        
        # Check if already reminded today
        if self.last_daily_reminder:
            if self.last_daily_reminder.date() == now.date():
                return False
        
        # Show reminder
        self._show_daily_reminder()
        
        # Update last reminder time
        self.last_daily_reminder = now
        self._save_incidents()
        
        return True
    
    def _show_daily_reminder(self) -> None:
        """Show daily safety reminder"""
        print("\n" + "-" * 60)
        print(f"{self.BOLD}{self.CYAN}📅 DAILY SAFETY REMINDER{self.RESET}")
        print("-" * 60)
        
        if self.incidents:
            most_recent = self.incidents[-1]
            incident_date = datetime.fromisoformat(most_recent.date)
            days_ago = (datetime.now() - incident_date).days
            
            print(f"{self.YELLOW}Last ban: {days_ago} days ago{self.RESET}")
            print(f"Reason: {most_recent.reason}")
        
        print(f"\n{self.GREEN}✓{self.RESET} Stay within rate limits")
        print(f"{self.GREEN}✓{self.RESET} Use human-like delays")
        print(f"{self.GREEN}✓{self.RESET} Avoid suspicious patterns")
        print(f"{self.GREEN}✓{self.RESET} Monitor usage statistics")
        print("-" * 60 + "\n")
        
        logger.info("📅 Daily safety reminder displayed")
    
    def alert_approaching_limit(
        self,
        operation_type: str,
        current: int,
        limit: int,
        timeframe: str
    ) -> None:
        """
        Alert when approaching rate limit.
        
        Args:
            operation_type: Type of operation (tweet, like, etc.)
            current: Current usage count
            limit: Maximum limit
            timeframe: Timeframe (hourly, daily)
        """
        percentage = (current / limit) * 100
        
        if percentage >= 90:
            level = "CRITICAL"
            color = self.RED
        elif percentage >= 80:
            level = "WARNING"
            color = self.YELLOW
        else:
            return  # Don't alert below 80%
        
        print(f"\n{color}{self.BOLD}⚠️  {level}: Approaching {timeframe} limit{self.RESET}")
        print(f"{color}{operation_type.upper()}: {current}/{limit} ({percentage:.0f}%){self.RESET}")
        print(f"{self.YELLOW}Recommendation: Slow down or stop {operation_type} operations{self.RESET}\n")
        
        logger.warning(
            f"⚠️ {level}: {operation_type} {timeframe} usage at {percentage:.0f}% "
            f"({current}/{limit})"
        )
    
    def generate_weekly_report(self) -> Dict:
        """
        Generate weekly usage report.
        
        Returns:
            Report data dictionary
        """
        # This would integrate with rate_limiter to get actual stats
        # For now, return placeholder structure
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "last_7_days",
            "ban_incidents": len(self.incidents),
            "days_since_last_ban": None,
            "safety_score": 100,  # 0-100 (lower = more risky behavior)
            "recommendations": []
        }
        
        if self.incidents:
            last_ban = datetime.fromisoformat(self.incidents[-1].date)
            days_since = (datetime.now() - last_ban).days
            report["days_since_last_ban"] = days_since
            
            if days_since < 30:
                report["safety_score"] = max(0, 100 - (30 - days_since) * 3)
                report["recommendations"].append("⚠️ Recent ban - extreme caution advised")
        
        return report
    
    def print_weekly_report(self) -> None:
        """Print weekly safety report"""
        report = self.generate_weekly_report()
        
        print("\n" + "=" * 60)
        print(f"{self.BOLD}{self.CYAN}📊 WEEKLY SAFETY REPORT{self.RESET}")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Period: Last 7 days\n")
        
        # Safety score
        score = report["safety_score"]
        if score >= 90:
            score_color = self.GREEN
            score_label = "EXCELLENT"
        elif score >= 70:
            score_color = self.CYAN
            score_label = "GOOD"
        elif score >= 50:
            score_color = self.YELLOW
            score_label = "CAUTION"
        else:
            score_color = self.RED
            score_label = "DANGER"
        
        print(f"Safety Score: {score_color}{self.BOLD}{score}/100{self.RESET} ({score_label})")
        
        # Ban history
        if report["days_since_last_ban"] is not None:
            days = report["days_since_last_ban"]
            print(f"Days since last ban: {self.YELLOW}{days}{self.RESET}")
        else:
            print(f"Days since last ban: {self.GREEN}N/A (no bans){self.RESET}")
        
        # Recommendations
        if report["recommendations"]:
            print(f"\n{self.YELLOW}Recommendations:{self.RESET}")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        
        print("=" * 60 + "\n")
        
        logger.info("📊 Weekly safety report generated")
    
    def get_memorial_message(self) -> Optional[str]:
        """
        Get memorial message for UI display.
        
        Returns:
            Message string if incidents exist, None otherwise
        """
        if not self.incidents:
            return None
        
        most_recent = self.incidents[-1]
        incident_date = datetime.fromisoformat(most_recent.date)
        days_ago = (datetime.now() - incident_date).days
        
        return (
            f"⚠️ Account was banned {days_ago} days ago "
            f"({incident_date.strftime('%Y-%m-%d')}). "
            f"Reason: {most_recent.reason}. USE EXTREME CAUTION."
        )


# Singleton instance
_safety_logger_instance: Optional[SafetyLogger] = None


def get_safety_logger() -> SafetyLogger:
    """Get singleton safety logger instance"""
    global _safety_logger_instance
    if _safety_logger_instance is None:
        _safety_logger_instance = SafetyLogger()
    return _safety_logger_instance


def record_xideai_ban_incident():
    """
    Helper function to record the XiDeAI Pro ban incident.
    Call this ONCE during setup.
    """
    logger_instance = get_safety_logger()
    
    # Record the actual ban incident (adjust date if needed)
    ban_date = datetime(2026, 1, 21)  # Adjust to actual ban date
    
    logger_instance.record_ban_incident(
        date=ban_date,
        reason="Automation detection - XiDeAI Pro usage",
        account="X account (suspended)",
        notes="Bot-like behavior detected. Appeal submitted. "
               "Implemented comprehensive anti-detection system to prevent recurrence."
    )
    
    print(f"{SafetyLogger.GREEN}✅ Ban incident recorded in safety system{SafetyLogger.RESET}")
