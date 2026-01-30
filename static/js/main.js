// Глобальные переменные
let currentRecordId = null;
let cameraStream = null;
let fillChart = null;

// Загрузка статистики при старте
document.addEventListener('DOMContentLoaded', function() {
    loadGlobalStats();
    setupDragAndDrop();
    checkServerStatus();
    
    setTimeout(checkCanvasElements, 500);
});

// Проверка статуса сервера
async function checkServerStatus() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        if (data.success) {
            console.log('Сервер доступен, модель:', data.model);
        }
    } catch (error) {
        console.error('Сервер недоступен:', error);
        alert('Внимание: Сервер недоступен. Пожалуйста, убедитесь, что сервер запущен.');
    }
}

// Настройка drag-and-drop
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#28a745';
        uploadArea.style.backgroundColor = '#d4edda';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#007bff';
        uploadArea.style.backgroundColor = '#f0f8ff';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#007bff';
        uploadArea.style.backgroundColor = '#f0f8ff';
        
        if (e.dataTransfer.files.length) {
            imageInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });
    
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });
    
    imageInput.addEventListener('change', handleFileSelect);
}

// Обработка выбора файла
function handleFileSelect() {
    const fileInput = document.getElementById('imageInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const img = document.getElementById('originalImage');
            img.src = e.target.result;
            img.style.display = 'block';
            document.getElementById('noOriginal').style.display = 'none';
            analyzeBtn.disabled = false;
        };
        
        reader.readAsDataURL(file);
    }
}

// Запуск камеры
async function startCamera() {
    try {
        const video = document.getElementById('cameraPreview');
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });
        
        cameraStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        
        document.getElementById('startCameraBtn').style.display = 'none';
        document.getElementById('captureBtn').style.display = 'inline-block';
        document.getElementById('stopCameraBtn').style.display = 'inline-block';
        document.getElementById('analyzeBtn').disabled = false;
        
    } catch (error) {
        alert('Ошибка доступа к камере: ' + error.message);
    }
}

// Снимок с камеры
function captureImage() {
    const video = document.getElementById('cameraPreview');
    const canvas = document.getElementById('cameraCanvas');
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    
    const img = document.getElementById('originalImage');
    img.src = canvas.toDataURL('image/jpeg');
    img.style.display = 'block';
    document.getElementById('noOriginal').style.display = 'none';
    
    
    document.getElementById('analyzeBtn').disabled = false;
}

// Остановка камеры
function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    document.getElementById('cameraPreview').style.display = 'none';
    document.getElementById('startCameraBtn').style.display = 'inline-block';
    document.getElementById('captureBtn').style.display = 'none';
    document.getElementById('stopCameraBtn').style.display = 'none';
}

