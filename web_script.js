// 系统配置
let config = {
    apiUrl: 'http://localhost:5000/api/query',
    connectUrl: 'http://localhost:5000/api/connect_db'
};
let conversationId = null;
// 连接数据库按钮逻辑
async function connectDatabase() {
    try {
        const response = await axios.post(config.connectUrl);
        if (response.data.success) {
            addMessage('数据库连接成功: ' + response.data.message, 'system');
            // 你可以在这里设置连接状态为已连接
        } else {
            addMessage('数据库连接失败: ' + (response.data.error || '未知错误'), 'system');
            // 你可以在这里设置连接状态为未连接
        }
    } catch (error) {
        addMessage('数据库连接请求失败', 'system');
    }
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
        addMessage('请求处理失败', 'system');
    }
}

function handleResponse(data) {
    if (data.error) {
        addMessage(`处理请求时出错: ${data.error}`, 'system');
        return;
    }
    if (data.sql) addSqlMessage(data.sql);
    if (data.message) addMessage(data.message, 'system');
    // 新增：处理 chart_urls
    if (data.chart_urls) {
        // 显示可视化区域
        document.getElementById('visualizationContainer').style.display = 'block';
        showChartImages(data.chart_urls);
    }
}

function showChartImage(url) {
    const container = document.getElementById('visualizationContainer');
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth' });
    const chartDiv = document.querySelector('.chart-container');
    chartDiv.innerHTML = `<img src="${url}" alt="图表" style="max-width:100%;max-height:300px;display:block;margin:auto;">`;
    document.querySelector('.table-container').classList.add('d-none');
    document.querySelectorAll('[data-type]').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-type="chart"]').classList.add('active');
}

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

function addSqlMessage(sql) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message sql-message';
    messageDiv.innerHTML = `
        <div class="d-flex align-items-center mb-2">
            <i class="fas fa-code me-2 text-success"></i>
            <strong>SQL查询</strong>
        </div>
        <pre>${sql}</pre>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

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

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) typingIndicator.remove();
}

document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// 假设你的“连接数据库”按钮id为 connectDbBtn
const connectDbBtn = document.getElementById('connectDbBtn');
if (connectDbBtn) {
    connectDbBtn.addEventListener('click', connectDatabase);
}
