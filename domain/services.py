# domain/services.py
import numpy as np
from typing import List, Dict, Optional, Tuple
from domain.models import SleepRecord, AnalysisResult


class SleepAnalysisService:
    """Сервис анализа данных сна с персональными нормами."""

    # ------------------------------------------------------------------
    # Возрастные группы и нормы
    # ------------------------------------------------------------------
    @staticmethod
    def _get_age_group(age: int) -> str:
        if age < 18:
            return "teen"
        elif age < 30:
            return "young_adult"
        elif age < 45:
            return "adult"
        elif age < 65:
            return "middle_age"
        else:
            return "older_adult"

    def _get_sleep_norms(
        self, age: Optional[int], gender: Optional[str]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Возвращает персональные нормы сна в виде словаря с кортежами (min, max).
        Если возраст не указан, возвращаются стандартные нормы для взрослого 18-45 лет.
        """
        # Базовые нормы (взрослые 18–45 лет)
        norms = {
            "total_sleep_hours": (7.0, 9.0),
            "deep_sleep_pct": (15.0, 25.0),  # % от общей продолжительности сна
            "rem_sleep_pct": (20.0, 25.0),
            "efficiency": (85.0, 100.0),
            "latency_min": (10.0, 20.0),
            "waso_min": (0.0, 30.0),
            "fragmentation": (0.0, 1.5),  # пробуждений в час
        }

        if age is None:
            return norms

        age_group = self._get_age_group(age)

        # Корректировка по возрасту (источники: NSF, AASM, метаанализы 2020-2024)
        if age_group == "teen":
            # Подростки 13-17 лет: сна нужно 8-10 ч, глуб.сон ~20-25%
            norms["total_sleep_hours"] = (8.0, 10.0)
            norms["deep_sleep_pct"] = (20.0, 30.0)
            norms["rem_sleep_pct"] = (20.0, 25.0)
        elif age_group == "young_adult":
            # 18-29 лет: базовые нормы, глубокий сон в норме 15-25%
            pass
        elif age_group == "adult":
            # 30-44 года: начинает снижаться доля глубокого сна
            norms["deep_sleep_pct"] = (10.0, 20.0)
            norms["waso_min"] = (0.0, 40.0)
        elif age_group == "middle_age":
            # 45-64 года: дальнейшее снижение глубокого сна, эффективность немного ниже
            norms["deep_sleep_pct"] = (7.0, 20.0)
            norms["efficiency"] = (80.0, 100.0)
            norms["waso_min"] = (0.0, 45.0)
        elif age_group == "older_adult":
            # 65+ лет: рекомендовано 7-8 ч, глубокий сон существенно меньше, допустима более низкая эффективность
            norms["total_sleep_hours"] = (6.0, 8.0)
            norms["deep_sleep_pct"] = (5.0, 15.0)
            norms["efficiency"] = (75.0, 100.0)
            norms["waso_min"] = (0.0, 60.0)

        # Небольшие поправки по полу
        if gender == "F":
            # Женщины в среднем имеют немного больше глубокого сна, но также чаще жалуются на бессонницу
            # Слегка повышаем верхнюю границу нормы глубокого сна
            deep_min, deep_max = norms["deep_sleep_pct"]
            norms["deep_sleep_pct"] = (deep_min + 2, min(deep_max + 5, 35.0))
        elif gender == "M":
            # Мужчины: без значительных корректировок, оставляем как есть
            pass

        return norms

    # ------------------------------------------------------------------
    # Основной метод анализа
    # ------------------------------------------------------------------
    def analyze(self, records: List[SleepRecord]) -> AnalysisResult:
        if not records:
            raise ValueError("No sleep records provided")

        sorted_records = sorted(records, key=lambda r: r.date)

        # 1. Базовые средние
        avg_total = float(np.mean([r.total_sleep_minutes for r in sorted_records]))
        avg_time_in_bed = float(
            np.mean([r.time_in_bed_minutes for r in sorted_records])
        )
        avg_efficiency = float(np.mean([r.sleep_efficiency for r in sorted_records]))
        avg_deep = float(np.mean([r.deep_sleep_minutes for r in sorted_records]))
        avg_light = float(np.mean([r.light_sleep_minutes for r in sorted_records]))
        avg_rem = float(np.mean([r.rem_minutes for r in sorted_records]))

        # 2. Латентность, WASO, фрагментация
        latencies = [
            r.sleep_latency_minutes
            for r in sorted_records
            if r.sleep_latency_minutes is not None
        ]
        avg_latency = float(np.mean(latencies)) if latencies else None

        # WASO: если известна латентность, вычитаем её из разницы время в постели - общий сон
        waso_vals = []
        for r in sorted_records:
            if r.sleep_latency_minutes is not None:
                waso_vals.append(
                    r.time_in_bed_minutes
                    - r.total_sleep_minutes
                    - r.sleep_latency_minutes
                )
            else:
                # Грубая оценка без латентности
                waso_vals.append(r.time_in_bed_minutes - r.total_sleep_minutes)
        avg_waso = float(np.mean(waso_vals)) if waso_vals else None

        frags = [r.sleep_fragmentation for r in sorted_records]
        avg_fragmentation = float(np.mean(frags)) if frags else None

        # 3. Регулярность
        durations = [r.total_sleep_minutes for r in sorted_records]
        sleep_regularity = float(np.std(durations)) if len(durations) >= 2 else 0.0

        # Консистентность времени отхода ко сну (разброс в минутах относительно полуночи)
        def bedtime_minutes_from_midnight(r: SleepRecord) -> float:
            minutes = r.sleep_start.hour * 60 + r.sleep_start.minute
            if (
                minutes > 12 * 60
            ):  # до полудня считаем "после полуночи", сдвигаем чтобы избежать разрыва
                minutes -= 24 * 60
            return minutes

        bedtimes = [bedtime_minutes_from_midnight(r) for r in sorted_records]
        bedtime_consistency = float(np.std(bedtimes)) if len(bedtimes) >= 2 else 0.0

        # 4. Физиологические показатели (если есть)
        hrs = [r.heart_rate_avg for r in sorted_records if r.heart_rate_avg is not None]
        hrv = [
            r.hr_variability_avg
            for r in sorted_records
            if r.hr_variability_avg is not None
        ]
        resp = [
            r.respiratory_rate_avg
            for r in sorted_records
            if r.respiratory_rate_avg is not None
        ]
        mov = [r.movement_index for r in sorted_records if r.movement_index is not None]
        subj = [
            r.sleep_quality_rating
            for r in sorted_records
            if r.sleep_quality_rating is not None
        ]

        avg_hr = float(np.mean(hrs)) if hrs else None
        avg_hrv = float(np.mean(hrv)) if hrv else None
        avg_resp = float(np.mean(resp)) if resp else None
        avg_mov = float(np.mean(mov)) if mov else None
        avg_subj = float(np.mean(subj)) if subj else None

        # 5. Персональные данные (из первой записи, где есть возраст)
        user_age = None
        user_gender = None
        for r in sorted_records:
            if r.age is not None:
                user_age = r.age
                user_gender = r.gender  # пол берём оттуда же
                break
        # Если пол не задан, но возраст есть, gender может быть None
        if user_age is not None and user_gender is None:
            user_gender = None  # оставляем

        # Получаем персональные нормы (если возраст есть)
        norms = (
            self._get_sleep_norms(user_age, user_gender)
            if user_age is not None
            else self._get_sleep_norms(None, None)
        )

        # 6. Интегральный sleep_score с учётом норм
        sleep_score = self._compute_sleep_score(
            avg_total,
            avg_efficiency,
            avg_deep,
            avg_rem,
            avg_fragmentation,
            avg_latency,
            avg_waso,
            bedtime_consistency,
            norms,
        )

        # 7. Sleep debt (целевое значение из норм)
        target_hours = (
            norms["total_sleep_hours"][0] + norms["total_sleep_hours"][1]
        ) / 2.0
        target_minutes = target_hours * 60
        sleep_debt = max(0.0, target_minutes - avg_total)

        # 8. Тренд эффективности за последние 7 дней
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

        # 9. Рекомендации с учётом профиля
        recommendations = self._generate_recommendations(
            avg_total,
            avg_efficiency,
            avg_deep,
            avg_rem,
            sleep_regularity,
            avg_latency,
            avg_waso,
            avg_fragmentation,
            avg_hrv,
            avg_mov,
            avg_subj,
            trend,
            user_age,
            user_gender,
            norms,
        )

        return AnalysisResult(
            records=sorted_records,
            avg_total_sleep=avg_total,
            avg_time_in_bed=avg_time_in_bed,
            avg_efficiency=avg_efficiency,
            avg_latency=avg_latency,
            avg_waso=avg_waso,
            avg_fragmentation=avg_fragmentation,
            avg_deep_sleep=avg_deep,
            avg_light_sleep=avg_light,
            avg_rem_sleep=avg_rem,
            sleep_regularity=sleep_regularity,
            bedtime_consistency=bedtime_consistency,
            avg_heart_rate=avg_hr,
            avg_hrv=avg_hrv,
            avg_respiratory_rate=avg_resp,
            avg_movement=avg_mov,
            avg_subjective_rating=avg_subj,
            sleep_score=sleep_score,
            sleep_debt_minutes=sleep_debt,
            trend=trend,
            recommendations=recommendations,
            user_age=user_age,
            user_gender=user_gender,
        )

    # ------------------------------------------------------------------
    # Расчёт Sleep Score (0–100) с персонализированными нормами
    # ------------------------------------------------------------------
    def _compute_sleep_score(
        self,
        total_min: float,
        efficiency: float,
        deep_min: float,
        rem_min: float,
        fragmentation: Optional[float],
        latency: Optional[float],
        waso: Optional[float],
        bedtime_std: float,
        norms: Dict[str, Tuple[float, float]],
    ) -> int:
        score = 0.0

        # 1. Длительность (20 баллов)
        total_hours = total_min / 60.0
        min_h, max_h = norms["total_sleep_hours"]
        if min_h <= total_hours <= max_h:
            dur_score = 20.0
        else:
            deviation = min(abs(total_hours - min_h), abs(total_hours - max_h))
            dur_score = max(
                0.0, 20.0 - deviation * 5
            )  # минус 5 баллов за каждый час отклонения
        score += dur_score

        # 2. Эффективность (20 баллов)
        eff_min, _ = norms["efficiency"]
        if efficiency >= eff_min:
            eff_score = 20.0
        else:
            eff_score = max(0.0, efficiency / eff_min * 20.0)
        score += eff_score

        # 3. Глубокий сон (15 баллов)
        deep_pct = (deep_min / total_min * 100) if total_min > 0 else 0.0
        deep_min_pct, deep_max_pct = norms["deep_sleep_pct"]
        if deep_pct >= deep_max_pct:
            deep_score = 15.0
        elif deep_pct <= deep_min_pct:
            deep_score = max(
                0.0, deep_pct / deep_min_pct * 10.0
            )  # ниже нижней границы – меньше баллов
        else:
            # линейно между min и max
            deep_score = 10.0 + 5.0 * (deep_pct - deep_min_pct) / (
                deep_max_pct - deep_min_pct
            )
        score += deep_score

        # 4. REM-сон (15 баллов)
        rem_pct = (rem_min / total_min * 100) if total_min > 0 else 0.0
        rem_min_pct, rem_max_pct = norms["rem_sleep_pct"]
        if rem_pct >= rem_max_pct:
            rem_score = 15.0
        elif rem_pct <= rem_min_pct:
            rem_score = max(0.0, rem_pct / rem_min_pct * 10.0)
        else:
            rem_score = 10.0 + 5.0 * (rem_pct - rem_min_pct) / (
                rem_max_pct - rem_min_pct
            )
        score += rem_score

        # 5. Стабильность и непрерывность (20 баллов: 10 за фрагментацию + 10 за регулярность времени)
        frag_min, frag_max = norms.get("fragmentation", (0.0, 1.5))
        if fragmentation is not None:
            if fragmentation <= frag_min:
                frag_score = 10.0
            elif fragmentation >= frag_max:
                frag_score = 0.0
            else:
                frag_score = (
                    10.0 - (fragmentation - frag_min) / (frag_max - frag_min) * 10.0
                )
        else:
            frag_score = 10.0  # нет данных – не штрафуем
        score += frag_score

        # Консистентность времени отхода ко сну (10 баллов)
        if bedtime_std <= 15:
            bedtime_score = 10.0
        elif bedtime_std <= 30:
            bedtime_score = 8.0
        elif bedtime_std <= 60:
            bedtime_score = 5.0
        else:
            bedtime_score = max(0.0, 5.0 - (bedtime_std - 60) / 10)
        score += bedtime_score

        # 6. Штрафы за латентность и WASO (до -10 баллов)
        penalty = 0.0
        lat_min, lat_max = norms["latency_min"]
        if latency is not None:
            if latency > lat_max:
                penalty += min(5.0, (latency - lat_max) / 10)
        waso_min, waso_max = norms["waso_min"]
        if waso is not None:
            if waso > waso_max:
                penalty += min(5.0, (waso - waso_max) / 10)
        score -= penalty

        return max(0, min(100, int(round(score))))

    # ------------------------------------------------------------------
    # Генерация рекомендаций с учётом профиля и норм
    # ------------------------------------------------------------------
    def _generate_recommendations(
        self,
        avg_total: float,
        avg_eff: float,
        avg_deep: float,
        avg_rem: float,
        regularity: float,
        latency: Optional[float],
        waso: Optional[float],
        frag: Optional[float],
        hrv: Optional[float],
        mov: Optional[float],
        subj: Optional[float],
        trend: str,
        age: Optional[int],
        gender: Optional[str],
        norms: Dict[str, Tuple[float, float]],
    ) -> List[Dict[str, str]]:
        recs = []
        total_hours = avg_total / 60.0

        # 1. Продолжительность сна
        min_h, max_h = norms["total_sleep_hours"]
        if total_hours < min_h:
            recs.append(
                {
                    "level": "danger",
                    "message": f"Средняя продолжительность сна ({total_hours:.1f} ч) ниже нормы ({min_h:.0f}–{max_h:.0f} ч). Постарайтесь ложиться раньше или выделять больше времени на сон.",
                }
            )
        elif total_hours > max_h:
            recs.append(
                {
                    "level": "warning",
                    "message": f"Средняя продолжительность сна ({total_hours:.1f} ч) выше верхней границы нормы ({max_h:.0f} ч). Регулярный избыточный сон может указывать на низкое качество сна или скрытые нарушения.",
                }
            )
        else:
            recs.append(
                {
                    "level": "success",
                    "message": f"Продолжительность сна ({total_hours:.1f} ч) в пределах нормы.",
                }
            )

        # 2. Эффективность сна
        eff_min, _ = norms["efficiency"]
        if avg_eff < eff_min - 10:
            recs.append(
                {
                    "level": "danger",
                    "message": "Эффективность сна существенно ниже нормы. Рекомендуется техника ограничения времени в постели (CBT-I): сократите время нахождения в кровати до фактического среднего времени сна.",
                }
            )
        elif avg_eff < eff_min:
            recs.append(
                {
                    "level": "warning",
                    "message": "Эффективность сна ниже оптимальной. Используйте метод стимул-контроля: вставайте с постели, если не можете уснуть в течение 20 минут.",
                }
            )
        else:
            recs.append({"level": "success", "message": "Эффективность сна в норме."})

        # 3. Глубокий сон
        deep_pct = (avg_deep / avg_total * 100) if avg_total > 0 else 0.0
        deep_min, deep_max = norms["deep_sleep_pct"]
        if deep_pct < deep_min:
            recs.append(
                {
                    "level": "danger",
                    "message": f"Доля глубокого сна ({deep_pct:.0f}%) значительно ниже возрастной нормы ({deep_min:.0f}–{deep_max:.0f}%). Рекомендуется: исключить алкоголь, обеспечить прохладу в спальне, увеличить дневную физическую активность.",
                }
            )
        elif deep_pct < (deep_min + deep_max) / 2:
            recs.append(
                {
                    "level": "warning",
                    "message": f"Доля глубокого сна ({deep_pct:.0f}%) немного ниже оптимального значения. Попробуйте ложиться до 23:00 и не есть за 2–3 часа до сна.",
                }
            )
        else:
            recs.append(
                {"level": "success", "message": "Глубокий сон в хорошем диапазоне."}
            )

        # 4. REM-сон
        rem_pct = (avg_rem / avg_total * 100) if avg_total > 0 else 0.0
        rem_min, rem_max = norms["rem_sleep_pct"]
        if rem_pct < rem_min:
            recs.append(
                {
                    "level": "danger",
                    "message": f"Доля REM-сна ({rem_pct:.0f}%) ниже нормы ({rem_min:.0f}–{rem_max:.0f}%). Это часто связано со стрессом или употреблением алкоголя. Рекомендуются вечерние ритуалы расслабления.",
                }
            )
        elif rem_pct < rem_max:
            recs.append(
                {
                    "level": "warning",
                    "message": "REM-сон чуть ниже верхней границы. Для улучшения попробуйте медитацию, дыхательные упражнения, избегайте яркого света вечером.",
                }
            )
        else:
            recs.append({"level": "success", "message": "REM-сон в норме."})

        # 5. Регулярность
        if regularity > 60:
            recs.append(
                {
                    "level": "danger",
                    "message": "Очень нерегулярный сон по продолжительности. Старайтесь соблюдать одинаковое время подъёма и отхода ко сну даже в выходные.",
                }
            )
        elif regularity > 30:
            recs.append(
                {
                    "level": "warning",
                    "message": "Умеренная нерегулярность сна. Разница между буднями и выходными не должна превышать 1 часа.",
                }
            )

        # 6. Физиология
        if hrv is not None and hrv < 30:
            recs.append(
                {
                    "level": "warning",
                    "message": "Низкая вариабельность сердечного ритма (HRV) может указывать на переутомление. Рекомендуется день восстановления.",
                }
            )
        if mov is not None and mov > 15:
            recs.append(
                {
                    "level": "warning",
                    "message": "Повышенная двигательная активность во сне. Проверьте удобство матраса и подушки, избегайте тяжёлой пищи на ночь.",
                }
            )

        # 7. Субъективная оценка
        if subj is not None:
            if subj <= 2:
                recs.append(
                    {
                        "level": "danger",
                        "message": "Вы сами оцениваете качество сна как низкое. Обсудите это с врачом-сомнологом, особенно если объективные показатели в норме.",
                    }
                )
            elif subj <= 3:
                recs.append(
                    {
                        "level": "warning",
                        "message": "Субъективно сон мог бы быть лучше. Попробуйте вести дневник сна для выявления негативных факторов.",
                    }
                )
            else:
                recs.append(
                    {
                        "level": "success",
                        "message": "По вашим ощущениям, качество сна хорошее.",
                    }
                )

        # 8. Возрастные и гендерные особенности
        if age is not None:
            if age >= 65:
                recs.append(
                    {
                        "level": "info",
                        "message": "В возрасте 65+ снижение доли глубокого сна и увеличение ночных пробуждений – естественный процесс. Продолжайте поддерживать регулярный режим и дневную активность.",
                    }
                )
            elif age >= 45:
                recs.append(
                    {
                        "level": "info",
                        "message": "В среднем возрасте важно компенсировать естественное снижение глубокого сна физической нагрузкой и избеганием алкоголя.",
                    }
                )
            if gender == "F" and age and 40 <= age <= 60:
                recs.append(
                    {
                        "level": "info",
                        "message": "В перименопаузе могут наблюдаться ночные пробуждения и ухудшение качества сна. Поддерживайте прохладу в спальне и обсудите с врачом возможные стратегии.",
                    }
                )

        # 9. Тренд
        if trend == "ухудшается":
            recs.append(
                {
                    "level": "warning",
                    "message": "Наблюдается отрицательная динамика. Проанализируйте стресс-факторы и образ жизни за последние дни.",
                }
            )
        elif trend == "улучшается":
            recs.append(
                {
                    "level": "success",
                    "message": "Положительная динамика! Ваш сон улучшается, продолжайте в том же духе.",
                }
            )

        # Общий совет
        recs.append(
            {
                "level": "info",
                "message": "Гигиена сна: темнота, тишина, прохлада (18–20°C), отказ от гаджетов за час до сна, постоянный режим.",
            }
        )

        return recs
