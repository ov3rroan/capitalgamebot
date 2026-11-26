const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#0b0f1a');
    tg.setBackgroundColor('#0b0f1a');
}

// Для локальной разработки
const API = window.location.origin;
let initData = tg?.initData || '';
let user = null;

// ============ Helpers ============

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => toast.classList.remove('show'), 2800);
}

function formatMoney(n) {
    return new Intl.NumberFormat('ru-RU').format(Math.floor(n)) + ' 💰';
}

async function api(path, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(API + path, opts);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.detail || data.message || 'Ошибка');
    }
    return data;
}

// ============ Auth & Profile ============

async function loadProfile() {
    try {
        const data = await api('/api/auth', 'POST', { initData });
        user = data;
        renderProfile();
    } catch (e) {
        console.error(e);
        // fallback для локального теста
        user = {
            name: 'Тестер',
            balance: 1500,
            energy: 100,
            max_energy: 100,
            level: 1,
            exp: 0,
            influence: 0,
            reputation: 0,
            property_value: 0
        };
        renderProfile();
    }
}

function renderProfile() {
    if (!user) return;
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('user-level').textContent = `Ур. ${user.level}`;
    document.getElementById('balance').textContent = formatMoney(user.balance);
    document.getElementById('energy').textContent = `⚡ ${user.energy}/${user.max_energy}`;
    document.getElementById('stat-influence').textContent = user.influence;
    document.getElementById('stat-reputation').textContent = user.reputation || 0;
    document.getElementById('stat-property').textContent = formatMoney(user.property_value || 0);

    const expNext = user.level * 100;
    const pct = Math.min(100, (user.exp / expNext) * 100);
    document.getElementById('exp-fill').style.width = pct + '%';
}

// ============ Tabs ============

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`tab-${tabName}`).classList.add('active');
    document.querySelector(`.nav-btn[data-tab="${tabName}"]`)?.classList.add('active');

    if (tabName === 'jobs') loadJobs();
    if (tabName === 'property') loadProperties();
    if (tabName === 'top') loadTop();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// ============ Jobs ============

