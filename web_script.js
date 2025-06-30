 // 系统配置
let config = {
    apiUrl: 'http://localhost:5000/api/query',
    dbConnection: 'mysql://user:pass@localhost:3306/sales_db',
    model: 'gpt-4',
    autoVisualize: true
};

// 对话状态
let conversationId = null;
let resultChart = null;

// 初始化系统
document.addEventListener('DOMContentLoaded', function() {
    // 检查配置
    const savedConfig = localStorage.getItem('dbAssistantConfig');
    if (savedConfig) {
        config = JSON.parse(savedConfig);
        updateConfigUI();
    }
    
    // 初始化数据库连接状态
    checkDatabaseConnection();
    
    // 初始化图表
    initChart();
});

// 更新配置UI
function updateConfigUI() {
    document.getElementById('apiUrl').value = config.apiUrl;
    document.getElementById('dbConnection').value = config.dbConnection;
    document.getElementById('modelSelect').value = config.model;
    document.getElementById('autoVisualize').checked = config.autoVisualize;
    document.getElementById('modelStatus').textContent = `Text2SQL 模型: ${config.model.toUpperCase()}`;
}

// 检查数据库连接状态
async function checkDatabaseConnection() {
    const dbStatusDot = document.getElementById('dbStatusDot');
    const dbStatusText = document.getElementById('dbStatusText');
    
    try {
        // 模拟数据库连接检查
        dbStatusDot.className = 'status-dot';
        dbStatusText.textContent = '正在连接数据库...';
        
        // 实际应用中这里应该调用API检查数据库连接
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        dbStatusDot.className = 'status-dot connected';
        dbStatusText.textContent = '已连接: MySQL 销售数据库';
    } catch (error) {
        dbStatusDot.className = 'status-dot disconnected';
        dbStatusText.textContent = '数据库连接失败';
    }
}

// 初始化图表
function initChart() {
    const ctx = document.getElementById('resultChart').getContext('2d');
    resultChart = new Chart(ctx, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#fff' }
                },
                title: {
                    display: true,
                    text: '查询结果',
                    color: '#fff',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#fff' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#fff' }
                }
            }
        }
    });
}

// 发送消息到后端
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (message === '') return;
    addMessage(message, 'user');
    userInput.value = '';
    showTypingIndicator();
    try {
        // 只需发送自然语言到后端，后端负责所有处理
        const response = await axios.post(config.apiUrl, {
            question: message,
            conversation_id: conversationId
        });
        removeTypingIndicator();
        handleResponse(response.data);
        if (response.data.conversation_id) {
            conversationId = response.data.conversation_id;
        }
    } catch (error) {
        removeTypingIndicator();
        handleError(error);
    }
}

// 处理后端响应
function handleResponse(data) {
    if (data.error) {
        addMessage(`处理请求时出错: ${data.error}`, 'system');
        return;
    }
    // 显示SQL查询
    if (data.sql) addSqlMessage(data.sql);
    // 显示系统消息和分析/摘要
    addMessage(data.message || '已成功查询到以下结果:', 'system');
    // 可视化结果（后端已处理好，前端只负责渲染）
    if (data.result && data.result.length > 0 && config.autoVisualize) {
        visualizeResult(data.result, data.visualization);
    }
}

// 处理错误
function handleError(error) {
    let errorMsg = '请求处理失败';
    
    if (error.response) {
        // 服务器响应了错误状态码
        errorMsg = `服务器错误: ${error.response.status} - ${error.response.data.error || '未知错误'}`;
    } else if (error.request) {
        // 请求已发出但没有收到响应
        errorMsg = '无法连接到服务器，请检查API地址';
    } else {
        // 请求配置出错
        errorMsg = `请求配置错误: ${error.message}`;
    }
    
    addMessage(errorMsg, 'system');
}

