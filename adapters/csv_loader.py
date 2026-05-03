import csv
from datetime import datetime
from typing import List
from domain.models import SleepRecord


class CSVLoadError(Exception):
    pass


class CSVLoader:
    REQUIRED_COLUMNS = {
        "date",
        "sleep_start",
        "sleep_end",
        "deep_sleep_minutes",
        "light_sleep_minutes",
        "rem_minutes",
        "awakenings",
    }

    # Необязательные колонки, которые мы поддерживаем
    OPTIONAL_COLUMNS = {
        "heart_rate_avg",
        "hr_variability_avg",
        "respiratory_rate_avg",
        "movement_index",
        "sleep_latency_minutes",
        "sleep_quality_rating",
        "age",
        "gender",
    }

    @staticmethod
    def load(filepath: str) -> List[SleepRecord]:
        records = []
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CSVLoadError("CSV file is empty or missing headers")

            fieldnames_set = set(reader.fieldnames)
            missing = CSVLoader.REQUIRED_COLUMNS - fieldnames_set
            if missing:
                raise CSVLoadError(f"Missing required columns: {', '.join(missing)}")

            # Определяем наличие опциональных полей
            optional_present = fieldnames_set & CSVLoader.OPTIONAL_COLUMNS

            for row_num, row in enumerate(reader, start=2):
                try:
                    record = SleepRecord(
                        date=datetime.strptime(row["date"].strip(), "%Y-%m-%d").date(),
                        sleep_start=datetime.strptime(
                            row["sleep_start"].strip(), "%H:%M"
                        ).time(),
                        sleep_end=datetime.strptime(
                            row["sleep_end"].strip(), "%H:%M"
                        ).time(),
                        deep_sleep_minutes=float(row["deep_sleep_minutes"]),
                        light_sleep_minutes=float(row["light_sleep_minutes"]),
                        rem_minutes=float(row["rem_minutes"]),
                        awakenings=int(row["awakenings"]),
                    )
                    # Заполняем опциональные поля, если они есть и не пусты
                    if (
                        "heart_rate_avg" in optional_present
                        and row.get("heart_rate_avg", "").strip()
                    ):
                        record.heart_rate_avg = float(row["heart_rate_avg"])
                    if (
                        "hr_variability_avg" in optional_present
                        and row.get("hr_variability_avg", "").strip()
                    ):
                        record.hr_variability_avg = float(row["hr_variability_avg"])
                    if (
                        "respiratory_rate_avg" in optional_present
                        and row.get("respiratory_rate_avg", "").strip()
                    ):
                        record.respiratory_rate_avg = float(row["respiratory_rate_avg"])
                    if (
                        "movement_index" in optional_present
                        and row.get("movement_index", "").strip()
                    ):
                        record.movement_index = float(row["movement_index"])
                    if (
                        "sleep_latency_minutes" in optional_present
                        and row.get("sleep_latency_minutes", "").strip()
                    ):
                        record.sleep_latency_minutes = int(row["sleep_latency_minutes"])
                    if (
                        "sleep_quality_rating" in optional_present
                        and row.get("sleep_quality_rating", "").strip()
                    ):
                        val = int(row["sleep_quality_rating"])
                        if 1 <= val <= 5:
                            record.sleep_quality_rating = val
                        else:
                            raise ValueError(
                                f"sleep_quality_rating must be 1-5, got {val}"
                            )
                    if "age" in optional_present and row.get("age", "").strip():
                        record.age = int(row["age"])
                    if "gender" in optional_present and row.get("gender", "").strip():
                        gender_val = row["gender"].strip().upper()
                        if gender_val in ("M", "F"):
                            record.gender = gender_val
                        else:
                            raise ValueError(
                                f"gender must be 'M' or 'F', got '{gender_val}'"
                            )

                    records.append(record)
                except (ValueError, KeyError) as e:
                    raise CSVLoadError(f"Row {row_num}: invalid data - {e}")
        return records