// Анализ изображения
async function analyzeImage() {
    const fileInput = document.getElementById('imageInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    analyzeBtn.disabled = true;
    loadingSpinner.style.display = 'inline-block';
    
    try {
        let formData = new FormData();
        
        
        const settings = JSON.parse(localStorage.getItem('bookshelfSettings') || '{}');
        
        
        if (settings.confidenceThreshold) {
            formData.append('confidence_threshold', settings.confidenceThreshold);
        }
        if (settings.analysisType) {
            formData.append('analysis_type', settings.analysisType);
        }
        
        if (fileInput.files.length > 0) {
            
            formData.append('image', fileInput.files[0]);
            console.log('Отправляю файл:', fileInput.files[0].name);
        } else if (cameraStream) {
            
            const canvas = document.getElementById('cameraCanvas');
            canvas.toBlob(blob => {
                formData.append('image', blob, 'camera_capture.jpg');
            }, 'image/jpeg');
        } else {
            throw new Error('Нет изображения для анализа');
        }
        
        // Таймаут для запроса
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);
        
        console.log('Отправляю запрос на анализ...');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        console.log('Ответ получен, статус:', response.status);
        
        const data = await response.json();
        console.log('Данные ответа:', data);
        
        if (data.success) {
            currentRecordId = data.record_id;
            displayResults(data);
            enableReportButtons();
            loadGlobalStats();
        } else {
            throw new Error(data.error || 'Ошибка анализа изображения');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        
        if (error.name === 'AbortError') {
            alert('Превышено время ожидания (120 секунд). Возможно, модель долго обрабатывает изображение.');
        } else {
            alert('Ошибка: ' + error.message);
        }
        
    } finally {
        analyzeBtn.disabled = false;
        loadingSpinner.style.display = 'none';
    }
}

// Отображение результатов
function displayResults(data) {
    
    const processedImg = document.getElementById('processedImage');
    processedImg.src = data.processed_image;
    processedImg.style.display = 'block';
    document.getElementById('noProcessed').style.display = 'none';
    
    
    const results = data.results;
    document.getElementById('totalBooks').textContent = results.total_books;
    document.getElementById('shelfCount').textContent = results.shelf_count;
    document.getElementById('avgFill').textContent = results.average_fill.toFixed(1) + '%';
    document.getElementById('processingTime').textContent = results.processing_time.toFixed(1) + 'с';
    
    
    document.getElementById('resultsSection').style.display = 'block';
    
    
    createFillChartSafe(results.fill_percentages);
    
    
    const resultSection = document.getElementById('resultsSection');
    resultSection.classList.add('fade-in');
}


function checkCanvasElements() {
    console.log('Проверка canvas элементов...');
    
    const canvas = document.getElementById('shelfFillChart');
    if (canvas) {
        console.log('shelfFillChart найден:', {
            id: canvas.id,
            tagName: canvas.tagName,
            isCanvas: canvas.tagName === 'CANVAS',
            hasGetContext: typeof canvas.getContext,
            isFunction: typeof canvas.getContext === 'function'
        });
        
        if (canvas.tagName !== 'CANVAS') {
            console.warn('Преобразую элемент в canvas...');
            const newCanvas = document.createElement('canvas');
            newCanvas.id = 'shelfFillChart';
            newCanvas.width = 400;
            newCanvas.height = 200;
            newCanvas.style.width = '100%';
            newCanvas.style.height = 'auto';
            canvas.parentNode.replaceChild(newCanvas, canvas);
        }
    } else {
        console.warn('Элемент shelfFillChart не найден на странице');
    }
}


window.safeGetCanvasContext = function(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('Canvas not found:', canvasId);
        return null;
    }
    
    if (canvas.tagName !== 'CANVAS') {
        console.warn('Element is not canvas, converting...');
        const newCanvas = document.createElement('canvas');
        newCanvas.id = canvasId;
        newCanvas.width = 400;
        newCanvas.height = 200;
        canvas.parentNode.replaceChild(newCanvas, canvas);
        return newCanvas.getContext('2d');
    }
    
    if (typeof canvas.getContext !== 'function') {
        console.error('getContext is not a function');
        return null;
    }
    
    return canvas.getContext('2d');
};


function createFillChartSafe(fillPercentages) {
    const ctx = window.safeGetCanvasContext('shelfFillChart');
    
    if (!ctx) {
        console.log('Не удалось получить контекст canvas, показываю текстовый вариант');
        showTextChart(fillPercentages, fillPercentages.map((_, i) => `Полка ${i + 1}`));
        return;
    }
    
    if (fillChart && typeof fillChart.destroy === 'function') {
        fillChart.destroy();
    }
    
    const labels = fillPercentages.map((_, i) => `Полка ${i + 1}`);
    
    if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен');
        showTextChart(fillPercentages, labels);
        return;
    }
    
    fillChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Заполнение (%)',
                data: fillPercentages,
                backgroundColor: fillPercentages.map(p => 
                    p > 80 ? '#dc3545' : p > 50 ? '#ffc107' : '#28a745'
                ),
                borderColor: fillPercentages.map(p => 
                    p > 80 ? '#bd2130' : p > 50 ? '#e0a800' : '#1e7e34'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Заполнение: ${context.raw}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Процент заполнения'
                    }
                }
            }
        }
    });
}