async function loadJobs() {
    const list = document.getElementById('jobs-list');
    list.innerHTML = '<div class="loading">Загрузка работ...</div>';

    try {
        const jobs = await api('/api/jobs');
        list.innerHTML = jobs.map(job => `
            <div class="card">
                <div class="card-icon">${job.icon}</div>
                <div class="card-body">
                    <div class="card-title">${job.name}</div>
                    <div class="card-desc">${job.description}</div>
                    <div class="card-meta">
                        <span class="meta-item green">+${job.base_income} 💰</span>
                        <span class="meta-item">⚡ ${job.energy_cost}</span>
                        <span class="meta-item purple">Ур. ${job.min_level}+</span>
                        ${job.risk > 0.1 ? `<span class="meta-item" style="color:var(--danger)">Риск ${Math.round(job.risk*100)}%</span>` : ''}
                    </div>
                </div>
                <div class="card-action">
                    <button class="btn" onclick="doWork(${job.id})" ${user && user.level < job.min_level ? 'disabled' : ''}>
                        Работать
                    </button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

async function doWork(jobId) {
    try {
        const res = await api('/api/work', 'POST', { initData, job_id: jobId });
        if (res.success) {
            showToast(res.message, 'success');
            user.balance = res.balance;
            user.energy = res.energy;
            user.level = res.level;
            user.exp = res.exp;
            renderProfile();
        } else {
            showToast(res.message, 'error');
            user.energy = res.energy;
            renderProfile();
        }
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ============ Property ============

document.querySelectorAll('.prop-tab').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.prop-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (btn.dataset.prop === 'shop') {
            document.getElementById('property-shop').style.display = 'flex';
            document.getElementById('property-my').style.display = 'none';
            loadPropertyShop();
        } else {
            document.getElementById('property-shop').style.display = 'none';
            document.getElementById('property-my').style.display = 'flex';
            loadMyProperties();
        }
    });
});

async function loadProperties() {
    loadPropertyShop();
}

async function loadPropertyShop() {
    const list = document.getElementById('property-shop');
    list.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const props = await api('/api/properties');
        list.innerHTML = props.map(p => `
            <div class="card">
                <div class="card-icon">${p.icon}</div>
                <div class="card-body">
                    <div class="card-title">${p.name}</div>
                    <div class="card-desc">${p.description}</div>
                    <div class="card-meta">
                        <span class="meta-item green">${formatMoney(p.price)}</span>
                        ${p.income_per_hour > 0 ? `<span class="meta-item">+${p.income_per_hour}/час</span>` : ''}
                        <span class="meta-item purple">Ур. ${p.min_level}+</span>
                    </div>
                </div>
                <div class="card-action">
                    <button class="btn" onclick="buyProperty(${p.id})">Купить</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

async function loadMyProperties() {
    const list = document.getElementById('property-my');
    list.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const data = await api(`/api/my_properties?initData=${encodeURIComponent(initData)}`);
        if (!data.properties.length) {
            list.innerHTML = '<div class="loading">У тебя пока нет имущества. Купи что-нибудь в магазине!</div>';
            return;
        }
        list.innerHTML = `
            <div class="card" style="background:rgba(0,229,192,0.08);border-color:rgba(0,229,192,0.2)">
                <div class="card-body">
                    <div class="card-title">Доступно к сбору</div>
                    <div class="card-desc">${formatMoney(data.total_pending)}</div>
                </div>
                <div class="card-action">
                    <button class="btn btn-success" onclick="collectIncome()">Собрать</button>
                </div>
            </div>
        ` + data.properties.map(p => `
            <div class="card">
                <div class="card-icon">${p.icon}</div>
                <div class="card-body">
                    <div class="card-title">${p.name}</div>
                    <div class="card-meta">
                        <span class="meta-item">+${p.income_per_hour}/час</span>
                        <span class="meta-item green">+${formatMoney(p.pending_income)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

async function buyProperty(id) {
    try {
        const res = await api('/api/buy_property', 'POST', { initData, property_id: id });
        showToast(res.message, 'success');
        user.balance = res.balance;
        user.influence = res.influence;
        renderProfile();
        loadPropertyShop();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function collectIncome() {
    try {
        const res = await api('/api/collect_income', 'POST', { initData });
        showToast(res.message, 'success');
        user.balance = res.balance;
        renderProfile();
        // если открыта вкладка моего имущества — обновим
        if (document.querySelector('.prop-tab[data-prop="my"].active')) {
            loadMyProperties();
        }
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ============ Casino ============

function changeBet(delta) {
    const input = document.getElementById('bet-amount');
    let val = parseInt(input.value) || 100;
    val = Math.max(10, Math.min(50000, val + delta));
    input.value = val;
}

async function playCasino(game) {
    const bet = parseFloat(document.getElementById('bet-amount').value) || 100;
    const resultEl = document.getElementById('casino-result');
    resultEl.className = 'casino-result';
    resultEl.textContent = 'Крутим...';

    try {
        const res = await api('/api/casino', 'POST', { initData, game, bet });
        user.balance = res.balance;
        renderProfile();

        resultEl.textContent = res.result + (res.win > 0 ? `  (+${formatMoney(res.win)})` : '');
        resultEl.classList.add(res.win > bet ? 'win' : (res.win > 0 ? '' : 'lose'));

        if (res.win > bet) {
            showToast(`Выигрыш ${formatMoney(res.win)}!`, 'success');
        }
    } catch (e) {
        resultEl.textContent = e.message;
        resultEl.classList.add('lose');
        showToast(e.message, 'error');
    }
}

// ============ Top ============

async function loadTop() {
    const list = document.getElementById('top-list');
    list.innerHTML = '<div class="loading">Загрузка топа...</div>';

    try {
        const top = await api('/api/top?limit=20');
        if (!top.length) {
            list.innerHTML = '<div class="loading">Пока никого нет в топе</div>';
            return;
        }
        list.innerHTML = top.map(u => `
            <div class="top-item">
                <div class="top-place">${u.place}</div>
                <div class="top-info">
                    <div class="top-name">${u.name}${u.username ? ' @' + u.username : ''}</div>
                    <div class="top-level">Уровень ${u.level} · Влияние ${u.influence}</div>
                </div>
                <div class="top-balance">${formatMoney(u.balance)}</div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

// ============ Init ============

loadProfile();
