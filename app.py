import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from config import Config
from adapters.csv_loader import CSVLoader, CSVLoadError
from domain.services import SleepAnalysisService
from visualization.plotter import SleepPlotter

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    return app

app = create_app()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'csvfile' not in request.files:
            flash('Файл не выбран')
            return redirect(request.url)
        file = request.files['csvfile']
        if file.filename == '':
            flash('Файл не выбран')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(filepath)
            session['csv_path'] = filepath
            return redirect(url_for('report'))
        else:
            flash('Разрешены только файлы CSV')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/report')
def report():
    csv_path = session.get('csv_path')
    if not csv_path or not os.path.exists(csv_path):
        flash('Сначала загрузите CSV-файл')
        return redirect(url_for('upload'))
    try:
        loader = CSVLoader()
        records = loader.load(csv_path)
        service = SleepAnalysisService()
        analysis = service.analyze(records)
        plotter = SleepPlotter()
        duration_phase_html = plotter.create_duration_phase_plot(analysis.records)
        efficiency_html = plotter.create_efficiency_plot(analysis.records)
        # Удаляем файл после анализа, чтобы не засорять папку
        os.remove(csv_path)
        session.pop('csv_path', None)
        return render_template('report.html',
                               analysis=analysis,
                               duration_phase_html=duration_phase_html,
                               efficiency_html=efficiency_html)
    except CSVLoadError as e:
        flash(f'Ошибка в CSV: {e}')
        if os.path.exists(csv_path):
            os.remove(csv_path)
        session.pop('csv_path', None)
        return redirect(url_for('upload'))
    except Exception as e:
        flash(f'Ошибка анализа: {e}')
        if os.path.exists(csv_path):
            os.remove(csv_path)
        session.pop('csv_path', None)
        return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True)