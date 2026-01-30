import torch
import torchvision.transforms as transforms
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import time
import os
from typing import Dict, List, Tuple, Any
from sklearn.cluster import KMeans

class BookShelfAnalyzer:
    """Основной класс анализатора книжного шкафа"""
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Используется устройство: {self.device}")
        
        # Инициализация моделей
        self._init_models()
        
        # Трансформации для изображений
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                              std=[0.229, 0.224, 0.225])
        ])
    
    def _init_models(self):
        """Инициализация всех моделей"""
        try:
            print("Загрузка детектора YOLO...")
            
            # Проверяем существование локального файла модели
            model_path = self.config.get('yolo_model_path', 'yolo.pt')
            
            if os.path.exists(model_path):
                print(f"Локальная модель найдена: {model_path}")
                file_size = os.path.getsize(model_path) / (1024*1024)
                print(f"Размер модели: {file_size:.1f} MB")
                self.detector = YOLO(model_path)
                print("Модель YOLO успешно загружена из локального файла")
            else:
                print(f"Локальная модель не найдена: {model_path}")
            
            # Проверяем работу модели
            self._test_detector()
            
        except Exception as e:
            print(f"Ошибка при загрузке моделей: {e}")
            raise
    
    def _test_detector(self):
        """Тестирование детектора"""
        try:
            print("Тестирование детектора...")
            # Создаем тестовое изображение
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            results = self.detector(test_image, verbose=False)
            print("Детектор протестирован успешно")
            
            # Выводим информацию о классах
            if hasattr(self.detector, 'names'):
                print(f"Доступно классов: {len(self.detector.names)}")
                # Ищем класс 'book'
                for class_id, class_name in self.detector.names.items():
                    if 'book' in class_name.lower():
                        print(f"Найден класс книги: ID={class_id}, имя='{class_name}'")
            
        except Exception as e:
            print(f"Ошибка тестирования детектора: {e}")
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Основной метод анализа изображения"""
        start_time = time.time()
        
        try:
            print(f"Анализ изображения: {os.path.basename(image_path)}")
            
            # Загрузка изображения
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Не удалось загрузить изображение: {image_path}")
            
            original_height, original_width = image.shape[:2]
            print(f"Размер изображения: {original_width}x{original_height}")
            
            # Уменьшаем изображение для ускорения обработки
            max_size = 1024
            if max(original_height, original_width) > max_size:
                scale = max_size / max(original_height, original_width)
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                image = cv2.resize(image, (new_width, new_height), 
                                 interpolation=cv2.INTER_LINEAR)
                print(f"Изображение уменьшено до: {new_width}x{new_height}")
            
            # 1. Детектирование книг
            print("Детектирование книг...")
            books, processed_image = self._detect_books(image)
            print(f"Найдено книг: {len(books)}")
            
            # 2. Определение полок
            print("Определение полок...")
            shelves = self._detect_shelves(image, books)
            print(f"Найдено полок: {len(shelves)}")
            
            # 3. Расчет статистики
            print("Расчет статистики...")
            statistics = self._calculate_statistics(books, shelves, original_width, original_height)
            
            # 4. Создание визуализации
            print("Создание визуализации...")
            visualization_path = self._create_visualization(
                image_path, processed_image, books, shelves, statistics
            )
            
            processing_time = time.time() - start_time
            
            
            shelf_type = {
                'type': 'open_shelf',
                'confidence': 0.9
            }
            
            results = {
                'success': True,
                'shelf_type': shelf_type,
                'books': books,
                'shelves': shelves,
                'statistics': statistics,
                'visualization_path': visualization_path,
                'processing_time': processing_time,
                'image_dimensions': {
                    'width': original_width,
                    'height': original_height
                }
            }
            
            print(f"Анализ завершен за {processing_time:.2f} секунд")
            return results
            
        except Exception as e:
            print(f"Ошибка при анализе изображения: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_books(self, image: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Детектирование книг с использованием YOLO"""
        try:
            # Используем YOLO для детекции
            results = self.detector(image, conf=self.config.get('confidence_threshold', 0.5))
            
            books = []
            processed_image = image.copy()
            height, width = image.shape[:2]
            
            # Ищем классы, связанные с книгами
            book_class_ids = []
            if hasattr(self.detector, 'names'):
                for class_id, class_name in self.detector.names.items():
                    if 'book' in class_name.lower() or 'books' in class_name.lower():
                        book_class_ids.append(class_id)
                        print(f"Использую класс для детекции книг: {class_id} - '{class_name}'")
            
            
            if not book_class_ids:
                book_class_ids = list(range(10))
                print(f"Классы книг не найдены, использую первые 10 классов")
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        cls = int(box.cls[0])
                        
                        # Фильтруем объекты по классу и уверенности
                        if cls in book_class_ids and confidence > 0.3:
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            
                            # Проверяем, что bounding box в пределах изображения
                            x1 = max(0, min(x1, width - 1))
                            y1 = max(0, min(y1, height - 1))
                            x2 = max(0, min(x2, width - 1))
                            y2 = max(0, min(y2, height - 1))
                            
                            if x2 > x1 and y2 > y1:  # Проверяем валидность bounding box
                                book_data = {
                                    'bbox': [x1, y1, x2, y2],
                                    'confidence': confidence,
                                    'class_id': cls,
                                    'width': x2 - x1,
                                    'height': y2 - y1,
                                    'area': (x2 - x1) * (y2 - y1)
                                }
                                books.append(book_data)
                                
                                # Рисуем bounding box
                                cv2.rectangle(processed_image, 
                                            (x1, y1), 
                                            (x2, y2),
                                            (0, 255, 0), 2)
                                cv2.putText(processed_image, 
                                          f'Book: {confidence:.2f}',
                                          (x1, y1 - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                          (0, 255, 0), 2)
            
            return books, processed_image
            
        except Exception as e:
            print(f"Ошибка детектирования книг: {e}")
            return [], image
    
    def _detect_shelves(self, image: np.ndarray, books: List[Dict]) -> List[Dict]:
        """Обнаружение полок в книжном шкафу"""
        try:
            height, width = image.shape[:2]
            shelves = []
            
            if not books or len(books) < 2:
                print("Недостаточно книг для определения полок")
                # Создаем одну полку на все изображение
                shelves.append({
                    'shelf_number': 1,
                    'y1': 0,
                    'y2': height,
                    'book_count': len(books),
                    'books': books
                })
                return shelves
            
            # Группируем книги по горизонтальным уровням (полкам)
            book_y_centers = [(b['bbox'][1] + b['bbox'][3]) / 2 for b in books]
            
            # Определяем количество полок
            n_shelves = min(max(2, len(set([int(y // 50) for y in book_y_centers]))), 6)
            print(f"Определение {n_shelves} полок...")
            
            if len(book_y_centers) >= n_shelves:
                # Используем K-means для кластеризации по высоте
                kmeans = KMeans(n_clusters=n_shelves, random_state=42, n_init=10)
                shelf_labels = kmeans.fit_predict(np.array(book_y_centers).reshape(-1, 1))
                
                # Для каждой полки находим границы
                for i in range(n_shelves):
                    shelf_books = [books[j] for j in range(len(books)) if shelf_labels[j] == i]
                    
                    if shelf_books:
                        y_coords = []
                        for book in shelf_books:
                            y_coords.append(book['bbox'][1])  # верх
                            y_coords.append(book['bbox'][3])  # низ
                        
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        # Добавляем отступы
                        padding = height * 0.05
                        shelf_y1 = max(0, int(y_min - padding))
                        shelf_y2 = min(height, int(y_max + padding))
                        
                        shelf_data = {
                            'shelf_number': i + 1,
                            'y1': shelf_y1,
                            'y2': shelf_y2,
                            'height': shelf_y2 - shelf_y1,
                            'book_count': len(shelf_books),
                            'books': shelf_books
                        }
                        shelves.append(shelf_data)
            
            # Сортируем полки по вертикали
            shelves.sort(key=lambda x: x['y1'])
            
            # Нумеруем заново после сортировки
            for i, shelf in enumerate(shelves):
                shelf['shelf_number'] = i + 1
            
            return shelves
            
        except Exception as e:
            print(f"Ошибка обнаружения полок: {e}")
            # Возвращаем одну полку на все изображение
            return [{
                'shelf_number': 1,
                'y1': 0,
                'y2': height,
                'book_count': len(books),
                'books': books
            }]
    
    def _calculate_statistics(self, books: List[Dict], shelves: List[Dict], 
                            width: int, height: int) -> Dict[str, Any]:
        """Расчет статистики заполнения"""
        try:
            total_books = len(books)
            shelf_count = len(shelves)
            
            # Расчет процента заполнения для каждой полки
            fill_percentages = []
            shelf_books_counts = []
            
            for shelf in shelves:
                shelf_books = shelf['books']
                
                if shelf_books:
                    # Считаем суммарную ширину книг на полке
                    total_book_width = sum([b['width'] for b in shelf_books])
                    
                    # Процент заполнения (ширина книг / ширина полки)
                    fill_percentage = min(100, (total_book_width / width) * 100)
                    fill_percentages.append(round(fill_percentage, 2))
                    shelf_books_counts.append(len(shelf_books))
                else:
                    fill_percentages.append(0)
                    shelf_books_counts.append(0)
            
            # Средний процент заполнения
            average_fill = round(np.mean(fill_percentages), 2) if fill_percentages else 0
            
            # Плотность книг
            total_area = width * height
            book_area = sum([b['area'] for b in books]) if books else 0
            density_percentage = round((book_area / total_area) * 100, 2) if total_area > 0 else 0
            
            return {
                'total_books': total_books,
                'shelf_count': shelf_count,
                'fill_percentages': fill_percentages,
                'average_fill': average_fill,
                'density_percentage': density_percentage,
                'book_distribution': {
                    'shelf_counts': shelf_books_counts,
                    'fill_percentages': fill_percentages
                },
                'image_area': total_area,
                'total_book_area': int(book_area)
            }
            
        except Exception as e:
            print(f"Ошибка расчета статистики: {e}")
            return {
                'total_books': len(books),
                'shelf_count': len(shelves),
                'fill_percentages': [],
                'average_fill': 0,
                'density_percentage': 0,
                'error': str(e)
            }
    
    def _create_visualization(self, original_path: str, processed_image: np.ndarray,
                            books: List[Dict], shelves: List[Dict],
                            statistics: Dict) -> str:
        """Создание визуализации с результатами"""
        try:
            # Создаем визуализацию
            vis_image = processed_image.copy()
            height, width = vis_image.shape[:2]
            
            # Рисуем полки
            colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0), 
                     (255, 0, 255), (0, 255, 255)]
            
            for i, shelf in enumerate(shelves):
                color = colors[i % len(colors)]
                cv2.rectangle(vis_image,
                            (0, shelf['y1']),
                            (width, shelf['y2']),
                            color, 2)
                
                # Подпись полки
                if i < len(statistics['fill_percentages']):
                    fill_percent = statistics['fill_percentages'][i]
                    label = f"Полка {i+1}: {fill_percent}% ({shelf['book_count']} книг)"
                    cv2.putText(vis_image, label,
                              (10, shelf['y1'] + 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                              color, 2)
            
            # Добавляем статистику на изображение
            stats_text = [
                f"Всего книг: {statistics['total_books']}",
                f"Полок: {statistics['shelf_count']}",
                f"Среднее заполнение: {statistics['average_fill']}%",
                f"Плотность: {statistics['density_percentage']}%"
            ]
            
            y_offset = 50
            for text in stats_text:
                cv2.putText(vis_image, text,
                          (width - 300, y_offset),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                          (255, 255, 255), 2)
                cv2.putText(vis_image, text,
                          (width - 301, y_offset - 1),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                          (0, 0, 0), 2)
                y_offset += 30
            
            # Сохраняем результат
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(original_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_analyzed_{timestamp}{ext}"
            output_path = os.path.join(self.config['processed_folder'], output_filename)
            
            cv2.imwrite(output_path, vis_image)
            print(f"Визуализация сохранена: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"Ошибка создания визуализации: {e}")
            return original_path