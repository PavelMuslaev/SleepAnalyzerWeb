import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import List, Optional, Dict, Tuple
from domain.models import SleepRecord


class SleepPlotter:
    @staticmethod
    def create_duration_phase_figure(
        records: List[SleepRecord],
        norms: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> go.Figure:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        total = [r.total_sleep_minutes / 60.0 for r in sorted_records]
        deep = [r.deep_sleep_minutes / 60.0 for r in sorted_records]
        light = [r.light_sleep_minutes / 60.0 for r in sorted_records]
        rem = [r.rem_minutes / 60.0 for r in sorted_records]

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            subplot_titles=("Общая продолжительность сна", "Фазы сна"),
            vertical_spacing=0.15
        )
        fig.add_trace(go.Scatter(x=dates, y=total, mode='lines+markers', name='Всего часов'), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=deep, mode='lines+markers', name='Глубокий'), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=light, mode='lines+markers', name='Лёгкий'), row=2, col=1)
        fig.add_trace(go.Scatter(x=dates, y=rem, mode='lines+markers', name='REM'), row=2, col=1)

        if norms and total:
            avg_total_hours = sum(total) / len(total)
            deep_min_pct, deep_max_pct = norms.get("deep_sleep_pct", (15.0, 25.0))
            rem_min_pct, rem_max_pct = norms.get("rem_sleep_pct", (20.0, 25.0))
            deep_min_h = avg_total_hours * deep_min_pct / 100.0
            deep_max_h = avg_total_hours * deep_max_pct / 100.0
            rem_min_h = avg_total_hours * rem_min_pct / 100.0
            rem_max_h = avg_total_hours * rem_max_pct / 100.0

            fig.add_hline(y=deep_min_h, line_dash="dot", line_color="gray",
                          annotation_text=f"мин. глубокого ({deep_min_pct:.0f}%)",
                          annotation_position="bottom right", row=2, col=1)
            fig.add_hline(y=deep_max_h, line_dash="dot", line_color="gray",
                          annotation_text=f"макс. глубокого ({deep_max_pct:.0f}%)",
                          annotation_position="top right", row=2, col=1)
            fig.add_hline(y=rem_min_h, line_dash="dot", line_color="gray",
                          annotation_text=f"мин. REM ({rem_min_pct:.0f}%)",
                          annotation_position="bottom right", row=2, col=1)
            fig.add_hline(y=rem_max_h, line_dash="dot", line_color="gray",
                          annotation_text=f"макс. REM ({rem_max_pct:.0f}%)",
                          annotation_position="top right", row=2, col=1)

        fig.update_layout(title='Анализ сна', height=600, hovermode='x unified')
        fig.update_yaxes(title_text='Часы', row=1, col=1)
        fig.update_yaxes(title_text='Часы', row=2, col=1)
        return fig

    @staticmethod
    def create_efficiency_figure(
        records: List[SleepRecord],
        norms: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> go.Figure:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        eff = [r.sleep_efficiency for r in sorted_records]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=eff, mode='lines+markers', name='Эффективность (%)'))
        if norms:
            eff_min, _ = norms.get("efficiency", (85.0, 100.0))
            fig.add_hrect(y0=eff_min, y1=100, fillcolor="green", opacity=0.1, line_width=0,
                          annotation_text=f"Норма ≥{eff_min:.0f}%", annotation_position="top left")
            fig.add_hline(y=eff_min, line_dash="dash", line_color="green",
                          annotation_text=f"Нижняя граница ({eff_min:.0f}%)",
                          annotation_position="bottom right")
        fig.update_layout(title='Эффективность сна', yaxis_title='%', height=300)
        return fig

    @staticmethod
    def create_physio_figures(records: List[SleepRecord]) -> List[Tuple[str, go.Figure]]:
        """Возвращает список (название, Figure) для доступных физиологических данных."""
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        figs = []

        hr_vals = [r.heart_rate_avg for r in sorted_records if r.heart_rate_avg is not None]
        if hr_vals:
            hr_dates = dates[-len(hr_vals):]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hr_dates, y=hr_vals, mode='lines+markers', name='Пульс'))
            fig.update_layout(title='Средний пульс во сне', yaxis_title='уд/мин', height=300)
            figs.append(('heart_rate', fig))

        hrv_vals = [r.hr_variability_avg for r in sorted_records if r.hr_variability_avg is not None]
        if hrv_vals:
            hrv_dates = dates[-len(hrv_vals):]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hrv_dates, y=hrv_vals, mode='lines+markers', name='HRV'))
            fig.update_layout(title='Вариабельность сердечного ритма', yaxis_title='мс', height=300)
            figs.append(('hrv', fig))

        resp_vals = [r.respiratory_rate_avg for r in sorted_records if r.respiratory_rate_avg is not None]
        if resp_vals:
            resp_dates = dates[-len(resp_vals):]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=resp_dates, y=resp_vals, mode='lines+markers', name='Дыхание'))
            fig.update_layout(title='Частота дыхания', yaxis_title='вдох/мин', height=300)
            figs.append(('resp', fig))

        mov_vals = [r.movement_index for r in sorted_records if r.movement_index is not None]
        if mov_vals:
            mov_dates = dates[-len(mov_vals):]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mov_dates, y=mov_vals, mode='lines+markers', name='Движения'))
            fig.update_layout(title='Двигательная активность', yaxis_title='движ/ч', height=300)
            figs.append(('movement', fig))

        return figs

    # Удобные обёртки для HTML
    @staticmethod
    def create_duration_phase_plot(records, norms=None) -> str:
        fig = SleepPlotter.create_duration_phase_figure(records, norms)
        return pio.to_html(fig, full_html=False)

    @staticmethod
    def create_efficiency_plot(records, norms=None) -> str:
        fig = SleepPlotter.create_efficiency_figure(records, norms)
        return pio.to_html(fig, full_html=False)