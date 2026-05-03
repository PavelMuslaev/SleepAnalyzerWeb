from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class SleepRecord:
    # Обязательные поля
    date: datetime.date
    sleep_start: datetime.time
    sleep_end: datetime.time
    deep_sleep_minutes: float
    light_sleep_minutes: float
    rem_minutes: float
    awakenings: int

    # Новые опциональные поля (Option 1)
    heart_rate_avg: Optional[float] = None
    hr_variability_avg: Optional[float] = None  # HRV (ms)
    respiratory_rate_avg: Optional[float] = None  # breaths/min
    movement_index: Optional[float] = None  # movements per hour
    sleep_latency_minutes: Optional[int] = None  # minutes to fall asleep
    sleep_quality_rating: Optional[int] = None  # subjective 1-5
    age: Optional[int] = None
    gender: Optional[str] = None  # 'M' или 'F'

    @property
    def total_sleep_minutes(self) -> float:
        return self.deep_sleep_minutes + self.light_sleep_minutes + self.rem_minutes

    @property
    def time_in_bed_minutes(self) -> float:
        start_dt = datetime.combine(self.date, self.sleep_start)
        end_dt = datetime.combine(self.date, self.sleep_end)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        return (end_dt - start_dt).total_seconds() / 60.0

    @property
    def sleep_efficiency(self) -> float:
        tib = self.time_in_bed_minutes
        return (self.total_sleep_minutes / tib * 100) if tib > 0 else 0.0

    @property
    def wake_after_sleep_onset(self) -> float:
        """WASO: время бодрствования после первого засыпания (приблизительно, через эффективность)."""
        # Точнее – через awakenings * среднюю длительность пробуждения, но без неё оценим как разницу между временем в постели и фактическим сном.
        return (
            self.time_in_bed_minutes
            - self.total_sleep_minutes
            - (self.sleep_latency_minutes or 0)
        )

    @property
    def sleep_fragmentation(self) -> float:
        """Количество пробуждений в час сна."""
        total_hours = self.total_sleep_minutes / 60.0
        return self.awakenings / total_hours if total_hours > 0 else 0.0


@dataclass
class AnalysisResult:
    # Обязательные поля (без default)
    records: List[SleepRecord]
    avg_total_sleep: float
    avg_time_in_bed: float
    avg_efficiency: float
    avg_deep_sleep: float
    avg_light_sleep: float
    avg_rem_sleep: float
    sleep_regularity: float

    # Опциональные поля (с default)
    avg_latency: Optional[float] = None
    avg_waso: Optional[float] = None
    avg_fragmentation: Optional[float] = None
    bedtime_consistency: float = 0.0
    avg_heart_rate: Optional[float] = None
    avg_hrv: Optional[float] = None
    avg_respiratory_rate: Optional[float] = None
    avg_movement: Optional[float] = None
    avg_subjective_rating: Optional[float] = None
    sleep_score: Optional[int] = None
    sleep_debt_minutes: Optional[float] = None
    trend: str = ""
    recommendations: List[dict] = field(default_factory=list)
    user_age: Optional[int] = None
    user_gender: Optional[str] = None

    def to_dict(self):
        return {
            'avg_total_sleep': self.avg_total_sleep,
            'avg_time_in_bed': self.avg_time_in_bed,
            'avg_efficiency': self.avg_efficiency,
            'avg_latency': self.avg_latency,
            'avg_waso': self.avg_waso,
            'avg_fragmentation': self.avg_fragmentation,
            'avg_deep_sleep': self.avg_deep_sleep,
            'avg_light_sleep': self.avg_light_sleep,
            'avg_rem_sleep': self.avg_rem_sleep,
            'sleep_regularity': self.sleep_regularity,
            'bedtime_consistency': self.bedtime_consistency,
            'avg_heart_rate': self.avg_heart_rate,
            'avg_hrv': self.avg_hrv,
            'avg_respiratory_rate': self.avg_respiratory_rate,
            'avg_movement': self.avg_movement,
            'avg_subjective_rating': self.avg_subjective_rating,
            'sleep_score': self.sleep_score,
            'sleep_debt_minutes': self.sleep_debt_minutes,
            'trend': self.trend,
            'recommendations': [{'level': r['level'], 'message': r['message']} for r in self.recommendations],
            'user_age': self.user_age,
            'user_gender': self.user_gender
        }