import os

class Config:
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bookshelf-analyzer-secret-key'
    
    # Настройки базы данных
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "bookshelf.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Папки для загрузки
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ORIGINAL_FOLDER = os.path.join(UPLOAD_FOLDER, 'original')
    PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
    
    # Разрешенные расширения файлов
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
    
    # Максимальный размер файла (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Настройки моделей
    MODEL_PATHS = {
        'yolo': 'yolo.pt', 
    }
    
    # Пороги уверенности
    CONFIDENCE_THRESHOLD = 0.5
    IOU_THRESHOLD = 0.45
    
    @staticmethod
    def init_app(app):
        # Создание необходимых папок
        os.makedirs(Config.ORIGINAL_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs('reports', exist_ok=True)