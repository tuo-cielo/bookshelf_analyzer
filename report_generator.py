import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
import json
import numpy as np

class ReportGenerator:
    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def _prepare_analysis_data_from_db_record(self, db_record: dict) -> dict:
        """Подготавливает данные из записи базы данных для генерации отчетов"""
        try:
            # Получаем fill_percentages из записи БД
            fill_percentages = []
            if 'fill_percentages' in db_record:
                # Может быть строкой JSON или уже списком
                if isinstance(db_record['fill_percentages'], str):
                    try:
                        fill_percentages = json.loads(db_record['fill_percentages'])
                    except:
                        fill_percentages = []
                elif isinstance(db_record['fill_percentages'], list):
                    fill_percentages = db_record['fill_percentages']
            
            # Получаем распределение книг по полкам
            shelf_counts = []
            if 'shelf_counts' in db_record.get('statistics', {}):
                shelf_counts = db_record['statistics'].get('shelf_counts', [])
            else:
                # Если нет конкретного распределения, создаем равномерное
                total_books = db_record.get('total_books', 0)
                shelf_count = db_record.get('shelf_count', 1)
                if shelf_count > 0 and total_books > 0:
                    shelf_counts = [int(total_books / shelf_count)] * shelf_count
                    # Добавляем остаток к первой полке
                    remainder = total_books % shelf_count
                    if remainder > 0:
                        shelf_counts[0] += remainder
                else:
                    shelf_counts = []
            
            # Если fill_percentages пустые, создаем на основе распределения
            if not fill_percentages and shelf_counts:
                total_books = sum(shelf_counts)
                if total_books > 0:
                    fill_percentages = [count / total_books * 100 for count in shelf_counts]
            
            # Создаем структуру данных для отчетов
            analysis_data = {
                'timestamp': db_record.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'filename': db_record.get('filename', 'unknown'),
                'processing_time': db_record.get('processing_time', 0),
                'image_width': db_record.get('image_width', 0),
                'image_height': db_record.get('image_height', 0),
                'statistics': {
                    'total_books': db_record.get('total_books', 0),
                    'shelf_count': db_record.get('shelf_count', 0),
                    'average_fill': db_record.get('average_fill', 0),
                    'density_percentage': db_record.get('density_percentage', 0),
                    'fill_percentages': fill_percentages,
                    'book_distribution': {
                        'shelf_counts': shelf_counts,
                        'fill_percentages': fill_percentages
                    }
                }
            }
            
            return analysis_data
            
        except Exception as e:
            print(f"Ошибка подготовки данных из БД: {e}")
            # Возвращаем минимальные данные
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': db_record.get('filename', 'unknown'),
                'processing_time': db_record.get('processing_time', 0),
                'image_width': db_record.get('image_width', 0),
                'image_height': db_record.get('image_height', 0),
                'statistics': {
                    'total_books': db_record.get('total_books', 0),
                    'shelf_count': db_record.get('shelf_count', 0),
                    'average_fill': db_record.get('average_fill', 0),
                    'density_percentage': db_record.get('density_percentage', 0),
                    'fill_percentages': [],
                    'book_distribution': {
                        'shelf_counts': [],
                        'fill_percentages': []
                    }
                }
            }
    
    def _prepare_analysis_data_from_analyzer(self, analyzer_results: dict) -> dict:
        """Подготавливает данные из анализатора для генерации отчетов"""
        try:
            statistics = analyzer_results.get('statistics', {})
            shelves = analyzer_results.get('shelves', [])
            
            # Извлекаем данные о полках из результатов анализатора
            fill_percentages = statistics.get('fill_percentages', [])
            shelf_counts = statistics.get('book_distribution', {}).get('shelf_counts', [])
            
            # Если в анализаторе нет fill_percentages, создаем их
            if not fill_percentages and shelves:
                fill_percentages = []
                shelf_counts = []
                for shelf in shelves:
                    shelf_counts.append(shelf.get('book_count', 0))
                    # Процент заполнения на основе высоты полки
                    if 'height' in shelf:
                        fill_percentages.append(min(100, shelf['height'] / 200 * 100))
                    else:
                        fill_percentages.append(0)
            
            analysis_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': os.path.basename(analyzer_results.get('image_path', 'unknown')),
                'processing_time': analyzer_results.get('processing_time', 0),
                'image_width': analyzer_results.get('image_dimensions', {}).get('width', 0),
                'image_height': analyzer_results.get('image_dimensions', {}).get('height', 0),
                'statistics': {
                    'total_books': statistics.get('total_books', 0),
                    'shelf_count': statistics.get('shelf_count', 0),
                    'average_fill': statistics.get('average_fill', 0),
                    'density_percentage': statistics.get('density_percentage', 0),
                    'fill_percentages': fill_percentages,
                    'book_distribution': {
                        'shelf_counts': shelf_counts,
                        'fill_percentages': fill_percentages
                    }
                }
            }
            
            return analysis_data
            
        except Exception as e:
            print(f"Ошибка подготовки данных из анализатора: {e}")
            return self._prepare_analysis_data_from_db_record({})
    
    def _prepare_analysis_data(self, input_data: dict) -> dict:
        """Универсальный метод подготовки данных"""
        # Определяем тип входных данных
        if 'statistics' in input_data and 'shelves' in input_data:
            # Данные от анализатора
            return self._prepare_analysis_data_from_analyzer(input_data)
        elif 'total_books' in input_data and 'shelf_count' in input_data:
            # Данные из базы данных
            return self._prepare_analysis_data_from_db_record(input_data)
        else:
            # Неизвестный формат, пытаемся обработать
            print(f"Неизвестный формат данных: {list(input_data.keys())}")
            return self._prepare_analysis_data_from_db_record(input_data)
    
    def generate_pdf_report(self, input_data: dict,
                          original_image_path: str = None,
                          processed_image_path: str = None) -> str:
        try:
            # Подготавливаем данные (универсальный метод)
            analysis_data = self._prepare_analysis_data(input_data)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bookshelf_analysis_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            
            # Заголовок
            elements.append(Paragraph("Bookshelf Analysis Report", self.styles['CustomTitle']))
            elements.append(Spacer(1, 20))
            
            # Информация об анализе
            elements.append(Paragraph("Analysis Information", self.styles['CustomHeading2']))
            
            analysis_info = [
                ["Analysis Date:", analysis_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
                ["File Name:", analysis_data.get('filename', 'N/A')],
                ["Processing Time:", f"{analysis_data.get('processing_time', 0):.2f} sec"],
                ["Image Size:", f"{analysis_data.get('image_width', 0)}x{analysis_data.get('image_height', 0)}"]
            ]
            
            info_table = Table(analysis_info, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Статистика полок
            elements.append(Paragraph("Shelf Statistics", self.styles['CustomHeading2']))
            
            stats = analysis_data.get('statistics', {})
            statistics_data = [
                ["Total Books:", str(stats.get('total_books', 0))],
                ["Number of Shelves:", str(stats.get('shelf_count', 0))],
                ["Average Fill Percentage:", f"{stats.get('average_fill', 0):.2f}%"],
                ["Density Percentage:", f"{stats.get('density_percentage', 0):.2f}%"]
            ]
            
            stats_table = Table(statistics_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Подробный анализ по полкам
            fill_percentages = stats.get('fill_percentages', [])
            shelf_counts = stats.get('book_distribution', {}).get('shelf_counts', [])
            
            if fill_percentages and shelf_counts:
                elements.append(Paragraph("Shelf-by-Shelf Analysis", self.styles['CustomHeading2']))
                
                shelf_data = [["Shelf Number", "Books Count", "Fill Percentage"]]
                
                for i, (count, fill) in enumerate(zip(shelf_counts, fill_percentages)):
                    shelf_data.append([
                        f"Shelf {i+1}",
                        str(count),
                        f"{fill:.2f}%"
                    ])
                
                shelf_table = Table(shelf_data, colWidths=[2*inch, 2*inch, 2*inch])
                shelf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(shelf_table)
                elements.append(Spacer(1, 20))
            elif fill_percentages:
                # Если есть только fill_percentages без counts
                elements.append(Paragraph("Shelf-by-Shelf Analysis", self.styles['CustomHeading2']))
                
                shelf_data = [["Shelf Number", "Fill Percentage"]]
                
                for i, fill in enumerate(fill_percentages):
                    shelf_data.append([
                        f"Shelf {i+1}",
                        f"{fill:.2f}%"
                    ])
                
                shelf_table = Table(shelf_data, colWidths=[3*inch, 3*inch])
                shelf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(shelf_table)
                elements.append(Spacer(1, 20))
            
            # Визуализация
            if processed_image_path and os.path.exists(processed_image_path):
                elements.append(Paragraph("Analysis Visualization", self.styles['CustomHeading2']))
                
                try:
                    img = Image(processed_image_path, width=5*inch, height=3.75*inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph("Figure 1: Analysis results with detected shelves and books", 
                                            self.styles['CustomNormal']))
                except Exception as img_error:
                    print(f"Ошибка загрузки изображения для отчета: {img_error}")
                    elements.append(Paragraph("Визуализация недоступна", self.styles['CustomNormal']))
            
            # Заключение
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Conclusion", self.styles['CustomHeading2']))
            
            total_books = stats.get('total_books', 0)
            shelf_count = stats.get('shelf_count', 0)
            avg_fill = stats.get('average_fill', 0)
            
            conclusion_text = f"Analysis detected {total_books} books distributed across {shelf_count} shelves. "
            conclusion_text += f"The average shelf fill percentage is {avg_fill:.2f}%."
            
            if fill_percentages:
                max_fill = max(fill_percentages) if fill_percentages else 0
                min_fill = min(fill_percentages) if fill_percentages else 0
                max_shelf_idx = fill_percentages.index(max_fill) + 1 if max_fill in fill_percentages else 0
                min_shelf_idx = fill_percentages.index(min_fill) + 1 if min_fill in fill_percentages else 0
                
                if max_shelf_idx > 0 and min_shelf_idx > 0:
                    conclusion_text += f" Shelf {max_shelf_idx} is the most filled ({max_fill:.2f}%), "
                    conclusion_text += f"while shelf {min_shelf_idx} is the least filled ({min_fill:.2f}%)."
            
            elements.append(Paragraph(conclusion_text, self.styles['CustomNormal']))
            
          
            elements.append(Spacer(1, 30))
            footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            elements.append(Paragraph(footer_text, 
                                    ParagraphStyle(
                                        name='Footer',
                                        fontSize=8,
                                        alignment=2,
                                        textColor=colors.gray
                                    )))
            
            doc.build(elements)
            
            print(f"PDF report created: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error creating PDF report: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_excel_report(self, input_data: dict,
                            include_multiple: list[dict] = None) -> str:
        try:
            # Подготавливаем данные
            analysis_data = self._prepare_analysis_data(input_data)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bookshelf_analysis_{timestamp}.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Основные данные
                main_data = {
                    'Parameter': [
                        'Analysis Date',
                        'File Name',
                        'Total Books',
                        'Number of Shelves',
                        'Average Fill Percentage',
                        'Density Percentage',
                        'Processing Time (sec)',
                        'Image Width',
                        'Image Height'
                    ],
                    'Value': [
                        analysis_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        analysis_data.get('filename', 'N/A'),
                        analysis_data.get('statistics', {}).get('total_books', 0),
                        analysis_data.get('statistics', {}).get('shelf_count', 0),
                        analysis_data.get('statistics', {}).get('average_fill', 0),
                        analysis_data.get('statistics', {}).get('density_percentage', 0),
                        analysis_data.get('processing_time', 0),
                        analysis_data.get('image_width', 0),
                        analysis_data.get('image_height', 0)
                    ]
                }
                
                df_main = pd.DataFrame(main_data)
                df_main.to_excel(writer, sheet_name='Main Data', index=False)
                
                # Данные по полкам
                fill_percentages = analysis_data.get('statistics', {}).get('fill_percentages', [])
                shelf_counts = analysis_data.get('statistics', {}).get('book_distribution', {}).get('shelf_counts', [])
                
                if fill_percentages:
                    if not shelf_counts:
                        total_books = analysis_data.get('statistics', {}).get('total_books', 0)
                        if total_books > 0:
                            total_fill = sum(fill_percentages)
                            if total_fill > 0:
                                shelf_counts = [int((fill / total_fill) * total_books) for fill in fill_percentages]
                    
                    shelf_data = {
                        'Shelf Number': list(range(1, len(fill_percentages) + 1)),
                        'Book Count': shelf_counts[:len(fill_percentages)] if shelf_counts else [0] * len(fill_percentages),
                        'Fill Percentage': fill_percentages,
                        'Fill Status': [
                            'High' if p > 80 else 'Medium' if p > 50 else 'Low'
                            for p in fill_percentages
                        ]
                    }
                    
                    df_shelves = pd.DataFrame(shelf_data)
                    df_shelves.to_excel(writer, sheet_name='Shelf Data', index=False)
                
                # История анализов
                if include_multiple:
                    history_data = []
                    for record in include_multiple:
                        # Подготавливаем данные для каждой записи
                        record_data = self._prepare_analysis_data(record)
                        history_data.append({
                            'Date': record_data.get('timestamp'),
                            'File': record_data.get('filename'),
                            'Books': record_data.get('statistics', {}).get('total_books', 0),
                            'Shelves': record_data.get('statistics', {}).get('shelf_count', 0),
                            'Avg Fill': record_data.get('statistics', {}).get('average_fill', 0),
                            'Processing Time': record_data.get('processing_time', 0)
                        })
                    
                    df_history = pd.DataFrame(history_data)
                    df_history.to_excel(writer, sheet_name='Analysis History', index=False)
                
                # Сводная статистика
                if include_multiple and len(include_multiple) > 1:
                    summary_data = {
                        'Total Analyses': len(include_multiple),
                        'Average Books': np.mean([self._prepare_analysis_data(r).get('statistics', {}).get('total_books', 0) 
                                                for r in include_multiple]),
                        'Max Fill': np.max([self._prepare_analysis_data(r).get('statistics', {}).get('average_fill', 0) 
                                          for r in include_multiple]),
                        'Min Fill': np.min([self._prepare_analysis_data(r).get('statistics', {}).get('average_fill', 0) 
                                          for r in include_multiple]),
                        'Total Processing Time': sum([self._prepare_analysis_data(r).get('processing_time', 0) 
                                                    for r in include_multiple])
                    }
                    
                    df_summary = pd.DataFrame([summary_data])
                    df_summary.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            print(f"Excel report created: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error creating Excel report: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_json_report(self, input_data: dict) -> str:
        try:
            # Подготавливаем данные
            analysis_data = self._prepare_analysis_data(input_data)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bookshelf_analysis_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            report_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'bookshelf_analysis',
                    'version': '1.0',
                    'language': 'en',
                    'analyzer_version': '1.0'
                },
                'analysis_data': analysis_data,
                'source_data': input_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"JSON report created: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error creating JSON report: {e}")
            return None
    
    def generate_simple_report(self, input_data: dict, report_type='all'):
        reports = {}
        
        if report_type in ['pdf', 'all']:
            # Используем путь к обработанному изображению из входных данных
            processed_image_path = input_data.get('processed_path') or input_data.get('visualization_path')
            reports['pdf'] = self.generate_pdf_report(
                input_data, 
                processed_image_path=processed_image_path
            )
        
        if report_type in ['excel', 'all']:
            reports['excel'] = self.generate_excel_report(input_data)
        
        if report_type in ['json', 'all']:
            reports['json'] = self.generate_json_report(input_data)
        
        return reports
