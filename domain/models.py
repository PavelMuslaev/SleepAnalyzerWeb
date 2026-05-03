# domain/models.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class SleepRecord:
    date: datetime.date
    sleep_start: datetime.time
    sleep_end: datetime.time
    deep_sleep_minutes: float
    light_sleep_minutes: float
    rem_minutes: float
    awakenings: int

    @property
    def total_sleep_minutes(self) -> float:
        start_dt = datetime.combine(self.date, self.sleep_start)
        end_dt = datetime.combine(self.date, self.sleep_end)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        return (end_dt - start_dt).total_seconds() / 60.0

    @property
    def sleep_efficiency(self) -> float:
        if self.total_sleep_minutes == 0:
            return 0.0
        return ((
                            self.deep_sleep_minutes + self.light_sleep_minutes + self.rem_minutes) / self.total_sleep_minutes) * 100

    @property
    def deep_sleep_pct(self) -> float:
        total_sleep = (self.deep_sleep_minutes + self.light_sleep_minutes + self.rem_minutes)
        if total_sleep == 0:
            return 0.0
        return (self.deep_sleep_minutes / total_sleep) * 100

    @property
    def rem_sleep_pct(self) -> float:
        total_sleep = (self.deep_sleep_minutes + self.light_sleep_minutes + self.rem_minutes)
        if total_sleep == 0:
            return 0.0
        return (self.rem_minutes / total_sleep) * 100


@dataclass
class AnalysisResult:
    records: List[SleepRecord]
    avg_total_sleep: float
    avg_deep_sleep: float
    avg_rem_sleep: float
    avg_efficiency: float
    sleep_regularity: float  # Standard deviation of total sleep duration (lower is better)
    trend: str
    recommendations: List[dict] = field(
        default_factory=list)  # Each recommendation: {"level": "danger/warning/success", "message": "..."}