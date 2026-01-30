from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class AnalysisRecord(db.Model):
    """Модель для хранения истории анализов"""
    __tablename__ = 'analysis_records'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    filename = db.Column(db.String(256))
    original_path = db.Column(db.String(512))
    processed_path = db.Column(db.String(512))
    
    # Результаты анализа
    total_books = db.Column(db.Integer)
    shelf_count = db.Column(db.Integer)
    fill_percentages = db.Column(db.Text)  # JSON массив процентов заполнения
    average_fill = db.Column(db.Float)
    
    # Дополнительные данные
    processing_time = db.Column(db.Float)
    image_width = db.Column(db.Integer)
    image_height = db.Column(db.Integer)
    
    def __init__(self, **kwargs):
        super(AnalysisRecord, self).__init__(**kwargs)
        if self.fill_percentages and isinstance(self.fill_percentages, list):
            self.fill_percentages = json.dumps(self.fill_percentages)
    
    def to_dict(self):
        """Преобразование объекта в словарь"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'filename': self.filename,
            'original_path': self.original_path,
            'processed_path': self.processed_path,
            'total_books': self.total_books,
            'shelf_count': self.shelf_count,
            'fill_percentages': json.loads(self.fill_percentages) if self.fill_percentages else [],
            'average_fill': self.average_fill,
            'processing_time': self.processing_time,
            'image_width': self.image_width,
            'image_height': self.image_height
        }
    
    @property
    def fill_percentages_list(self):
        """Возвращает fill_percentages как список"""
        if isinstance(self.fill_percentages, str):
            try:
                return json.loads(self.fill_percentages)
            except:
                return []
        elif isinstance(self.fill_percentages, list):
            return self.fill_percentages
        return []

class BookDetection(db.Model):
    """Модель для хранения информации о детектированных книгах"""
    __tablename__ = 'book_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_records.id'))
    
    # Координаты bounding box
    x_min = db.Column(db.Integer)
    y_min = db.Column(db.Integer)
    x_max = db.Column(db.Integer)
    y_max = db.Column(db.Integer)
    
    # Размеры
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    
    # Уверенность
    confidence = db.Column(db.Float)
    
    # Принадлежность к полке
    shelf_number = db.Column(db.Integer)
    
    # Связь с записью анализа
    analysis = db.relationship('AnalysisRecord', backref='detections')