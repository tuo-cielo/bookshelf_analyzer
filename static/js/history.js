// JavaScript для страницы истории

let currentPage = 1;
let totalPages = 1;
let fillTimeChart = null;
let distributionChart = null;

// Загрузка истории при ПОЛНОЙ загрузке страницы
window.addEventListener('load', function() {
    console.log('History page fully loaded');
    // Проверяем что Chart.js загружен
    if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен!');
        return;
    }
    loadHistory();
    setupEventListeners();
    
    // Проверяем canvas элементы
    checkCanvasElements();
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Поиск
    document.getElementById('searchInput').addEventListener('input', function() {
        loadHistory(1);
    });
    
    // Фильтр по дате
    document.getElementById('dateFilter').addEventListener('change', function() {
        loadHistory(1);
    });
    
    // Сортировка
    document.getElementById('sortSelect').addEventListener('change', function() {
        loadHistory(1);
    });
}

// Проверка canvas элементов
function checkCanvasElements() {
    console.log('Checking canvas elements...');
    
    const fillCanvas = document.getElementById('fillChart');
    const distCanvas = document.getElementById('distributionChart');
    
    if (fillCanvas) {
        console.log('fillChart found:', {
            tagName: fillCanvas.tagName,
            isCanvas: fillCanvas.tagName === 'CANVAS',
            hasGetContext: typeof fillCanvas.getContext
        });
    }
    
    if (distCanvas) {
        console.log('distributionChart found:', {
            tagName: distCanvas.tagName,
            isCanvas: distCanvas.tagName === 'CANVAS',
            hasGetContext: typeof distCanvas.getContext
        });
    }
}