function showTextChart(fillPercentages, labels) {
    const container = document.getElementById('shelfFillChart');
    if (!container) return;
    
    if (container.tagName === 'CANVAS') {
        const ctx = container.getContext('2d');
        if (ctx) {
            ctx.clearRect(0, 0, container.width, container.height);
            ctx.fillStyle = '#f8f9fa';
            ctx.fillRect(0, 0, container.width, container.height);
            ctx.fillStyle = '#000';
            ctx.font = '12px Arial';
            ctx.textAlign = 'left';
            
            fillPercentages.forEach((p, i) => {
                const y = 30 + i * 20;
                ctx.fillText(`${labels[i]}: ${p}%`, 20, y);
                
                ctx.fillStyle = p > 80 ? '#dc3545' : p > 50 ? '#ffc107' : '#28a745';
                ctx.fillRect(150, y - 10, (p * 2), 10);
                ctx.fillStyle = '#000';
            });
        }
    } else {
        container.innerHTML = `
            <div class="alert alert-info">
                <h6>Заполнение по полкам:</h6>
                <ul class="list-group">
                    ${fillPercentages.map((p, i) => `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            ${labels[i]}
                            <span class="badge ${p > 80 ? 'bg-danger' : p > 50 ? 'bg-warning' : 'bg-success'}">
                                ${p}%
                            </span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
}

// Включение кнопок экспорта
function enableReportButtons() {
    document.getElementById('pdfBtn').disabled = false;
    document.getElementById('excelBtn').disabled = false;
    document.getElementById('jsonBtn').disabled = false;
}

// Генерация отчета
async function generateReport(type) {
    if (!currentRecordId) {
        alert('Сначала проанализируйте изображение');
        return;
    }
    
    try {
        const response = await fetch(`/api/generate_report?type=${type}&record_id=${currentRecordId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bookshelf_report_${currentRecordId}.${type}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка генерации отчета');
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
        console.error(error);
    }
}

// Просмотр истории
function viewHistory() {
    window.location.href = '/history';
}


function showStats() {
    window.location.href = '/stats';
}

// Загрузка глобальной статистики
async function loadGlobalStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            const statsContainer = document.getElementById('globalStats');
            
            statsContainer.innerHTML = `
                <div class="text-center">
                    <div class="display-6 text-primary">${stats.total_analyses}</div>
                    <p class="text-muted">Всего анализов</p>
                    
                    <div class="row mt-3">
                        <div class="col-6">
                            <div class="display-6 text-success">${stats.total_books_detected}</div>
                            <small class="text-muted">Книг обнаружено</small>
                        </div>
                        <div class="col-6">
                            <div class="display-6 text-warning">${stats.average_fill_percentage}%</div>
                            <small class="text-muted">Среднее заполнение</small>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

// Очистка всех данных
function clearAll() {
    if (confirm('Вы уверены, что хотите очистить все данные текущей сессии?')) {
        document.getElementById('originalImage').src = '';
        document.getElementById('originalImage').style.display = 'none';
        document.getElementById('noOriginal').style.display = 'block';
        
        document.getElementById('processedImage').src = '';
        document.getElementById('processedImage').style.display = 'none';
        document.getElementById('noProcessed').style.display = 'block';
        
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('imageInput').value = '';
        document.getElementById('analyzeBtn').disabled = true;
        
        if (fillChart) {
            fillChart.destroy();
            fillChart = null;
        }
        
        currentRecordId = null;
        
        document.getElementById('pdfBtn').disabled = true;
        document.getElementById('excelBtn').disabled = true;
        document.getElementById('jsonBtn').disabled = true;
        
        stopCamera();
    }
}