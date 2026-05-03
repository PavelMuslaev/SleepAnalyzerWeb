# domain/services.py
import numpy as np
from typing import List, Dict, Any
from domain.models import SleepRecord, AnalysisResult


class SleepAnalysisService:
    def analyze(self, records: List[SleepRecord]) -> AnalysisResult:
        if not records:
            raise ValueError("No sleep records provided")

        sorted_records = sorted(records, key=lambda r: r.date)

        # Вычисляем средние
        avg_total = np.mean([r.total_sleep_minutes for r in sorted_records])
        avg_deep = np.mean([r.deep_sleep_minutes for r in sorted_records])
        avg_rem = np.mean([r.rem_minutes for r in sorted_records])
        avg_eff = np.mean([r.sleep_efficiency for r in sorted_records])

        # Новая метрика: регулярность сна (стандартное отклонение от средней продолжительности)
        durations = [r.total_sleep_minutes for r in sorted_records]
        if len(durations) >= 2:
            sleep_regularity = np.std(durations)
        else:
            sleep_regularity = 0.0

        # Простой тренд по эффективности за последние 7 дней (или все)
        efficiencies = [r.sleep_efficiency for r in sorted_records[-7:]]
        if len(efficiencies) >= 2:
            x = np.arange(len(efficiencies))
            slope = np.polyfit(x, efficiencies, 1)[0]
            if slope > 1:
                trend = "улучшается"
            elif slope < -1:
                trend = "ухудшается"
            else:
                trend = "стабильный"
        else:
            trend = "недостаточно данных"

        recommendations = self._generate_recommendations(
            avg_total, avg_deep, avg_rem, avg_eff, sleep_regularity, trend
        )

        return AnalysisResult(
            records=sorted_records,
            avg_total_sleep=avg_total,
            avg_deep_sleep=avg_deep,
            avg_rem_sleep=avg_rem,
            avg_efficiency=avg_eff,
            sleep_regularity=sleep_regularity,
            trend=trend,
            recommendations=recommendations
        )

    def _generate_recommendations(self, avg_total: float, avg_deep: float, avg_rem: float, efficiency: float,
                                  regularity: float, trend: str) -> List[Dict[str, str]]:
        """Generate evidence-based recommendations with levels ('danger', 'warning', 'success')."""
        recs = []

        # 1. Анализ продолжительности сна (National Sleep Foundation: 7-9h)
        total_hours = avg_total / 60
        if total_hours < 7:
            recs.append({
                "level": "danger",
                "message": "Средняя продолжительность сна ниже рекомендуемой нормы (7–9 часов для взрослых). Это может негативно сказываться на когнитивных функциях и иммунитете."
            })
        elif total_hours > 9:
            recs.append({
                "level": "warning",
                "message": "Средняя продолжительность сна выше нормы. Регулярный избыточный сон может быть связан с повышенным риском сердечно-сосудистых заболеваний."
            })
        else:
            recs.append({
                "level": "success",
                "message": "Средняя продолжительность сна в пределах здоровой нормы (7–9 часов). Так держать!"
            })

        # 2. Анализ глубокого сна (норма 20–25%)
        deep_pct = (avg_deep / avg_total) * 100 if avg_total > 0 else 0
        if deep_pct < 15:
            recs.append({
                "level": "danger",
                "message": "Крайне низкая доля глубокого сна (менее 15%). Рекомендуется увеличить физическую активность в первой половине дня и полностью исключить алкоголь перед сном."
            })
        elif deep_pct < 20:
            recs.append({
                "level": "warning",
                "message": "Доля глубокого сна немного ниже нормы (15-20%). Для её повышения старайтесь ложиться спать до 23:00 и поддерживайте прохладную температуру в спальне (18-20°C)."
            })

        # 3. Анализ REM-сна (норма 20–25%)
        rem_pct = (avg_rem / avg_total) * 100 if avg_total > 0 else 0
        if rem_pct < 15:
            recs.append({
                "level": "danger",
                "message": "Крайне низкая доля REM-сна (менее 15%). Это может быть вызвано хроническим стрессом или употреблением алкоголя. Рекомендуются расслабляющие ритуалы перед сном и техники управления стрессом."
            })
        elif rem_pct < 20:
            recs.append({
                "level": "warning",
                "message": "Доля REM-сна немного ниже нормы (15-20%). Попробуйте добавить вечерние ритуалы расслабления: чтение, тёплую ванну, медитацию или лёгкую растяжку."
            })

        # 4. Анализ эффективности сна
        if efficiency < 75:
            recs.append({
                "level": "danger",
                "message": "Эффективность сна крайне низкая (менее 75%). Рекомендуется применять метод ограничения сна (CBT-I): сократите время пребывания в постели до вашего среднего фактического времени сна, чтобы консолидировать сон."
            })
        elif efficiency < 85:
            recs.append({
                "level": "warning",
                "message": "Эффективность сна ниже оптимальной (75–85%). Используйте метод стимул-контроля (CBT-I): если не можете уснуть в течение 20 минут, встаньте с постели и займитесь чем-то спокойным при тусклом свете."
            })
        else:
            recs.append({
                "level": "success",
                "message": "Эффективность сна на хорошем уровне (выше 85%). Отличная работа!"
            })

        # 5. Анализ регулярности сна
        if regularity > 60:
            recs.append({
                "level": "danger",
                "message": "Очень высокая нерегулярность сна. Постарайтесь ложиться и вставать в одно и то же время даже в выходные дни. Это поможет стабилизировать ваши циркадные ритмы."
            })
        elif regularity > 30:
            recs.append({
                "level": "warning",
                "message": "Умеренная нерегулярность сна. Старайтесь, чтобы разница во времени сна в будние и выходные дни не превышала 1 часа."
            })

        # 6. Анализ тренда
        if trend == "ухудшается":
            recs.append({
                "level": "warning",
                "message": "Наблюдается отрицательная динамика. Проанализируйте стресс-факторы, режим дня и питание. Возможно, вам будет полезна консультация сомнолога."
            })
        elif trend == "улучшается":
            recs.append({
                "level": "success",
                "message": "Положительная динамика! Ваши показатели сна улучшаются. Продолжайте в том же духе."
            })

        # Добавляем общие рекомендации по гигиене сна
        recs.append({
            "level": "info",
            "message": "Общая рекомендация: поддерживайте в спальне темноту, тишину и прохладу (18-20°C). Избегайте использования гаджетов за 1-2 часа до сна, так как синий свет подавляет выработку мелатонина."
        })

        return recs