// JavaScript для страницы статистики

let dailyTrendsChart = null;
let shelfTypesChart = null;


console.log('Stats.js loaded, checking for required elements...');

const requiredElements = [
    'mainStats',
    'dailyTrendsChart',
    'shelfTypesChart',
    'recentActivity',
    'topAnalyzers',
    'detailedStatsTable',
    'errorDisplay'
];

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking elements...');
    
    requiredElements.forEach(function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.error('Element not found:', elementId);
        } else {
            console.log('Element found:', elementId, element.tagName);
        }
    });
    
    loadAllStats();
    document.getElementById('refreshBtn')?.addEventListener('click', refreshStats);
});

async function loadAllStats() {
    try {
        showLoadingState(true);
        
        const mainResponse = await fetch('/api/stats');
        const mainData = await mainResponse.json();
        
        if (mainData.success) {
            displayMainStats(mainData.statistics);
        } else {
            showError('Ошибка загрузки основной статистики');
        }
        
        const detailedResponse = await fetch('/api/detailed_stats');
        const detailedData = await detailedResponse.json();
        
        if (detailedData.success) {
            if (detailedData.daily_trends) {
                createDailyTrendsChart(detailedData.daily_trends);
            }
            
            if (detailedData.shelf_types) {
                createShelfTypesChart(detailedData.shelf_types);
            }
            
            if (detailedData.recent_activity) {
                displayRecentActivity(detailedData.recent_activity);
            }
            
            if (detailedData.top_analyzers) {
                displayTopAnalyzers(detailedData.top_analyzers);
            }
            
            displayDetailedStats(detailedData);
            
        } else {
            console.warn('Детальная статистика недоступна:', detailedData.error);
            showAlert('Детальная статистика временно недоступна', 'warning');
        }
        
        showLoadingState(false);
        
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        showError('Ошибка загрузки статистики: ' + error.message);
        showLoadingState(false);
    }
}

function displayMainStats(stats) {
    const mainStatsDiv = document.getElementById('mainStats');
    
    if (!mainStatsDiv || !stats) return;
    
    mainStatsDiv.innerHTML = `
        <div class="col-md-3">
            <div class="stat-card bg-primary text-white">
                <div class="text-center">
                    <i class="fas fa-chart-bar fa-2x mb-3"></i>
                    <h3>${stats.total_analyses || 0}</h3>
                    <p class="mb-0">Всего анализов</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stat-card bg-success text-white">
                <div class="text-center">
                    <i class="fas fa-book fa-2x mb-3"></i>
                    <h3>${stats.total_books_detected || 0}</h3>
                    <p class="mb-0">Книг обнаружено</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stat-card bg-warning text-dark">
                <div class="text-center">
                    <i class="fas fa-percentage fa-2x mb-3"></i>
                    <h3>${stats.average_fill_percentage ? stats.average_fill_percentage.toFixed(2) : '0.00'}%</h3>
                    <p class="mb-0">Среднее заполнение</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stat-card bg-info text-white">
                <div class="text-center">
                    <i class="fas fa-clock fa-2x mb-3"></i>
                    <h3>${stats.avg_processing_time ? stats.avg_processing_time.toFixed(2) : '0.00'}</h3>
                    <p class="mb-0">Ср. время (сек)</p>
                </div>
            </div>
        </div>
    `;
}

