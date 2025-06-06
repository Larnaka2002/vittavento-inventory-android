// API endpoints
const API = {
    items: '/api/items',
    operations: '/api/operations',
    statistics: '/api/statistics'
};

// Global variables
let currentScanMode = null;
let html5QrCode = null;

// Navigation
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');

    // Set up navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.getAttribute('data-section') ||
                           e.target.parentElement.getAttribute('data-section');
            if (section) {
                showSection(section);

                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                (e.target.classList.contains('nav-link') ? e.target : e.target.parentElement).classList.add('active');
            }
        });
    });

    // Load initial data and show dashboard
    showSection('dashboard');
    updateDashboard();

    // Set up search
    const searchInput = document.getElementById('warehouseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', updateWarehouseTable);
    }

    // Set up barcode inputs
    const incomingBarcode = document.getElementById('incomingBarcode');
    const outgoingBarcode = document.getElementById('outgoingBarcode');

    if (incomingBarcode) {
        // Обработка изменения поля (для ручного ввода)
        incomingBarcode.addEventListener('change', (e) => {
            findItemByBarcode(e.target.value, 'incoming');
        });

        // Обработка Enter для ручного сканера
        incomingBarcode.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                findItemByBarcode(e.target.value, 'incoming');
                // Переход к полю количества
                const quantityField = document.getElementById('incomingQuantity');
                if (quantityField && document.getElementById('incomingItemInfo').style.display !== 'none') {
                    quantityField.focus();
                    quantityField.select();
                }
            }
        });

        // Автофокус при переходе на страницу
        incomingBarcode.addEventListener('focus', () => {
            incomingBarcode.select();
        });
    }

    if (outgoingBarcode) {
        // Обработка изменения поля (для ручного ввода)
        outgoingBarcode.addEventListener('change', (e) => {
            findItemByBarcode(e.target.value, 'outgoing');
        });

        // Обработка Enter для ручного сканера
        outgoingBarcode.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                findItemByBarcode(e.target.value, 'outgoing');
                // Переход к полю количества
                const quantityField = document.getElementById('outgoingQuantity');
                if (quantityField && document.getElementById('outgoingItemInfo').style.display !== 'none') {
                    quantityField.focus();
                    quantityField.select();
                }
            }
        });

        // Автофокус при переходе на страницу
        outgoingBarcode.addEventListener('focus', () => {
            outgoingBarcode.select();
        });
    }

    // Обработка Enter в полях количества
    const incomingQuantity = document.getElementById('incomingQuantity');
    const outgoingQuantity = document.getElementById('outgoingQuantity');

    if (incomingQuantity) {
        incomingQuantity.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                processIncoming();
            }
        });
    }

    if (outgoingQuantity) {
        outgoingQuantity.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                processOutgoing();
            }
        });
    }
});

function showSection(sectionId) {
    console.log('Showing section:', sectionId);

    // Скрываем все секции
    document.querySelectorAll('.section').forEach(s => {
        s.classList.remove('active');
        s.style.display = 'none';
    });

    // Показываем нужную секцию
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add('active');
        section.style.display = 'block';

        // Update data when switching sections
        if (sectionId === 'dashboard') updateDashboard();
        if (sectionId === 'warehouse') updateWarehouseTable();

        // Автофокус на поле штрихкода для удобства работы со сканером
        if (sectionId === 'incoming') {
            setTimeout(() => {
                const barcodeField = document.getElementById('incomingBarcode');
                if (barcodeField) {
                    barcodeField.focus();
                    barcodeField.select();
                }
            }, 100);
        }

        if (sectionId === 'outgoing') {
            setTimeout(() => {
                const barcodeField = document.getElementById('outgoingBarcode');
                if (barcodeField) {
                    barcodeField.focus();
                    barcodeField.select();
                }
            }, 100);
        }
    } else {
        console.error('Section not found:', sectionId);
    }
}

