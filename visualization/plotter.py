import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import List, Optional, Dict, Tuple
from domain.models import SleepRecord


class SleepPlotter:
    @staticmethod
    def create_duration_phase_figure(
        records: List[SleepRecord],
        norms: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> go.Figure:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        total = [r.total_sleep_minutes / 60.0 for r in sorted_records]
        deep = [r.deep_sleep_minutes / 60.0 for r in sorted_records]
        light = [r.light_sleep_minutes / 60.0 for r in sorted_records]
        rem = [r.rem_minutes / 60.0 for r in sorted_records]

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            subplot_titles=("Общая продолжительность сна", "Фазы сна"),
            vertical_spacing=0.15,
        )

        # График общей длительности с заливкой
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=total,
                mode="lines+markers",
                name="Всего часов",
                fill="tozeroy",
                fillcolor="rgba(66, 133, 244, 0.15)",
            ),
            row=1,
            col=1,
        )

        # Фазы с градиентной заливкой
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=deep,
                mode="lines+markers",
                name="Глубокий",
                fill="tozeroy",
                fillcolor="rgba(15, 157, 88, 0.15)",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=light,
                mode="lines+markers",
                name="Лёгкий",
                fill="tozeroy",
                fillcolor="rgba(255, 193, 7, 0.15)",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=rem,
                mode="lines+markers",
                name="REM",
                fill="tozeroy",
                fillcolor="rgba(203, 68, 75, 0.15)",
            ),
            row=2,
            col=1,
        )

        if norms and total:
            avg_total_hours = sum(total) / len(total)
            deep_min_pct, deep_max_pct = norms.get("deep_sleep_pct", (15.0, 25.0))
            rem_min_pct, rem_max_pct = norms.get("rem_sleep_pct", (20.0, 25.0))
            deep_min_h = avg_total_hours * deep_min_pct / 100.0
            deep_max_h = avg_total_hours * deep_max_pct / 100.0
            rem_min_h = avg_total_hours * rem_min_pct / 100.0
            rem_max_h = avg_total_hours * rem_max_pct / 100.0
            for y_val, txt in [
                (deep_min_h, f"мин. глубокого ({deep_min_pct:.0f}%)"),
                (deep_max_h, f"макс. глубокого ({deep_max_pct:.0f}%)"),
            ]:
                fig.add_hline(
                    y=y_val,
                    line_dash="dot",
                    line_color="gray",
                    annotation_text=txt,
                    annotation_position="bottom right",
                    row=2,
                    col=1,
                )
            for y_val, txt in [
                (rem_min_h, f"мин. REM ({rem_min_pct:.0f}%)"),
                (rem_max_h, f"макс. REM ({rem_max_pct:.0f}%)"),
            ]:
                fig.add_hline(
                    y=y_val,
                    line_dash="dot",
                    line_color="gray",
                    annotation_text=txt,
                    annotation_position="bottom right",
                    row=2,
                    col=1,
                )

        fig.update_layout(title="Анализ сна", height=600, hovermode="x unified")
        fig.update_yaxes(title_text="Часы", row=1, col=1)
        fig.update_yaxes(title_text="Часы", row=2, col=1)
        return fig

    @staticmethod
    def create_efficiency_figure(
        records: List[SleepRecord],
        norms: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> go.Figure:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        eff = [r.sleep_efficiency for r in sorted_records]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=eff,
                mode="lines+markers",
                name="Эффективность (%)",
                fill="tozeroy",
                fillcolor="rgba(66, 133, 244, 0.1)",
            )
        )
        if norms:
            eff_min, _ = norms.get("efficiency", (85.0, 100.0))
            fig.add_hrect(
                y0=eff_min,
                y1=100,
                fillcolor="green",
                opacity=0.1,
                line_width=0,
                annotation_text=f"Норма ≥{eff_min:.0f}%",
                annotation_position="top left",
            )
            fig.add_hline(
                y=eff_min,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Нижняя граница ({eff_min:.0f}%)",
            )
        fig.update_layout(title="Эффективность сна", yaxis_title="%", height=300)
        return fig

    @staticmethod
    def create_physio_figures(
        records: List[SleepRecord],
    ) -> List[Tuple[str, go.Figure]]:
        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date.isoformat() for r in sorted_records]
        figs = []
        for metric, name, color in [
            ("heart_rate_avg", "Пульс (уд/мин)", "rgba(220, 53, 69, 0.2)"),
            ("hr_variability_avg", "HRV (мс)", "rgba(25, 135, 84, 0.2)"),
            ("respiratory_rate_avg", "Дыхание (вд/мин)", "rgba(13, 202, 240, 0.2)"),
            ("movement_index", "Движения (в час)", "rgba(255, 193, 7, 0.2)"),
        ]:
            vals = [
                getattr(r, metric)
                for r in sorted_records
                if getattr(r, metric) is not None
            ]
            if vals:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=dates[-len(vals) :],
                        y=vals,
                        mode="lines+markers",
                        fill="tozeroy",
                        fillcolor=color,
                    )
                )
                fig.update_layout(
                    title=name, yaxis_title=name.split("(")[-1].rstrip(")"), height=300
                )
                figs.append((metric, fig))
        return figs

    # HTML-обёртки (как раньше)
    @staticmethod
    def create_duration_phase_plot(records, norms=None) -> str:
        fig = SleepPlotter.create_duration_phase_figure(records, norms)
        return pio.to_html(fig, full_html=False)

    @staticmethod
    def create_efficiency_plot(records, norms=None) -> str:
        fig = SleepPlotter.create_efficiency_figure(records, norms)
        return pio.to_html(fig, full_html=False)
