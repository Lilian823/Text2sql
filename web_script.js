// 系统配置
let config = {
    apiUrl: 'http://localhost:5000/api/query',
    connectUrl: 'http://localhost:5000/api/connect_db'
};
let conversationId = null;

// 连接数据库按钮逻辑
function handleConnectDbBtnClick() {
    fetch('/api/connect_db', {method: 'POST'})
        .then(resp => resp.json())
        .then(data => {
            const chatMessages = document.getElementById('chatMessages');
            const tipDiv = document.createElement('div');
            tipDiv.className = 'message system-message';
            if (data.success) {
                document.getElementById('dbStatusDot').classList.remove('bg-danger');
                document.getElementById('dbStatusDot').classList.add('bg-success');
                // 状态栏只显示简洁信息
                document.getElementById('dbStatusText').textContent = data.message || '数据库连接成功';
                // 消息框显示详细信息
                tipDiv.style.background = '#eaffea';
                tipDiv.style.color = '#218838';
                tipDiv.innerHTML = '<strong>' + (data.message || '数据库连接成功') + '</strong>';
                chatMessages.appendChild(tipDiv);
                // 新增：导入成功后发送提示消息
                const guideDiv = document.createElement('div');
                guideDiv.className = 'message system-message';
                guideDiv.innerHTML = `
                    <div class="d-flex align-items-center mb-2">
                        <i class="fas fa-robot me-2 text-success"></i>
                        <strong>数据库助手</strong>
                    </div>
                    <p>我已经收到您的数据库文件啦！你可以通过下方的输入框开始向我提问啦~</p>
                `;
                chatMessages.appendChild(guideDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                document.getElementById('dbStatusDot').classList.remove('bg-success');
                document.getElementById('dbStatusDot').classList.add('bg-danger');
                // 状态栏只显示简洁信息
                document.getElementById('dbStatusText').textContent = data.error || '数据库导入失败';
                // 消息框显示详细错误（含detail）
                tipDiv.style.background = '#ffeaea';
                tipDiv.style.color = '#b94a48';
                let detailMsg = '';
                if (data.detail) {
                    detailMsg = '<br><span style="font-size:0.95em;color:#b94a48;">详细信息：' + data.detail + '</span>';
                }
                tipDiv.innerHTML = '<strong>' + (data.error || '数据库导入失败') + '</strong>' + detailMsg;
                chatMessages.appendChild(tipDiv);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(() => alert('连接数据库失败'));
}
document.getElementById('connectDbBtn').addEventListener('click', handleConnectDbBtnClick);
// 聊天欢迎区“连接数据库”按钮联动
setTimeout(function() {
    const btn = document.getElementById('welcomeConnectBtn');
    if (btn) {
        btn.addEventListener('click', handleConnectDbBtnClick);
    }
}, 100);
// 图表类型切换逻辑
const chartTypes = ['bar', 'pie', 'line'];
document.querySelectorAll('#chartTypeToggle [data-chart]').forEach(btn => {
    btn.addEventListener('click', function() {
        chartTypes.forEach(type => {
            document.getElementById(type+'ChartBox').style.display = 'none';
            document.querySelector(`[data-chart="${type}"]`).classList.remove('active');
        });
        const type = this.getAttribute('data-chart');
        document.getElementById(type+'ChartBox').style.display = 'flex';
        this.classList.add('active');
    });
});
// 后端图片展示逻辑
function showChartImages(chartUrls) {
    const types = ['bar', 'pie', 'line'];
    types.forEach(type => {
        const img = document.getElementById(type+'ChartImg');
        const none = document.getElementById(type+'ChartNone');
        if (chartUrls && chartUrls[type]) {
            img.src = chartUrls[type];
            img.style.display = 'block';
            none.style.display = 'none';
        } else {
            img.style.display = 'none';
            none.style.display = 'block';
        }
    });
    // 默认切换到有图的类型，否则切到bar
    let shown = false;
    types.forEach(type => {
        if (chartUrls && chartUrls[type]) {
            document.getElementById(type+'ChartBox').style.display = 'flex';
            document.querySelector(`[data-chart="${type}"]`).classList.add('active');
            shown = true;
        } else {
            document.getElementById(type+'ChartBox').style.display = 'none';
            document.querySelector(`[data-chart="${type}"]`).classList.remove('active');
        }
    });
    if (!shown) {
        document.getElementById('barChartBox').style.display = 'flex';
        document.querySelector('[data-chart="bar"]').classList.add('active');
    }
}

// 下载当前图表图片
function getCurrentChartType() {
    const activeBtn = document.querySelector('#chartTypeToggle .active[data-chart]');
    return activeBtn ? activeBtn.getAttribute('data-chart') : 'bar';
}
document.getElementById('downloadChartBtn').addEventListener('click', function() {
    const type = getCurrentChartType();
    const img = document.getElementById(type + 'ChartImg');
    if (img && img.src && img.style.display !== 'none') {
        const a = document.createElement('a');
        a.href = img.src;
        a.download = type + '_chart.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } else {
        alert('暂无可下载的图表图片');
    }
});



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
        // 优先显示后端返回的 error 字段内容（如有），否则显示默认提示
        let errMsg = '请求处理失败';
        if (error.response && error.response.data) {
            // 兼容后端返回字符串或对象
            if (typeof error.response.data === 'string') {
                showErrorSystemMessage(error.response.data);
            } else if (error.response.data.error) {
                showErrorSystemMessage(error.response.data.error);
            } else {
                showErrorSystemMessage(errMsg);
            }
        } else {
            showErrorSystemMessage(errMsg);
        }
    }
}

function handleResponse(data) {
    if (data.error) {
        // 只显示后端返回的 error 字段内容，并用红色消息框
        showErrorSystemMessage(data.error);
        return;
    }
    if (data.sql) addSqlMessage(data.sql);
    // 只在没有 error 时才处理 message 字段
    if (data.message) {
        addMessage(data.message, 'system');
    }
    // 新增：处理 chart_urls
    if (data.chart_urls) {
        document.getElementById('visualizationContainer').style.display = 'block';
        showChartImages(data.chart_urls);
    }
}

// 新增：红色系统消息框
function showErrorSystemMessage(content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message';
    messageDiv.style.background = '#ffeaea';
    messageDiv.style.color = '#b94a48';
    messageDiv.innerHTML = `
        <div class="d-flex align-items-center mb-2">
            <i class="fas fa-exclamation-triangle me-2" style="color:#b94a48"></i>
            <strong>系统提示</strong>
        </div>
        <p>${content}</p>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
    // 去除内容中的所有星号
    const cleanContent = content.replace(/\*/g, '');
    let fontStyle = "font-family:inherit;font-size:inherit;white-space:pre-wrap;margin:0;";
    if (sender === 'user') {
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-user me-2 text-primary"></i>
                <strong>用户</strong>
            </div>
            <pre style="${fontStyle}">${cleanContent}</pre>
        `;
    } else {
        messageDiv.className = 'message system-message';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-robot me-2 text-success"></i>
                <strong>数据库助手</strong>
            </div>
            <pre style="${fontStyle}">${cleanContent}</pre>
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