// Dashboard functions
async function updateDashboard() {
    try {
        const stats = await fetchJSON(API.statistics);

        document.getElementById('totalItems').textContent = stats.total_items;
        document.getElementById('totalIncoming').textContent = stats.incoming_today;
        document.getElementById('totalOutgoing').textContent = stats.outgoing_today;
        document.getElementById('lowStock').textContent = stats.low_stock;

        await updateRecentOperations();
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

async function updateRecentOperations() {
    try {
        const operations = await fetchJSON(API.operations);
        const tbody = document.getElementById('recentOperations');

        if (operations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет операций</td></tr>';
            return;
        }

        tbody.innerHTML = operations.map(op => {
            const badge = op.type === 'incoming' ?
                '<span class="badge bg-success">Приход</span>' :
                '<span class="badge bg-danger">Списание</span>';

            const date = new Date(op.created_at).toLocaleString('ru-RU');

            return `
                <tr>
                    <td>${date}</td>
                    <td>${badge}</td>
                    <td>${op.item_article}</td>
                    <td>${op.item_name}</td>
                    <td>${op.type === 'incoming' ? '+' : '-'}${op.quantity}</td>
                    <td>${op.user}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error updating operations:', error);
    }
}

// Warehouse functions
async function updateWarehouseTable() {
    try {
        const items = await fetchJSON(API.items);
        const tbody = document.getElementById('warehouseTable');
        const searchValue = document.getElementById('warehouseSearch').value.toLowerCase();

        let filteredItems = items;
        if (searchValue) {
            filteredItems = items.filter(item =>
                item.article.toLowerCase().includes(searchValue) ||
                item.name.toLowerCase().includes(searchValue) ||
                item.barcode.includes(searchValue)
            );
        }

        if (filteredItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет позиций</td></tr>';
            return;
        }

        tbody.innerHTML = filteredItems.map(item => {
            const stockClass = item.quantity < 20 ? 'text-danger' :
                             item.quantity < 50 ? 'text-warning' : 'text-success';

            return `
                <tr>
                    <td>${item.article}</td>
                    <td>${item.name}</td>
                    <td><span class="badge bg-secondary">${item.type}</span></td>
                    <td class="${stockClass}"><strong>${item.quantity}</strong></td>
                    <td><code>${item.barcode}</code></td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="editItem(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteItem(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error updating warehouse:', error);
    }
}

// Add item
async function addItem() {
    const article = document.getElementById('itemArticle').value;
    const name = document.getElementById('itemName').value;
    const type = document.getElementById('itemType').value;
    const quantity = parseInt(document.getElementById('itemQuantity').value);
    const barcode = document.getElementById('itemBarcode').value;

    if (!article || !name || !type || !barcode) {
        showAlert('Заполните все поля!', 'danger');
        return;
    }

    try {
        const response = await fetch(API.items, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({article, name, type, quantity, barcode})
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка добавления');
        }

        // Close modal and reset form
        const modal = bootstrap.Modal.getInstance(document.getElementById('addItemModal'));
        modal.hide();
        document.getElementById('addItemForm').reset();

        showAlert('Позиция успешно добавлена!', 'success');
        updateWarehouseTable();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

// Delete item
async function deleteItem(id) {
    const confirmMessage = 'Вы уверены, что хотите удалить эту позицию?\n\n' +
                          'ВНИМАНИЕ: Также будет удалена вся история операций с этим товаром!';

    if (!confirm(confirmMessage)) return;

    try {
        const response = await fetch(`${API.items}/${id}`, {method: 'DELETE'});

        if (!response.ok) {
            throw new Error('Ошибка удаления');
        }

        showAlert('Позиция удалена', 'success');
        updateWarehouseTable();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

// Scanner functions
function startScanner(mode) {
    currentScanMode = mode;
    const containerId = mode === 'incoming' ? 'scannerContainer' : 'scannerContainerOut';
    document.getElementById(containerId).style.display = 'block';

    html5QrCode = new Html5Qrcode("scanner-video" + (mode === 'outgoing' ? '-out' : ''));

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 100 },
        aspectRatio: 1.7777778
    };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
            document.getElementById(mode + 'Barcode').value = decodedText;
            stopScanner();
            findItemByBarcode(decodedText, mode);
        },
        (errorMessage) => {
            // Ignore errors silently
        }
    ).catch((err) => {
        console.error(`Unable to start scanning: ${err}`);
        showAlert('Не удалось запустить камеру. Попробуйте ввести штрихкод вручную.', 'danger');
        stopScanner();
    });
}

function stopScanner() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            document.getElementById('scannerContainer').style.display = 'none';
            document.getElementById('scannerContainerOut').style.display = 'none';
        }).catch((err) => {
            console.error(`Unable to stop scanning: ${err}`);
        });
        html5QrCode = null;
    }
}

