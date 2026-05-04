import os
import uuid
import plotly.io as pio
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
from werkzeug.utils import secure_filename
from config import Config
from adapters.csv_loader import CSVLoader, CSVLoadError
from domain.services import SleepAnalysisService
from visualization.plotter import SleepPlotter
from adapters.docx_generator import DocxGenerator


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    return app


app = create_app()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        mode = request.form.get("mode", "file")

        # ============================================================
        # Загрузка файла
        # ============================================================
        if mode == "file":
            if (
                "csvfile" not in request.files
                or request.files["csvfile"].filename == ""
            ):
                flash("Выберите файл CSV")
                return redirect(request.url)
            file = request.files["csvfile"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(filepath)
                # Удаляем предыдущий CSV, если был
                old_csv = session.get("csv_path")
                if old_csv and os.path.exists(old_csv):
                    os.remove(old_csv)
                session["csv_path"] = filepath
                return redirect(url_for("report"))
            else:
                flash("Разрешены только файлы .csv")
                return redirect(request.url)

        # ============================================================
        # Ручной ввод
        # ============================================================
        elif mode == "manual":
            dates = request.form.getlist("date")
            starts = request.form.getlist("sleep_start")
            ends = request.form.getlist("sleep_end")
            deeps = request.form.getlist("deep_sleep_minutes")
            lights = request.form.getlist("light_sleep_minutes")
            rems = request.form.getlist("rem_minutes")
            awks = request.form.getlist("awakenings")

            filled_indices = [i for i, d in enumerate(dates) if d.strip()]
            if not filled_indices:
                flash("Введите хотя бы один день")
                return redirect(request.url)

            age_val = request.form.get("age", "").strip()
            gender_val = request.form.get("gender", "").strip().upper()
            if gender_val not in ("M", "F"):
                gender_val = ""

            headers = [
                "date",
                "sleep_start",
                "sleep_end",
                "deep_sleep_minutes",
                "light_sleep_minutes",
                "rem_minutes",
                "awakenings",
            ]

            day_opt_fields = [
                "heart_rate_avg",
                "hr_variability_avg",
                "respiratory_rate_avg",
                "movement_index",
                "sleep_latency_minutes",
                "sleep_quality_rating",
            ]

            opt_data = {}
            for fname in day_opt_fields:
                vals = request.form.getlist(fname)
                while len(vals) < len(dates):
                    vals.append("")
                if any(v.strip() for v in vals):
                    opt_data[fname] = vals
                    headers.append(fname)

            if age_val:
                headers.append("age")
            if gender_val:
                headers.append("gender")

            lines = [",".join(headers)]
            for i in filled_indices:
                row = [
                    dates[i].strip(),
                    starts[i].strip(),
                    ends[i].strip(),
                    deeps[i].strip(),
                    lights[i].strip(),
                    rems[i].strip(),
                    awks[i].strip(),
                ]
                for fname in day_opt_fields:
                    if fname in opt_data:
                        row.append(opt_data[fname][i].strip())
                if "age" in headers:
                    row.append(age_val)
                if "gender" in headers:
                    row.append(gender_val)
                lines.append(",".join(row))

            csv_content = "\n".join(lines)

            unique_name = f"{uuid.uuid4()}_manual.csv"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(csv_content)
            # Удаляем предыдущий CSV, если был
            old_csv = session.get("csv_path")
            if old_csv and os.path.exists(old_csv):
                os.remove(old_csv)
            session["csv_path"] = filepath
            return redirect(url_for("report"))

    return render_template("upload.html")


@app.route("/report")
def report():
    csv_path = session.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        flash("Сначала загрузите CSV-файл")
        return redirect(url_for("upload"))

    try:
        loader = CSVLoader()
        records = loader.load(csv_path)
        service = SleepAnalysisService()
        analysis = service.analyze(records)

        norms = (
            service._get_sleep_norms(analysis.user_age, analysis.user_gender)
            if analysis.user_age
            else service._get_sleep_norms(None, None)
        )

        plotter = SleepPlotter()
        fig_main = plotter.create_duration_phase_figure(analysis.records, norms)
        fig_eff = plotter.create_efficiency_figure(analysis.records, norms)
        physio_figs = plotter.create_physio_figures(analysis.records)

        # Только HTML для веб‑отчёта
        duration_phase_html = pio.to_html(fig_main, full_html=False)
        efficiency_html = pio.to_html(fig_eff, full_html=False)
        physio_plots = [
            (name, pio.to_html(fig, full_html=False)) for name, fig in physio_figs
        ]

        # Данные для последующего скачивания DOCX
        session["analysis_dict"] = analysis.to_dict()
        session["num_records"] = len(analysis.records)
        # csv_path остаётся в сессии для повторных скачиваний

        return render_template(
            "report.html",
            analysis=analysis,
            duration_phase_html=duration_phase_html,
            efficiency_html=efficiency_html,
            physio_plots=physio_plots,
        )

    except CSVLoadError as e:
        flash(f"Ошибка в CSV: {e}")
    except Exception as e:
        flash(f"Ошибка анализа: {e}")

    # При ошибке удаляем файл и очищаем сессию
    if os.path.exists(csv_path):
        os.remove(csv_path)
    session.pop("csv_path", None)
    session.pop("analysis_dict", None)
    session.pop("num_records", None)
    return redirect(url_for("upload"))


@app.route("/download_report")
def download_report():
    analysis_dict = session.get("analysis_dict")
    csv_path = session.get("csv_path")
    num_records = session.get("num_records", 1)

    if not analysis_dict or not csv_path or not os.path.exists(csv_path):
        flash("Нет данных для отчёта. Сначала загрузите данные.")
        return redirect(url_for("upload"))

    try:
        # Генерируем DOCX без изображений (быстро и без зависаний)
        buf = DocxGenerator.generate(
            analysis_dict,
            num_records=num_records,
            images=None
        )
        return send_file(
            buf,
            as_attachment=True,
            download_name="sleep_report.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        flash(f"Ошибка при создании отчёта: {e}")
        return redirect(url_for("upload"))


@app.route("/legend")
def legend():
    return render_template("legend.html")


if __name__ == "__main__":
    app.run(debug=True)