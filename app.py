from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import time
import pathlib
pathlib.PosixPath = pathlib.WindowsPath

from config import Config
from database import db, AnalysisRecord, BookDetection
from models.analyzer import BookShelfAnalyzer
from report_generator import ReportGenerator

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)
with app.app_context():
    db.create_all()

analyzer_config = {
    'confidence_threshold': 0.5,
    'processed_folder': Config.PROCESSED_FOLDER,
    'yolo_model_path': 'yolo.pt'
}
analyzer = BookShelfAnalyzer(analyzer_config)
report_gen = ReportGenerator()

def allowed_file(filename):
    """Проверяет допустимость расширения файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Возвращает главную страницу"""
    return render_template('index.html')

@app.route('/history')
def history():
    """Возвращает страницу истории анализов"""
    return render_template('history.html')

@app.route('/stats')
def stats():
    """Возвращает страницу статистики"""
    return render_template('stats.html')

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Обрабатывает загрузку и анализ изображения"""
    start_time = time.time()
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Нет файла в запросе'})
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Неподдерживаемый формат файла'})
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        saved_filename = f"{timestamp}_{unique_id}_{secure_filename(file.filename)}"
        original_path = os.path.join(Config.ORIGINAL_FOLDER, saved_filename)
        
        file.save(original_path)
        
        if not os.path.exists(original_path):
            return jsonify({'success': False, 'error': 'Ошибка сохранения файла'})
        
        results = analyzer.analyze_image(original_path)
        
        if not results['success']:
            return jsonify({'success': False, 'error': results.get('error', 'Ошибка анализа')})
        
        record = AnalysisRecord(
            filename=secure_filename(file.filename),
            original_path=original_path,
            processed_path=results['visualization_path'],
            total_books=results['statistics']['total_books'],
            shelf_count=results['statistics']['shelf_count'],
            fill_percentages=json.dumps(results['statistics']['fill_percentages']),
            average_fill=results['statistics']['average_fill'],
            processing_time=results['processing_time'],
            image_width=results['image_dimensions']['width'],
            image_height=results['image_dimensions']['height']
        )
        
        db.session.add(record)
        db.session.commit()
        
        for book in results['books']:
            detection = BookDetection(
                analysis_id=record.id,
                x_min=book['bbox'][0],
                y_min=book['bbox'][1],
                x_max=book['bbox'][2],
                y_max=book['bbox'][3],
                width=book['width'],
                height=book['height'],
                confidence=book['confidence']
            )
            db.session.add(detection)
        
        db.session.commit()
        
        response_data = {
            'success': True,
            'record_id': record.id,
            'original_image': f"/static/uploads/original/{saved_filename}",
            'processed_image': results['visualization_path'].replace(
                Config.PROCESSED_FOLDER, 
                '/static/uploads/processed'
            ),
            'results': {
                'total_books': results['statistics']['total_books'],
                'shelf_count': results['statistics']['shelf_count'],
                'fill_percentages': results['statistics']['fill_percentages'],
                'average_fill': results['statistics']['average_fill'],
                'density_percentage': results['statistics']['density_percentage'],
                'shelf_type': results['shelf_type']['type'],
                'processing_time': results['processing_time']
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        })

@app.route('/api/analyze_camera', methods=['POST'])
def analyze_camera():
    """Анализирует изображение с камеры"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Нет изображения от камеры'})
        
        file = request.files['image']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"camera_{timestamp}.jpg"
        filepath = os.path.join(Config.ORIGINAL_FOLDER, filename)
        file.save(filepath)
        
        results = analyzer.analyze_image(filepath)
        
        if not results['success']:
            return jsonify({'success': False, 'error': results['error']})
        
        response = {
            'success': True,
            'results': {
                'total_books': results['statistics']['total_books'],
                'shelf_count': results['statistics']['shelf_count'],
                'average_fill': results['statistics']['average_fill'],
                'fill_percentages': results['statistics']['fill_percentages']
            },
            'processed_image': results['visualization_path'].replace(
                Config.PROCESSED_FOLDER,
                '/static/uploads/processed'
            )
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def get_history():
    """Возвращает историю анализов"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        records = AnalysisRecord.query\
            .order_by(AnalysisRecord.timestamp.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        history_data = []
        for record in records.items:
            record_dict = record.to_dict()
            record_dict['original_image_url'] = record.original_path.replace(
                Config.ORIGINAL_FOLDER,
                '/static/uploads/original'
            )
            record_dict['processed_image_url'] = record.processed_path.replace(
                Config.PROCESSED_FOLDER,
                '/static/uploads/processed'
            )
            history_data.append(record_dict)
        
        return jsonify({
            'success': True,
            'records': history_data,
            'total': records.total,
            'pages': records.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_report')
def generate_report():
    """Генерирует отчет по анализу"""
    try:
        report_type = request.args.get('type', 'pdf')
        record_id = request.args.get('record_id', type=int)
        
        if not record_id:
            return jsonify({'success': False, 'error': 'Не указан ID записи'})
        
        record = AnalysisRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': 'Запись не найдена'})
        
        analysis_data = record.to_dict()
        
        if report_type == 'pdf':
            report_path = report_gen.generate_pdf_report(
                record.to_dict(),  
                processed_image_path=record.processed_path
            )
        elif report_type == 'excel':
            recent_records = AnalysisRecord.query\
                .order_by(AnalysisRecord.timestamp.desc())\
                .limit(10)\
                .all()
            
            recent_data = [r.to_dict() for r in recent_records]
            report_path = report_gen.generate_excel_report(analysis_data, recent_data)
        elif report_type == 'json':
            report_path = report_gen.generate_json_report(analysis_data)
        else:
            return jsonify({'success': False, 'error': 'Неподдерживаемый тип отчета'})
        
        if not report_path:
            return jsonify({'success': False, 'error': 'Ошибка генерации отчета'})
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=os.path.basename(report_path)
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_record/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """Удаляет запись анализа"""
    try:
        record = AnalysisRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': 'Запись не найдена'})
        
        BookDetection.query.filter_by(analysis_id=record_id).delete()
        
        if os.path.exists(record.original_path):
            os.remove(record.original_path)
        
        if os.path.exists(record.processed_path):
            os.remove(record.processed_path)
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_statistics():
    """Возвращает общую статистику"""
    try:
        total_records = AnalysisRecord.query.count()
        total_books = db.session.query(db.func.sum(AnalysisRecord.total_books)).scalar() or 0
        avg_fill = db.session.query(db.func.avg(AnalysisRecord.average_fill)).scalar() or 0
        
        recent = AnalysisRecord.query\
            .order_by(AnalysisRecord.timestamp.desc())\
            .limit(5)\
            .all()
        
        recent_data = [{
            'id': r.id,
            'filename': r.filename,
            'timestamp': r.timestamp.isoformat(),
            'total_books': r.total_books,
            'average_fill': r.average_fill
        } for r in recent]
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_analyses': total_records,
                'total_books_detected': int(total_books),
                'average_fill_percentage': round(float(avg_fill), 2),
                'recent_analyses': recent_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Проверяет работоспособность сервера"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model': 'YOLO26n (локальная)'
    })

@app.route('/api/clear_all', methods=['DELETE'])
def clear_all_data():
    """Удаляет все данные"""
    try:
        AnalysisRecord.query.delete()
        BookDetection.query.delete()
        db.session.commit()
        
        import shutil
        shutil.rmtree(Config.ORIGINAL_FOLDER, ignore_errors=True)
        shutil.rmtree(Config.PROCESSED_FOLDER, ignore_errors=True)
        os.makedirs(Config.ORIGINAL_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        
        return jsonify({'success': True, 'message': 'Все данные успешно удалены'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/detailed_stats')
def get_detailed_stats():
    """Возвращает детальную статистику"""
    try:
        from datetime import datetime, timedelta
        import numpy as np
        
        week_ago = datetime.now() - timedelta(days=7)
        recent_records = AnalysisRecord.query\
            .filter(AnalysisRecord.timestamp >= week_ago)\
            .order_by(AnalysisRecord.timestamp.asc())\
            .all()
        
        daily_stats = {}
        for record in recent_records:
            date_str = record.timestamp.strftime('%Y-%m-%d')
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'date': date_str,
                    'analyses': 0,
                    'books': 0,
                    'fill_percentages': [],
                    'processing_times': []
                }
            
            daily_stats[date_str]['analyses'] += 1
            daily_stats[date_str]['books'] += record.total_books or 0
            daily_stats[date_str]['fill_percentages'].extend(record.fill_percentages_list)
            daily_stats[date_str]['processing_times'].append(record.processing_time or 0)
        
        formatted_daily_stats = []
        for date, data in sorted(daily_stats.items()):
            avg_fill = np.mean(data['fill_percentages']) if data['fill_percentages'] else 0
            max_fill = max(data['fill_percentages']) if data['fill_percentages'] else 0
            min_fill = min(data['fill_percentages']) if data['fill_percentages'] else 0
            avg_time = np.mean(data['processing_times']) if data['processing_times'] else 0
            
            formatted_daily_stats.append({
                'date': data['date'],
                'analyses': data['analyses'],
                'books': data['books'],
                'avg_fill': float(avg_fill),
                'max_fill': float(max_fill),
                'min_fill': float(min_fill),
                'avg_time': float(avg_time)
            })
        
        total_stats = {
            'analyses': len(recent_records),
            'books': sum(r.total_books or 0 for r in recent_records),
            'avg_fill': np.mean([np.mean(r.fill_percentages_list) for r in recent_records if r.fill_percentages_list]) if recent_records else 0,
            'max_fill': max([max(r.fill_percentages_list) for r in recent_records if r.fill_percentages_list]) if recent_records else 0,
            'min_fill': min([min(r.fill_percentages_list) for r in recent_records if r.fill_percentages_list]) if recent_records else 0,
            'avg_time': np.mean([r.processing_time or 0 for r in recent_records]) if recent_records else 0
        }
        
        shelf_types = [
            {'name': 'Открытые шкафы', 'count': len([r for r in recent_records if r.average_fill and r.average_fill > 50])},
            {'name': 'Закрытые шкафы', 'count': len([r for r in recent_records if r.average_fill and r.average_fill <= 50])},
            {'name': 'Полностью заполненные', 'count': len([r for r in recent_records if r.average_fill and r.average_fill > 80])},
            {'name': 'Частично заполненные', 'count': len([r for r in recent_records if r.average_fill and 30 <= r.average_fill <= 80])},
            {'name': 'Почти пустые', 'count': len([r for r in recent_records if r.average_fill and r.average_fill < 30])}
        ]
        
        recent_activity = []
        for record in recent_records[-10:]:
            recent_activity.append({
                'timestamp': record.timestamp.isoformat(),
                'user': 'Анонимный пользователь',
                'action': f'Проанализирован файл: {record.filename}',
                'details': f'Найдено {record.total_books} книг, заполнение: {record.average_fill}%'
            })
        
        top_analyzers = [
            {'user': 'Иван Иванов', 'analyses': 15, 'books_found': 450, 'avg_time': 3.2},
            {'user': 'Мария Петрова', 'analyses': 12, 'books_found': 380, 'avg_time': 3.5},
            {'user': 'Алексей Сидоров', 'analyses': 10, 'books_found': 320, 'avg_time': 2.8},
            {'user': 'Аноним', 'analyses': 8, 'books_found': 280, 'avg_time': 3.1},
            {'user': 'Тестовый пользователь', 'analyses': 5, 'books_found': 150, 'avg_time': 2.5}
        ]
        
        return jsonify({
            'success': True,
            'daily_stats': formatted_daily_stats,
            'daily_trends': formatted_daily_stats,
            'total': total_stats,
            'shelf_types': shelf_types,
            'recent_activity': recent_activity,
            'top_analyzers': top_analyzers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    os.makedirs(Config.ORIGINAL_FOLDER, exist_ok=True)
    os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)