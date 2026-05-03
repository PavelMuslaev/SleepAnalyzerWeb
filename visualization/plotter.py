import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import List
from domain.models import SleepRecord


class SleepPlotter:
    @staticmethod
    def create_duration_phase_plot(records: List[SleepRecord]) -> str:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        total = [r.total_sleep_minutes / 60 for r in sorted_records]  # в часах
        deep = [r.deep_sleep_minutes / 60 for r in sorted_records]
        light = [r.light_sleep_minutes / 60 for r in sorted_records]
        rem = [r.rem_minutes / 60 for r in sorted_records]

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Общая продолжительность сна", "Фазы сна"),
                            vertical_spacing=0.15)

        fig.add_trace(go.Scatter(x=dates, y=total, mode='lines+markers', name='Всего часов'), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=deep, mode='lines+markers', name='Глубокий'), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=light, mode='lines+markers', name='Легкий'), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=rem, mode='lines+markers', name='REM'), row=2, col=1)

        fig.update_layout(title='Анализ сна', height=600, hovermode='x unified')
        fig.update_yaxes(title_text='Часы', row=1, col=1)
        fig.update_yaxes(title_text='Часы', row=2, col=1)

        # Возвращаем HTML div
        return pio.to_html(fig, full_html=False)

    @staticmethod
    def create_efficiency_plot(records: List[SleepRecord]) -> str:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        eff = [r.sleep_efficiency for r in sorted_records]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=eff, mode='lines+markers', name='Эффективность (%)'))
        fig.update_layout(title='Эффективность сна', yaxis_title='%', height=300)
        return pio.to_html(fig, full_html=False)