function displayDetailedStats(data) {
    const tableBody = document.getElementById('detailedStatsTable')?.querySelector('tbody');
    if (!tableBody) return;
    
    let html = '';
    
    if (data.daily_stats && Array.isArray(data.daily_stats)) {
        data.daily_stats.forEach(day => {
            html += `
                <tr>
                    <td>${day.date || 'Неизвестно'}</td>
                    <td><span class="badge bg-primary">${day.analyses || 0}</span></td>
                    <td><span class="badge bg-success">${day.books || 0}</span></td>
                    <td>
                        <div class="progress" style="height: 25px;">
                            <div class="progress-bar bg-info" style="width: ${day.avg_fill || 0}%">
                                ${(day.avg_fill || 0).toFixed(1)}%
                            </div>
                        </div>
                    </td>
                    <td><span class="badge bg-warning">${(day.max_fill || 0).toFixed(1)}%</span></td>
                    <td><span class="badge bg-secondary">${(day.min_fill || 0).toFixed(1)}%</span></td>
                    <td><span class="badge bg-dark">${(day.avg_time || 0).toFixed(2)}с</span></td>
                </tr>
            `;
        });
        
        if (data.total) {
            html += `
                <tr class="table-active">
                    <td><strong>Итого</strong></td>
                    <td><strong><span class="badge bg-primary">${data.total.analyses || 0}</span></strong></td>
                    <td><strong><span class="badge bg-success">${data.total.books || 0}</span></strong></td>
                    <td>
                        <strong>
                            <div class="progress" style="height: 25px;">
                                <div class="progress-bar bg-success" style="width: ${data.total.avg_fill || 0}%">
                                    ${(data.total.avg_fill || 0).toFixed(1)}%
                                </div>
                            </div>
                        </strong>
                    </td>
                    <td><strong><span class="badge bg-warning">${(data.total.max_fill || 0).toFixed(1)}%</span></strong></td>
                    <td><strong><span class="badge bg-secondary">${(data.total.min_fill || 0).toFixed(1)}%</span></strong></td>
                    <td><strong><span class="badge bg-dark">${(data.total.avg_time || 0).toFixed(2)}с</span></strong></td>
                </tr>
            `;
        }
    } else {
        html = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="fas fa-info-circle"></i>
                    <span class="ms-2">Нет данных для отображения</span>
                </td>
            </tr>
        `;
    }
    
    tableBody.innerHTML = html;
}

function createDailyTrendsChart(dailyTrends) {
    const canvas = document.getElementById('dailyTrendsChart');
    if (!canvas) {
        console.error('dailyTrendsChart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    if (dailyTrendsChart) {
        dailyTrendsChart.destroy();
    }
    
    if (!dailyTrends || !Array.isArray(dailyTrends) || dailyTrends.length === 0) {
        const trendsChart = document.getElementById('dailyTrendsChart');
        if (trendsChart && trendsChart.parentNode) {
            trendsChart.parentNode.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-chart-line fa-2x mb-3"></i>
                    <p>Нет данных для графика трендов</p>
                </div>
            `;
        } else {
            console.error('dailyTrendsChart or its parent not found');
        }
        return;
    }
    
    const labels = dailyTrends.map(trend => trend.date || '');
    const analysesData = dailyTrends.map(trend => trend.analyses || 0);
    const booksData = dailyTrends.map(trend => trend.books || 0);
    const fillData = dailyTrends.map(trend => trend.avg_fill || 0);
    
    dailyTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Количество анализов',
                    data: analysesData,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3
                },
                {
                    label: 'Количество книг',
                    data: booksData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.3
                },
                {
                    label: 'Среднее заполнение (%)',
                    data: fillData,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    yAxisID: 'y2',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
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
                        text: 'Анализы'
                    },
                    min: 0
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Книги'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    min: 0
                },
                y2: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Заполнение (%)'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

