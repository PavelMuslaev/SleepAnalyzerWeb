import csv
from datetime import datetime, date, time
from typing import List
from domain.models import SleepRecord


class CSVLoadError(Exception):
    pass


class CSVLoader:
    REQUIRED_COLUMNS = {'date', 'sleep_start', 'sleep_end', 'deep_sleep_minutes',
                        'light_sleep_minutes', 'rem_minutes', 'awakenings'}

    @staticmethod
    def load(filepath: str) -> List[SleepRecord]:
        records = []
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Проверяем наличие колонок
            if not reader.fieldnames:
                raise CSVLoadError("CSV file is empty or missing headers")
            missing = CSVLoader.REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise CSVLoadError(f"Missing columns: {', '.join(missing)}")

            for row_num, row in enumerate(reader, start=2):
                try:
                    record = SleepRecord(
                        date=datetime.strptime(row['date'].strip(), '%Y-%m-%d').date(),
                        sleep_start=datetime.strptime(row['sleep_start'].strip(), '%H:%M').time(),
                        sleep_end=datetime.strptime(row['sleep_end'].strip(), '%H:%M').time(),
                        deep_sleep_minutes=float(row['deep_sleep_minutes']),
                        light_sleep_minutes=float(row['light_sleep_minutes']),
                        rem_minutes=float(row['rem_minutes']),
                        awakenings=int(row['awakenings']),
                    )
                    records.append(record)
                except (ValueError, KeyError) as e:
                    raise CSVLoadError(f"Row {row_num}: invalid data - {e}")
        return records