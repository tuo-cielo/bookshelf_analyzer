// Глобальная функция для безопасного получения canvas контекста
window.getCanvasContext = function(canvasId) {
    console.log('Getting canvas context for:', canvasId);
    
    // 1. Находим элемент
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('ERROR: Element with id "' + canvasId + '" not found');
        return null;
    }
    
    // 2. Проверяем что это canvas
    console.log('Canvas element:', canvas);
    console.log('Tag name:', canvas.tagName);
    
    if (canvas.tagName !== 'CANVAS') {
        console.error('ERROR: Element with id "' + canvasId + '" is not a CANVAS element. It is:', canvas.tagName);
        return null;
    }
    
    // 3. Проверяем поддержку getContext
    if (typeof canvas.getContext !== 'function') {
        console.error('ERROR: getContext is not a function on this element');
        return null;
    }
    
    // 4. Получаем контекст
    try {
        const ctx = canvas.getContext('2d');
        console.log('Successfully got context for:', canvasId);
        return ctx;
    } catch (error) {
        console.error('ERROR getting context:', error);
        return null;
    }
};

// Инициализация при полной загрузке страницы
window.addEventListener('load', function() {
    console.log('Page fully loaded, checking for charts...');
    
   
    setTimeout(function() {
        
        const canvases = document.querySelectorAll('canvas');
        console.log('Found', canvases.length, 'canvas elements on page');
        
        
        canvases.forEach(function(canvas, index) {
            console.log('Canvas ' + (index + 1) + ':', {
                id: canvas.id,
                tagName: canvas.tagName,
                hasGetContext: typeof canvas.getContext === 'function',
                width: canvas.width,
                height: canvas.height
            });
        });
        
        // Инициализируем графики в зависимости от страницы
        if (document.getElementById('fillChart') && window.initHistoryCharts) {
            console.log('Initializing history charts');
            window.initHistoryCharts();
        }
        
        if (document.getElementById('dailyTrendsChart') && window.initStatsCharts) {
            console.log('Initializing stats charts');
            window.initStatsCharts();
        }
        
        if (document.getElementById('shelfFillChart') && window.initMainCharts) {
            console.log('Initializing main page charts');
            window.initMainCharts();
        }
        
    }, 100); 
});