function createShelfTypesChart(shelfTypes) {
    const canvas = document.getElementById('shelfTypesChart');
    if (!canvas) {
        console.error('shelfTypesChart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    if (shelfTypesChart) {
        shelfTypesChart.destroy();
    }
    
    if (!shelfTypes || !Array.isArray(shelfTypes) || shelfTypes.length === 0) {
        const shelfTypesChartElement = document.getElementById('shelfTypesChart');
        if (shelfTypesChartElement && shelfTypesChartElement.parentNode) {
            shelfTypesChartElement.parentNode.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-chart-pie fa-2x mb-3"></i>
                    <p>Нет данных о типах шкафов</p>
                </div>
            `;
        } else {
            console.error('shelfTypesChart or its parent not found');
        }
        return;
    }
    
    const labels = shelfTypes.map(type => type.name || 'Неизвестно');
    const data = shelfTypes.map(type => type.count || 0);
    const backgroundColors = [
        '#007bff', '#28a745', '#ffc107', '#dc3545', 
        '#6c757d', '#17a2b8', '#6610f2', '#e83e8c'
    ];
    
    shelfTypesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function displayRecentActivity(activity) {
    const timelineDiv = document.getElementById('recentActivity');
    if (!timelineDiv) return;
    
    if (!activity || !Array.isArray(activity) || activity.length === 0) {
        timelineDiv.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-info-circle"></i>
                <span class="ms-2">Нет данных об активности</span>
            </div>
        `;
        return;
    }
    
    timelineDiv.innerHTML = activity.map(item => `
        <div class="card mb-2">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-user-circle fa-2x text-secondary me-3"></i>
                            <div>
                                <strong>${item.user || 'Анонимный пользователь'}</strong>
                                <div class="text-muted small">${item.action || 'Неизвестное действие'}</div>
                                ${item.details ? `<div class="small text-info mt-1">${item.details}</div>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="text-end ms-3">
                        <div class="text-muted small">${formatDateTime(item.timestamp)}</div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayTopAnalyzers(analyzers) {
    const topAnalyzersDiv = document.getElementById('topAnalyzers');
    if (!topAnalyzersDiv) return;
    
    if (!analyzers || !Array.isArray(analyzers) || analyzers.length === 0) {
        topAnalyzersDiv.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-trophy fa-2x mb-2"></i>
                <p>Нет данных о топ анализаторах</p>
            </div>
        `;
        return;
    }
    
    topAnalyzersDiv.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover table-sm">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Пользователь</th>
                        <th class="text-center">Анализов</th>
                        <th class="text-center">Книг найдено</th>
                        <th class="text-center">Среднее время</th>
                    </tr>
                </thead>
                <tbody>
                    ${analyzers.map((analyzer, index) => `
                        <tr>
                            <td class="align-middle">
                                ${index === 0 ? '<i class="fas fa-trophy text-warning fa-lg"></i>' : 
                                  index === 1 ? '<i class="fas fa-trophy text-secondary fa-lg"></i>' :
                                  index === 2 ? '<i class="fas fa-trophy text-danger fa-lg"></i>' : 
                                  `<span class="text-muted">${index + 1}</span>`}
                            </td>
                            <td class="align-middle">
                                <i class="fas fa-user me-2"></i>
                                ${analyzer.user || 'Аноним'}
                            </td>
                            <td class="text-center align-middle">
                                <span class="badge bg-primary rounded-pill px-3 py-2">
                                    ${analyzer.analyses || 0}
                                </span>
                            </td>
                            <td class="text-center align-middle">
                                <span class="badge bg-success rounded-pill px-3 py-2">
                                    ${analyzer.books_found || 0}
                                </span>
                            </td>
                            <td class="text-center align-middle">
                                <span class="badge bg-info rounded-pill px-3 py-2">
                                    ${(analyzer.avg_time || 0).toFixed(2)}с
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function formatDateTime(timestamp) {
    if (!timestamp) return 'Неизвестно';
    
    try {
        const date = new Date(timestamp);
        if (isNaN(date.getTime())) return 'Неизвестно';
        
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) {
            return 'Только что';
        } else if (diffMins < 60) {
            return `${diffMins} мин назад`;
        } else if (diffHours < 24) {
            return `${diffHours} ч назад`;
        } else if (diffDays < 7) {
            return `${diffDays} дн назад`;
        } else {
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
    } catch (e) {
        return 'Неизвестно';
    }
}

function refreshStats() {
    loadAllStats();
    showAlert('Статистика обновлена', 'success');
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 
                              type === 'warning' ? 'exclamation-triangle' : 
                              type === 'danger' ? 'times-circle' : 'info-circle'} me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }
    }, 5000);
}

function showLoadingState(isLoading) {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = isLoading;
        refreshBtn.innerHTML = isLoading ? 
            '<i class="fas fa-spinner fa-spin me-2"></i>Обновление...' : 
            '<i class="fas fa-sync-alt me-2"></i>Обновить статистику';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorDisplay');
    if (errorDiv) {
        errorDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    } else {
        showAlert(message, 'danger');
    }
}