// Find item by barcode
async function findItemByBarcode(barcode, mode) {
    if (!barcode) return;

    // Очищаем пробелы
    barcode = barcode.trim();

    try {
        const response = await fetch(`${API.items}/barcode/${barcode}`);
        const item = await response.json();

        if (!response.ok) {
            // Звуковой сигнал ошибки
            playSound('error');
            showAlert('❌ Товар с таким штрихкодом не найден!', 'warning');
            document.getElementById(mode + 'ItemInfo').style.display = 'none';
            // Очищаем поле для нового сканирования
            document.getElementById(mode + 'Barcode').value = '';
            document.getElementById(mode + 'Barcode').focus();
            return;
        }

        // Звуковой сигнал успеха
        playSound('success');

        // Show item info
        document.getElementById(mode + 'Article').textContent = item.article;
        document.getElementById(mode + 'Name').textContent = item.name;
        document.getElementById(mode + 'Stock').textContent = item.quantity;
        document.getElementById(mode + 'ItemInfo').style.display = 'block';

        // Store current item ID for processing
        document.getElementById(mode + 'Barcode').dataset.itemId = item.id;

        // Подсветка найденного товара
        const itemInfo = document.getElementById(mode + 'ItemInfo');
        itemInfo.classList.add('pulse-animation');
        setTimeout(() => itemInfo.classList.remove('pulse-animation'), 1000);

    } catch (error) {
        playSound('error');
        showAlert('Ошибка поиска товара', 'danger');
    }
}

// Функция для воспроизведения звуков
function playSound(type) {
    // Создаем звуковые сигналы используя Web Audio API
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    if (type === 'success') {
        oscillator.frequency.value = 800; // Высокий тон для успеха
        gainNode.gain.value = 0.3;
    } else if (type === 'error') {
        oscillator.frequency.value = 300; // Низкий тон для ошибки
        gainNode.gain.value = 0.3;
    }

    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.1); // Короткий сигнал
}

// Process incoming
async function processIncoming() {
    const itemId = parseInt(document.getElementById('incomingBarcode').dataset.itemId);
    const quantity = parseInt(document.getElementById('incomingQuantity').value);

    if (!itemId || !quantity || quantity <= 0) {
        showAlert('Введите корректное количество!', 'danger');
        return;
    }

    try {
        const response = await fetch(API.operations, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: 'incoming',
                item_id: itemId,
                quantity: quantity
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка операции');
        }

        // Reset form
        document.getElementById('incomingBarcode').value = '';
        document.getElementById('incomingBarcode').dataset.itemId = '';
        document.getElementById('incomingQuantity').value = '';
        document.getElementById('incomingItemInfo').style.display = 'none';

        showAlert(`✅ Приход оформлен! +${quantity} шт. Новый остаток: ${data.new_quantity} шт.`, 'success');
        updateDashboard();

        // Возвращаем фокус на поле штрихкода для следующего сканирования
        document.getElementById('incomingBarcode').focus();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

// Process outgoing
async function processOutgoing() {
    const itemId = parseInt(document.getElementById('outgoingBarcode').dataset.itemId);
    const quantity = parseInt(document.getElementById('outgoingQuantity').value);

    if (!itemId || !quantity || quantity <= 0) {
        showAlert('Введите корректное количество!', 'danger');
        return;
    }

    try {
        const response = await fetch(API.operations, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: 'outgoing',
                item_id: itemId,
                quantity: quantity
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка операции');
        }

        // Reset form
        document.getElementById('outgoingBarcode').value = '';
        document.getElementById('outgoingBarcode').dataset.itemId = '';
        document.getElementById('outgoingQuantity').value = '';
        document.getElementById('outgoingItemInfo').style.display = 'none';

        showAlert(`✅ Списание оформлено! -${quantity} шт. Остаток: ${data.new_quantity} шт.`, 'success');
        updateDashboard();

        // Возвращаем фокус на поле штрихкода для следующего сканирования
        document.getElementById('outgoingBarcode').focus();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

// Helper functions
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Отключаем браузерную валидацию для модальной формы
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addItemForm');
    if (form) {
        form.setAttribute('novalidate', 'true');
    }
});