// Загрузка истории
async function loadHistory(page = 1) {
    try {
        const search = document.getElementById('searchInput').value;
        const date = document.getElementById('dateFilter').value;
        const sort = document.getElementById('sortSelect').value;
        
        // Показываем спиннер
        const tableBody = document.getElementById('historyTable');
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">
                    <div class="spinner-border text-primary"></div>
                    <p class="mt-2">Загрузка истории...</p>
                </td>
            </tr>
        `;
        
        // Формируем URL с параметрами
        let url = `/api/history?page=${page}&per_page=10`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (date) url += `&date=${date}`;
        if (sort) url += `&sort=${sort}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.records);
            updatePagination(data.total, data.pages, data.current_page);
            updateCharts(data.records);
        } else {
            throw new Error(data.error || 'Ошибка загрузки истории');
        }
        
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
        document.getElementById('historyTable').innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p class="mt-2">${error.message}</p>
                </td>
            </tr>
        `;
    }
}

// Отображение истории в таблице
function displayHistory(records) {
    const tableBody = document.getElementById('historyTable');
    
    if (records.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">
                    <i class="fas fa-inbox"></i>
                    <p class="mt-2">История пуста</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = records.map(record => `
        <tr onclick="showDetails(${record.id})" style="cursor: pointer;">
            <td>${record.id}</td>
            <td>${formatDateTime(record.timestamp)}</td>
            <td>
                <i class="fas fa-file-image"></i>
                ${record.filename}
            </td>
            <td>
                <span class="badge bg-primary rounded-pill">${record.total_books}</span>
            </td>
            <td>
                <span class="badge bg-info rounded-pill">${record.shelf_count}</span>
            </td>
            <td>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${record.average_fill}%;"
                         aria-valuenow="${record.average_fill}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${record.average_fill.toFixed(1)}%
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-secondary">${record.processing_time.toFixed(2)} сек</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); exportRecord(${record.id})">
                    <i class="fas fa-download"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); deleteRecord(${record.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Форматирование даты и времени
function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU');
}

// Обновление пагинации
function updatePagination(total, pages, current) {
    const pagination = document.getElementById('pagination');
    currentPage = current;
    totalPages = pages;
    
    let html = '';
    
    // Предыдущая страница
    html += `
        <li class="page-item ${current === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${current - 1})">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Номера страниц
    for (let i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || (i >= current - 2 && i <= current + 2)) {
            html += `
                <li class="page-item ${i === current ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
                </li>
            `;
        } else if (i === current - 3 || i === current + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Следующая страница
    html += `
        <li class="page-item ${current === pages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${current + 1})">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// Смена страницы
function changePage(page) {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
        loadHistory(page);
    }
}

// Обновление графиков
function updateCharts(records) {
    updateFillTimeChart(records);
    updateDistributionChart(records);
}

// График заполнения по времени
function updateFillTimeChart(records) {
    try {
        const canvas = document.getElementById('fillChart');
        if (!canvas) {
            console.log('Canvas fillChart не найден, пропускаем график');
            return;
        }
        
        // Проверяем что это canvas
        if (canvas.tagName !== 'CANVAS') {
            console.error('Элемент fillChart не является canvas. Это:', canvas.tagName);
            return;
        }
        
        // Проверяем наличие getContext
        if (typeof canvas.getContext !== 'function') {
            console.error('canvas.getContext не является функцией');
            return;
        }
        
        // Уничтожаем старый график
        if (fillTimeChart && typeof fillTimeChart.destroy === 'function') {
            fillTimeChart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        const labels = records.map(r => {
            const date = new Date(r.timestamp);
            return date.toLocaleDateString('ru-RU');
        }).reverse();
        
        const fillData = records.map(r => r.average_fill || 0).reverse();
        const bookData = records.map(r => r.total_books || 0).reverse();
        
        fillTimeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Среднее заполнение (%)',
                        data: fillData,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Количество книг',
                        data: bookData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Дата'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Заполнение (%)'
                        },
                        min: 0,
                        max: 100
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Количество книг'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
        
        console.log('График fillChart создан успешно');
        
    } catch (error) {
        console.error('Ошибка создания графика fillChart:', error);
        // Очищаем canvas при ошибке
        const canvas = document.getElementById('fillChart');
        if (canvas && canvas.getContext) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
}

// График распределения по заполнению
function updateDistributionChart(records) {
    try {
        const canvas = document.getElementById('distributionChart');
        if (!canvas) {
            console.log('Canvas distributionChart не найден, пропускаем график');
            return;
        }
        
        if (canvas.tagName !== 'CANVAS') {
            console.error('Элемент distributionChart не является canvas');
            return;
        }
        
        if (typeof canvas.getContext !== 'function') {
            console.error('canvas.getContext не является функцией');
            return;
        }
        
        if (distributionChart && typeof distributionChart.destroy === 'function') {
            distributionChart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Категории заполнения
        const categories = {
            'Низкое (<30%)': 0,
            'Среднее (30-70%)': 0,
            'Высокое (>70%)': 0
        };
        
        records.forEach(record => {
            const fill = record.average_fill || 0;
            if (fill < 30) {
                categories['Низкое (<30%)']++;
            } else if (fill <= 70) {
                categories['Среднее (30-70%)']++;
            } else {
                categories['Высокое (>70%)']++;
            }
        });
        
        distributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(categories),
                datasets: [{
                    data: Object.values(categories),
                    backgroundColor: [
                        '#28a745', // Зеленый для низкого
                        '#ffc107', // Желтый для среднего
                        '#dc3545'  // Красный для высокого
                    ],
                    borderColor: [
                        '#1e7e34',
                        '#e0a800',
                        '#bd2130'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('График distributionChart создан успешно');
        
    } catch (error) {
        console.error('Ошибка создания графика distributionChart:', error);
        // Очищаем canvas при ошибке
        const canvas = document.getElementById('distributionChart');
        if (canvas && canvas.getContext) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
}

// Показать детали записи
async function showDetails(recordId) {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.success) {
            const record = data.records.find(r => r.id === recordId);
            if (record) {
                displayRecordDetails(record);
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки деталей:', error);
    }
}

// Отображение деталей записи
function displayRecordDetails(record) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'detailsModal';
    modal.tabIndex = '-1';
    
    const fillPercentages = record.fill_percentages || [];
    
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Детали анализа</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Оригинальное изображение:</h6>
                            <img src="${record.original_image_url}" class="img-fluid rounded" alt="Оригинал">
                        </div>
                        <div class="col-md-6">
                            <h6>Результат анализа:</h6>
                            <img src="${record.processed_image_url}" class="img-fluid rounded" alt="Результат">
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <h6>Подробная статистика:</h6>
                        <table class="table table-bordered">
                            <tr>
                                <th>Параметр</th>
                                <th>Значение</th>
                            </tr>
                            <tr>
                                <td>Дата анализа</td>
                                <td>${formatDateTime(record.timestamp)}</td>
                            </tr>
                            <tr>
                                <td>Имя файла</td>
                                <td>${record.filename}</td>
                            </tr>
                            <tr>
                                <td>Размер изображения</td>
                                <td>${record.image_width} × ${record.image_height}</td>
                            </tr>
                            <tr>
                                <td>Всего книг</td>
                                <td><span class="badge bg-primary">${record.total_books}</span></td>
                            </tr>
                            <tr>
                                <td>Количество полок</td>
                                <td><span class="badge bg-info">${record.shelf_count}</span></td>
                            </tr>
                            <tr>
                                <td>Среднее заполнение</td>
                                <td><span class="badge bg-success">${record.average_fill.toFixed(1)}%</span></td>
                            </tr>
                            <tr>
                                <td>Время обработки</td>
                                <td><span class="badge bg-secondary">${record.processing_time.toFixed(2)} сек</span></td>
                            </tr>
                            ${fillPercentages.length > 0 ? `
                            <tr>
                                <td>Заполнение по полкам</td>
                                <td>
                                    <div class="mt-2">
                                        ${fillPercentages.map((p, i) => `
                                            <div class="mb-1">
                                                <small>Полка ${i + 1}:</small>
                                                <div class="progress" style="height: 15px;">
                                                    <div class="progress-bar" style="width: ${p}%">
                                                        ${p.toFixed(1)}%
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </td>
                            </tr>
                            ` : ''}
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="exportRecord(${record.id})">
                        <i class="fas fa-download"></i> Экспорт отчета
                    </button>
                    <button type="button" class="btn btn-danger" onclick="deleteRecord(${record.id})">
                        <i class="fas fa-trash"></i> Удалить запись
                    </button>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    modal.addEventListener('hidden.bs.modal', function () {
        document.body.removeChild(modal);
    });
}

// Экспорт записи
function exportRecord(recordId) {
    if (recordId) {
        const type = prompt('Введите тип отчета (pdf, excel, json):', 'pdf');
        if (type && ['pdf', 'excel', 'json'].includes(type.toLowerCase())) {
            window.open(`/api/generate_report?type=${type}&record_id=${recordId}`, '_blank');
        }
    }
}

// Удаление записи
async function deleteRecord(recordId) {
    if (recordId && confirm('Вы уверены, что хотите удалить эту запись?')) {
        try {
            const response = await fetch(`/api/delete_record/${recordId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Запись успешно удалена');
                loadHistory(currentPage);
                const modal = bootstrap.Modal.getInstance(document.getElementById('detailsModal'));
                if (modal) modal.hide();
            } else {
                throw new Error(data.error || 'Ошибка удаления');
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
            console.error(error);
        }
    }
}

// Обновление истории
function refreshHistory() {
    loadHistory(currentPage);
}

// Очистка фильтров
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFilter').value = '';
    document.getElementById('sortSelect').value = 'newest';
    loadHistory(1);
}

// Глобальные функции для кнопок
window.refreshHistory = refreshHistory;
window.clearFilters = clearFilters;
window.changePage = changePage;
window.showDetails = showDetails;
window.exportRecord = exportRecord;
window.deleteRecord = deleteRecord;