// 添加消息到聊天框
function addMessage(content, sender) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    
    if (sender === 'user') {
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-user me-2 text-primary"></i>
                <strong>用户</strong>
            </div>
            <p>${content}</p>
        `;
    } else {
        messageDiv.className = 'message system-message';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-robot me-2 text-success"></i>
                <strong>数据库助手</strong>
            </div>
            <p>${content}</p>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加SQL消息
function addSqlMessage(sql) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message sql-message';
    messageDiv.innerHTML = `
        <div class="d-flex align-items-center mb-2">
            <i class="fas fa-code me-2 text-success"></i>
            <strong>SQL查询</strong>
            <span class="badge badge-sql ms-2">${config.dbConnection.split(':')[0]}</span>
        </div>
        <pre>${sql}</pre>
    `;
    
    // 添加复制按钮
    const copyBtn = document.createElement('button');
    copyBtn.className = 'sql-copy-btn';
    copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>复制';
    copyBtn.onclick = () => copyToClipboard(sql);
    messageDiv.appendChild(copyBtn);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const copyBtn = event.target.closest('.sql-copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>已复制';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        }
    });
}

// 显示系统正在输入
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message system-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-robot me-2 text-success"></i>
            <strong>数据库助手</strong>
        </div>
        <div class="typing-indicator mt-2">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 移除系统正在输入指示器
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// 可视化结果
function visualizeResult(data, chartType) {
    if (!data || data.length === 0) {
        addMessage('查询结果为空', 'system');
        return;
    }
    
    // 显示可视化容器
    const container = document.getElementById('visualizationContainer');
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth' });
    
    // 更新表格
    updateTable(data);
    
    // 更新图表
    updateChart(data, chartType);
}

// 更新表格
function updateTable(data) {
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    
    // 清空表格
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';
    
    // 添加表头
    const keys = Object.keys(data[0]);
    keys.forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        tableHeader.appendChild(th);
    });
    
    // 添加数据行
    data.forEach(row => {
        const tr = document.createElement('tr');
        keys.forEach(key => {
            const td = document.createElement('td');
            td.textContent = row[key];
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
}

// 更新图表
function updateChart(data, chartType = 'bar') {
    // 如果没有数据，保持图表为空
    if (data.length === 0) return;
    
    const keys = Object.keys(data[0]);
    const labels = [];
    const values = [];
    
    // 尝试确定标签和数据列
    let labelKey = keys[0];
    let valueKey = keys[1];
    
    // 寻找数值列
    for (let i = 1; i < keys.length; i++) {
        if (typeof data[0][keys[i]] === 'number') {
            valueKey = keys[i];
            break;
        }
    }
    
    // 提取标签和数据
    data.forEach(item => {
        labels.push(item[labelKey]);
        values.push(item[valueKey]);
    });
    
    // 确定图表类型
    const chartTypes = ['bar', 'line', 'pie'];
    if (!chartTypes.includes(chartType)) {
        chartType = values.length > 10 ? 'line' : 'bar';
    }
    
    // 更新图表数据
    resultChart.data.labels = labels;
    resultChart.data.datasets = [{
        label: valueKey,
        data: values,
        backgroundColor: getColors(values.length, chartType),
        borderColor: 'rgba(255, 255, 255, 0.8)',
        borderWidth: 1
    }];
    
    // 更新图表类型
    resultChart.config.type = chartType;
    resultChart.update();
}

// 生成颜色数组
function getColors(count, type) {
    const colors = [];
    const baseColors = [
        'rgba(67, 97, 238, 0.7)',
        'rgba(76, 201, 240, 0.7)',
        'rgba(247, 37, 133, 0.7)',
        'rgba(106, 76, 219, 0.7)',
        'rgba(72, 199, 142, 0.7)',
        'rgba(255, 193, 7, 0.7)',
        'rgba(253, 126, 20, 0.7)',
        'rgba(32, 201, 151, 0.7)'
    ];
    
    if (type === 'pie') {
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
    } else {
        return baseColors[0];
    }
    
    return colors;
}

// 保存配置
function saveConfig() {
    config.apiUrl = document.getElementById('apiUrl').value;
    config.dbConnection = document.getElementById('dbConnection').value;
    config.model = document.getElementById('modelSelect').value;
    config.autoVisualize = document.getElementById('autoVisualize').checked;
    
    localStorage.setItem('dbAssistantConfig', JSON.stringify(config));
    updateConfigUI();
    
    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
    modal.hide();
}

// 事件监听
document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 示例问题点击事件
document.querySelectorAll('.example-card').forEach(card => {
    card.addEventListener('click', () => {
        const question = card.getAttribute('data-question');
        document.getElementById('userInput').value = question;
        sendMessage();
    });
});

// 图表/表格切换
document.querySelectorAll('[data-type]').forEach(btn => {
    btn.addEventListener('click', () => {
        // 切换激活状态
        document.querySelectorAll('[data-type]').forEach(b => {
            b.classList.remove('active');
        });
        btn.classList.add('active');
        
        // 显示对应内容
        const type = btn.getAttribute('data-type');
        if (type === 'chart') {
            document.querySelector('.chart-container').classList.remove('d-none');
            document.querySelector('.table-container').classList.add('d-none');
        } else {
            document.querySelector('.chart-container').classList.add('d-none');
            document.querySelector('.table-container').classList.remove('d-none');
        }
    });
});

// 保存配置按钮
document.getElementById('saveConfig').addEventListener('click', saveConfig);

// 连接数据库按钮
document.getElementById('connectBtn').addEventListener('click', checkDatabaseConnection);
