// Dashboard JavaScript
// Part 1: Setup, Tab Navigation, and API Functions

const API_BASE = '/api';
let cryptoChart, emasChart;
// Global data stores for AI Summary
let cryptoData = null;
let emasData = null;
let sembakoData = null;

// ============ Initialize ============
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initTableControls();
    loadAllData();
    updateTime();
    setInterval(updateTime, 1000);
    setInterval(loadAllData, 30000); // Refresh every 30 seconds
    // Peternakan filter buttons (setup once, not on every refresh)
    document.querySelectorAll('#peternakan .filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#peternakan .filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderPeternakanTable(e.target.dataset.filter);
        });
    });
});

// ============ Tab Navigation ============
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

// ============ Table Sort/Filter Controls ============
function initTableControls() {
    // Map table prefix to tbody id
    const tables = ['crypto', 'emas'];
    
    tables.forEach(prefix => {
        const controls = document.querySelector(`#${prefix} .table-controls`);
        if (!controls) return;
        
        const buttons = controls.querySelectorAll('.filter-btn');
        const startInput = controls.querySelector(`#${prefix}-date-start`);
        const endInput = controls.querySelector(`#${prefix}-date-end`);
        
        // Sort buttons
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                sortTable(prefix, btn.dataset.sort);
            });
        });
        
        // Date filter inputs
        [startInput, endInput].forEach(input => {
            if (input) input.addEventListener('change', () => filterByDate(prefix));
        });
    });
}

function sortTable(prefix, order) {
    const tbody = document.getElementById(`${prefix}-tbody`);
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aDate = a.cells[0]?.textContent.trim() || '';
        const bDate = b.cells[0]?.textContent.trim() || '';
        // Parse DD/MM/YYYY or YYYY-MM-DD
        const parse = (s) => {
            if (s.includes('/')) {
                const [d, m, y] = s.split('/');
                return new Date(y, m - 1, d);
            }
            return new Date(s);
        };
        const diff = parse(aDate) - parse(bDate);
        return order === 'asc' ? diff : -diff;
    });
    
    tbody.innerHTML = '';
    rows.forEach(r => tbody.appendChild(r));
}

function filterByDate(prefix) {
    const start = document.getElementById(`${prefix}-date-start`)?.value;
    const end = document.getElementById(`${prefix}-date-end`)?.value;
    const tbody = document.getElementById(`${prefix}-tbody`);
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.forEach(row => {
        const cellDate = row.cells[0]?.textContent.trim() || '';
        if (!start && !end) { row.style.display = ''; return; }
        
        // Parse date from cell
        let rowDate;
        if (cellDate.includes('/')) {
            const [d, m, y] = cellDate.split('/');
            rowDate = new Date(y, m - 1, d);
        } else {
            rowDate = new Date(cellDate);
        }
        
        const show = (!start || rowDate >= new Date(start)) && (!end || rowDate <= new Date(end));
        row.style.display = show ? '' : 'none';
    });
}

function switchTab(tabName) {
    // Hide all tabs
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => tab.classList.remove('active'));
    
    // Remove active state from all buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    const el = document.getElementById(tabName);
    if (!el) return;
    el.classList.add('active');
    
    // Mark button as active
    const btn = document.querySelector(`[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');
}

// ============ API Functions ============
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}/${endpoint}`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function loadAllData() {
    await Promise.all([
        loadSembakoData(),
        loadCryptoData(),
        loadEmasData(),
        loadPertanianData(),
        loadPeternakanData(),
        loadSahamData(),
        loadPakanData(),
        loadSentimenData(),
        loadKursData(),
        loadMinyakData(),
        loadBIData(),
        loadCPOData(),
        loadAlertsData(),
        checkHealth()
    ]);
    // AI analysis only on button click, not auto (save tokens)
}

// ============ Format Functions ============
function formatCurrency(value) {
    if (value == null || isNaN(value)) return '-';
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatIDR(value) {
    if (value == null || isNaN(value)) return '-';
    return new Intl.NumberFormat('id-ID').format(Math.round(value));
}

function formatUSD(value) {
    if (value == null || isNaN(value)) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value) {
    if (value == null || isNaN(value)) return '-';
    return (value > 0 ? '+' : '') + value.toFixed(2) + '%';
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('id-ID', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}

// ============ Sembako Data ============
async function loadSembakoData() {
    const response = await fetchData('sembako');
    if (!response || !response.data || response.data.length === 0) return;
    
    const data = response.data;
    sembakoData = response; // save to global for AI Summary
    const latest = data[data.length - 1];
    
    // Update overview cards (non-critical — wrapped so table always loads)
    try {
        document.getElementById('sembako-date').textContent = response.last_update || formatDate(latest.tanggal);
        document.getElementById('mini-beras').textContent = formatCurrency(latest.beras_premium);
        document.getElementById('mini-medium').textContent = formatCurrency(latest.beras_medium);
        document.getElementById('mini-gas').textContent = latest.gas_elpiji ? formatCurrency(latest.gas_elpiji) : 'Data belum tersedia';
        document.getElementById('mini-telur').textContent = latest.telur_ras ? formatCurrency(latest.telur_ras) : 'Data belum tersedia';
    } catch(e) { console.warn('Overview card error:', e); }
    
    // Fill table
    const tbody = document.getElementById('sembako-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatCurrency(row.beras_premium)}</td>
            <td>${formatCurrency(row.beras_medium)}</td>
            <td>${formatCurrency(row.minyak_goreng)}</td>
            <td>${formatCurrency(row.gula_pasir)}</td>
            <td>${formatCurrency(row.garam_bata || row.garam)}</td>
            <td>${formatCurrency(row.cabai_merah)}</td>
            <td>${formatCurrency(row.cabai_rawit)}</td>
            <td>${formatCurrency(row.bawang_merah)}</td>
            <td>${formatCurrency(row.bawang_putih)}</td>
            <td>${formatCurrency(row.telur_ras)}</td>
            <td>${formatCurrency(row.telur_kampung)}</td>
            <td>${formatCurrency(row.ayam_ras)}</td>
            <td>${formatCurrency(row.ayam_kampung)}</td>
            <td>${formatCurrency(row.daging_sapi)}</td>
            <td>${formatCurrency(row.gas_elpiji)}</td>
            <td>${formatCurrency(row.susu_km_bendera)}</td>
            <td>${formatCurrency(row.susu_km_indomilk)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Crypto Data ============
async function loadCryptoData() {
    const response = await fetchData('crypto');
    if (!response || !response.data || response.data.length === 0) return;
    
    const data = response.data;
    cryptoData = response; // global for AI Summary
    const latest = data[data.length - 1];
    
    // Update overview cards (non-critical — wrapped so table always loads)
    try {
        document.getElementById('crypto-mcap').textContent = latest.sentimen || 'NETRAL';
        document.getElementById('mini-btc').textContent = formatUSD(latest.btc_usd);
        document.getElementById('mini-eth').textContent = formatUSD(latest.eth_usd);
        document.getElementById('mini-sol').textContent = formatUSD(latest.sol_usd);
        document.getElementById('mini-ada').textContent = latest.ada_usd ? formatUSD(latest.ada_usd) : 'Data belum tersedia';
    } catch(e) { console.warn('Crypto overview error:', e); }
    
    // Fill table
    const tbody = document.getElementById('crypto-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        const btc24hClass = row.btc_24h < 0 ? 'text-danger' : 'text-success';
        const eth24hClass = (row.eth_24h||0) < 0 ? 'text-danger' : 'text-success';
        const sol24hClass = (row.sol_24h||0) < 0 ? 'text-danger' : 'text-success';
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatUSD(row.btc_usd)}</td>
            <td class="${btc24hClass}">${formatPercent(row.btc_24h)}</td>
            <td>${formatUSD(row.eth_usd)}</td>
            <td class="${eth24hClass}">${formatPercent(row.eth_24h)}</td>
            <td>${formatUSD(row.sol_usd)}</td>
            <td class="${sol24hClass}">${formatPercent(row.sol_24h)}</td>
            <td><span class="badge">${row.sentimen || 'NETRAL'}</span></td>
        `;
        tbody.appendChild(tr);
    });
    
    // Default sort: Terbaru (desc)
    sortTable('crypto', 'desc');
    
    // Update crypto chart
    updateCryptoChart(data);
}

// ============ Emas Data ============
async function loadEmasData() {
    const response = await fetchData('emas');
    if (!response || !response.data || response.data.length === 0) return;
    
    const data = response.data;
    const latest = data[data.length - 1];
    
    // Update overview cards (non-critical)
    try {
        document.getElementById('emas-price').textContent = formatCurrency(latest.antam_beli);
        document.getElementById('mini-emas-beli').textContent = formatCurrency(latest.antam_beli);
        document.getElementById('mini-emas-back').textContent = formatCurrency(latest.antam_buyback);
        document.getElementById('mini-spread').textContent = formatCurrency(latest.selisih);
        document.getElementById('mini-ubs').textContent = latest.ubs_beli ? formatCurrency(latest.ubs_beli) : 'Data belum tersedia';
    } catch(e) { console.warn('Emas overview error:', e); }
    
    // Fill table
    const tbody = document.getElementById('emas-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatCurrency(row.antam_beli)}</td>
            <td>${formatCurrency(row.antam_buyback)}</td>
            <td>${formatCurrency(row.antam_pegadaian)}</td>
            <td>${formatCurrency(row.galeri24)}</td>
            <td>${formatCurrency(row.ubs_beli)}</td>
            <td>${formatCurrency(row.selisih)}</td>
            <td>${formatPercent(row.spread_persen)}</td>
        `;
        tbody.appendChild(tr);
    });
    
    // Default sort: Terbaru (desc)
    sortTable('emas', 'desc');
    
    // Update emas chart
    updateEmasChart(data);
}

// ============ Pertanian Data ============
async function loadPertanianData() {
    const response = await fetchData('pertanian');
    if (!response || !response.data || response.data.length === 0) return;
    
    const data = response.data;
    
    // Fill table
    const tbody = document.getElementById('pertanian-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatCurrency(row.jagung_pipil)}</td>
            <td>${formatCurrency(row.jagung_pakan)}</td>
            <td>${formatCurrency(row.kedelai_impor)}</td>
            <td>${formatCurrency(row.kedelai_lokal)}</td>
            <td>${formatCurrency(row.pakan_broiler)}</td>
            <td>${formatCurrency(row.pakan_layer)}</td>
            <td>${formatCurrency(row.bungkil_kedelai)}</td>
            <td>${formatCurrency(row.jagung_giling)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Peternakan Data (Hulu to Hilir) ============
let peternakanData = [];

async function loadPeternakanData() {
    const response = await fetchData('peternakan');
    if (!response || !response.data || response.data.length === 0) return;
    
    peternakanData = response.data;
    
    // Fill table
    renderPeternakanTable('all', true);
}

function renderPeternakanTable(filter, initial=false) {
    const tbody = document.getElementById('peternakan-tbody');
    tbody.innerHTML = '';
    
    const filtered = filter === 'all' 
        ? peternakanData 
        : peternakanData.filter(row => row.kategori === filter);
    
    filtered.forEach(row => {
        const tr = document.createElement('tr');
        const catClass = row.kategori.toLowerCase();
        tr.innerHTML = `
            <td><span class="badge badge-${catClass}">${row.kategori}</span></td>
            <td>${row.sub_kategori}</td>
            <td>${row.produk}</td>
            <td class="price">${formatCurrency(row.harga)}</td>
            <td>${row.satuan}</td>
            <td>${row.sumber}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Pakan/Feed Data ============
async function loadPakanData() {
    const response = await fetchData('pakan');
    if (!response || !response.data || response.data.length === 0) return;

    const data = response.data;

    // Fill table
    const tbody = document.getElementById('pakan-tbody');
    tbody.innerHTML = '';

    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatCurrency(row.jagung_pipilan)}</td>
            <td>${formatCurrency(row.bungkil_kedelai)}</td>
            <td>${formatCurrency(row.dedak_padi)}</td>
            <td>${formatCurrency(row.tepung_ikan)}</td>
            <td>${formatCurrency(row.pollard)}</td>
            <td>${formatCurrency(row.biji_kapuk)}</td>
            <td>${formatCurrency(row.tepung_darah)}</td>
            <td>${formatCurrency(row.tepung_tulang)}</td>
            <td>${formatCurrency(row.molases)}</td>
            <td>${formatCurrency(row.bungkil_kelapa)}</td>
            <td>${formatCurrency(row.gaplek)}</td>
            <td>${formatCurrency(row.bungkil_sawit)}</td>
            <td>${formatCurrency(row.ampas_tahu)}</td>
            <td>${formatCurrency(row.tepung_bulu_ayam)}</td>
            <td>${formatCurrency(row.kulit_kentang)}</td>
            <td>${formatCurrency(row.onggok)}</td>
            <td>${formatCurrency(row.bungkil_kacang_tanah)}</td>
            <td>${formatCurrency(row.dedak_halus)}</td>
            <td>${formatCurrency(row.sorgum)}</td>
            <td>${formatCurrency(row.menir)}</td>
            <td>${formatCurrency(row.corn_gluten_feed)}</td>
            <td>${formatCurrency(row.rice_polish)}</td>
            <td>${formatCurrency(row.mung_bean_husk)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Sentimen Berita ============
async function loadSentimenData() {
    const response = await fetchData('sentimen'); // Panggil API sentimen baru
    if (!response || !response.data || response.data.length === 0) return;

    const data = response.data;
    const tbody = document.getElementById('sentimen-tbody');
    tbody.innerHTML = '';

    data.slice(-10).reverse().forEach(row => { // Tampilkan 10 berita terakhir, dari terbaru
        const tr = document.createElement('tr');
        
        let sentimentColor = 'grey';
        if (row.sentimen === 'POSITIF') sentimentColor = 'green';
        else if (row.sentimen === 'NEGATIF') sentimentColor = 'red';

        tr.innerHTML = `
            <td>${formatDate(row.tanggal)} ${row.waktu || ''}</td>
            <td>${row.keyword || '-'}</td>
            <td>${(row.headline || '').substring(0, 70)}...</td>
            <td style="color: ${sentimentColor}; font-weight: bold;">${row.sentimen} (${row.score})</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Keuangan Data ============
async function loadKeuanganData() {
    const response = await fetchData('keuangan');
    if (!response || !response.data || response.data.length === 0) return;
    
    const data = response.data;
    
    // Calculate summary
    let totalMasuk = 0, totalKeluar = 0;
    data.forEach(row => {
        if (row.jenis === 'Pemasukan') totalMasuk += row.jumlah || 0;
        if (row.jenis === 'Pengeluaran') totalKeluar += row.jumlah || 0;
    });
    
    // Update overview cards
    document.getElementById('keuangan-count').textContent = data.length;
    document.getElementById('mini-masuk').textContent = formatCurrency(totalMasuk);
    document.getElementById('mini-keluar').textContent = formatCurrency(totalKeluar);
    document.getElementById('mini-saldo').textContent = formatCurrency(totalMasuk - totalKeluar);
    
    // Fill table
    const tbody = document.getElementById('keuangan-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        const jenisBadge = row.jenis === 'Pemasukan' ? 
            '<span class="badge badge-success">Masuk</span>' :
            '<span class="badge badge-danger">Keluar</span>';
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${jenisBadge}</td>
            <td>${row.kategori || '-'}</td>
            <td>${row.deskripsi || '-'}</td>
            <td>${formatCurrency(row.jumlah)}</td>
            <td>${row.metode || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ Health Check ============
async function checkHealth() {
    const health = await fetchData('health');
    const statusEl = document.getElementById('health-status');
    if (health && health.status === 'healthy') {
        statusEl.textContent = '● Online';
        statusEl.className = 'status-badge status-ok';
    } else {
        statusEl.textContent = '● Offline';
        statusEl.className = 'status-badge status-error';
    }
}

// ============ Time Update ============
function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeStr;
    document.getElementById('footer-time').textContent = now.toLocaleString('id-ID');
}

// ============ Chart Functions ============
function getChartOptions(isMobile, opts) {
    opts = opts || {};
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    boxWidth: isMobile ? 10 : 14,
                    padding: isMobile ? 10 : 20,
                    usePointStyle: true,
                    pointStyle: 'circle',
                    font: { size: isMobile ? 11 : 13, weight: '500' }
                }
            },
            tooltip: {
                enabled: true,
                backgroundColor: 'rgba(15,23,42,0.9)',
                titleFont: { size: isMobile ? 11 : 13, weight: '600' },
                bodyFont: { size: isMobile ? 10 : 12 },
                padding: 10,
                cornerRadius: 8,
                displayColors: true,
                boxPadding: 4
            }
        },
        scales: {
            y: {
                beginAtZero: opts.beginAtZero !== false,
                grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                border: { display: false },
                ticks: {
                    font: { size: isMobile ? 10 : 12 },
                    maxTicksLimit: isMobile ? 5 : 6,
                    padding: 8,
                    callback: opts.yFmt || undefined
                }
            },
            x: {
                grid: { display: false },
                border: { display: false },
                ticks: {
                    font: { size: isMobile ? 9 : 11 },
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: isMobile ? 5 : 8
                }
            }
        }
    };
}

function isMobileDevice() {
    return window.innerWidth < 768;
}

function updateCryptoChart(data) {
    // Take last 7 days
    const last7 = data.slice(-7);
    const labels = last7.map(d => formatDate(d.tanggal));
    const btc = last7.map(d => d.btc_usd || 0);
    const eth = last7.map(d => d.eth_usd || 0);

    const ctx = document.getElementById('cryptoChart');
    if (!ctx) return;

    if (cryptoChart) cryptoChart.destroy();
    const isMobile = isMobileDevice();

    cryptoChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'BTC (USD)',
                    data: btc,
                    borderColor: '#f7931a',
                    backgroundColor: 'rgba(247,147,26,0.08)',
                    borderWidth: 2.5,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#f7931a',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'ETH (USD)',
                    data: eth,
                    borderColor: '#627eea',
                    backgroundColor: 'rgba(98,126,234,0.08)',
                    borderWidth: 2.5,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#627eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: getChartOptions(isMobile, {
            yFmt: v => '$' + (v / 1000).toFixed(0) + 'K'
        })
    });

    // Add second Y axis for ETH
    cryptoChart.options.scales.y1 = {
        position: 'right',
        grid: { drawOnChartArea: false },
        border: { display: false },
        ticks: {
            font: { size: isMobile ? 10 : 12 },
            color: '#627eea',
            callback: v => '$' + (v / 1000).toFixed(0) + 'K'
        }
    };
    cryptoChart.options.scales.y.ticks.color = '#f7931a';
    cryptoChart.update();
}

function updateEmasChart(data) {
    const last30 = data.slice(-30);
    const labels = last30.map(d => formatDate(d.tanggal));
    const antamBeli = last30.map(d => d.antam_beli || 0);
    const antamBuyback = last30.map(d => d.antam_buyback || 0);

    const ctx = document.getElementById('emasChart');
    if (!ctx) return;

    if (emasChart) emasChart.destroy();
    const isMobile = isMobileDevice();

    emasChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Antam Beli',
                    data: antamBeli,
                    borderColor: '#eab308',
                    backgroundColor: 'rgba(234,179,8,0.06)',
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#eab308',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Antam Buyback',
                    data: antamBuyback,
                    borderColor: '#a16207',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 3],
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    pointBackgroundColor: '#a16207',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: getChartOptions(isMobile, {
            yFmt: v => 'Rp ' + (v / 1000000).toFixed(1) + 'jt'
        })
    });
}

// Handle window resize for charts
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        // Reinitialize charts on resize if data is loaded
        if (typeof cryptoChart !== 'undefined' || typeof emasChart !== 'undefined') {
            loadAllData();
        }
    }, 250);
});

// ============ Saham Data (IHSG & Bluechip) ============
let sahamData = {};

async function loadSahamData() {
    const response = await fetchData('saham');
    if (!response || !response.data) return;

    sahamData = response.data;

    // Render IHSG summary
    renderIHSGSummary();

    // Render Sektor
    renderSektorList();

    // Render Watchlist
    renderWatchlist();

    // Render Bluechip table
    renderBluechipTable();

    // Update footer time
    if (response.last_update) {
        document.getElementById('footer-time').textContent = response.last_update;
    }
}

function renderIHSGSummary() {
    const ihsgData = sahamData.ihsg || [];
    if (ihsgData.length === 0) return;

    const latest = ihsgData[ihsgData.length - 1];

    function num(v) { return v != null ? Number(v).toLocaleString('id-ID') : '-'; }

    const ihsgEl = document.getElementById('overview-ihsg');
    const subEl = document.getElementById('overview-ihsg-sub');
    if (ihsgEl) ihsgEl.textContent = num(latest.ihsg);
    if (subEl) {
        const chg = latest.change_pct != null ? (latest.change_pct > 0 ? '+' : '') + Number(latest.change_pct).toFixed(2) + '%' : '-';
        const cls = latest.change_pct > 0 ? 'val-pos' : latest.change_pct < 0 ? 'val-neg' : '';
        subEl.innerHTML = `<span class="${cls}">${chg}</span> · H: ${num(latest.high)} L: ${num(latest.low)}`;
    }
}

function renderSektorList() {
    const container = document.getElementById('sektor-list');
    if (!container) return; // element may not exist in HTML
    const sektorData = sahamData.sektor || [];
    if (sektorData.length === 0) {
        container.innerHTML = '<div class="loading">No data</div>';
        return;
    }

    container.innerHTML = '';
    sektorData.forEach(sek => {
        const div = document.createElement('div');
        div.className = 'sektor-item';
        const changeClass = sek.daily_change > 0 ? 'positive' : sek.daily_change < 0 ? 'negative' : 'neutral';
        div.innerHTML = `
            <span class="sektor-name">${sek.sektor}</span>
            <span class="sektor-value">${sek.value ? sek.value.toLocaleString('id-ID') : '-'}</span>
            <span class="sektor-change ${changeClass}">${sek.change_pct ? (sek.change_pct > 0 ? '+' : '') + sek.change_pct + '%' : '-'}</span>
        `;
        container.appendChild(div);
    });
}

function renderWatchlist() {
    const tbody = document.getElementById('watchlist-tbody');
    const watchlist = sahamData.watchlist || [];
    if (watchlist.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No data</td></tr>';
        return;
    }

    tbody.innerHTML = '';
    watchlist.forEach(stock => {
        const tr = document.createElement('tr');
        const recClass = stock.recommendation === 'BUY' ? 'rec-buy' : stock.recommendation === 'SELL' ? 'rec-sell' : 'rec-hold';
        tr.innerHTML = `
            <td><strong>${stock.symbol}</strong></td>
            <td>${stock.nama || '-'}</td>
            <td>${stock.harga ? 'Rp ' + stock.harga.toLocaleString('id-ID') : '-'}</td>
            <td class="${stock.rsi < 40 ? 'rsi-oversold' : stock.rsi > 70 ? 'rsi-overbought' : ''}">${stock.rsi || '-'}</td>
            <td><span class="badge ${recClass}">${stock.recommendation || '-'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderBluechipTable() {
    const tbody = document.getElementById('bluechip-tbody');
    const bluechip = sahamData.bluechip || [];
    if (bluechip.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No data</td></tr>';
        return;
    }

    tbody.innerHTML = '';
    bluechip.forEach(stock => {
        const tr = document.createElement('tr');
        const recClass = stock.recommendation === 'BUY' ? 'rec-buy' : stock.recommendation === 'SELL' ? 'rec-sell' : 'rec-hold';
        const chgClass = stock.daily_chg > 0 ? 'positive' : stock.daily_chg < 0 ? 'negative' : 'neutral';
        tr.innerHTML = `
            <td><strong>${stock.symbol}</strong></td>
            <td>${stock.nama || '-'}</td>
            <td>${stock.sektor || '-'}</td>
            <td>${stock.harga ? 'Rp ' + stock.harga.toLocaleString('id-ID') : '-'}</td>
            <td class="${chgClass}">${stock.daily_chg_pct ? (stock.daily_chg_pct > 0 ? '+' : '') + stock.daily_chg_pct + '%' : '-'}</td>
            <td class="${stock.rsi < 40 ? 'rsi-oversold' : stock.rsi > 70 ? 'rsi-overbought' : ''}">${stock.rsi || '-'}</td>
            <td>${stock.trend || '-'}</td>
            <td>${stock.signal || '-'}</td>
            <td><span class="badge ${recClass}">${stock.recommendation || '-'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ============ AI Analysis (Persistent Job System) ============
let aiPollInterval = null;
let currentAiMode = 'quick';
let currentAiJobId = null;

function setAiMode(mode) {
    currentAiMode = mode;
    document.querySelectorAll('.ai-mode-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.ai-mode-btn[data-mode="${mode}"]`);
    if (btn) btn.classList.add('active');
}
function cancelCurrentAiJob() {
    if (currentAiJobId) cancelAiJob(currentAiJobId);
}

// --- Provider Status (9Router) ---
const ROUTER_LABELS = {r1:'GPT-4o',r2:'GPT-4o Mini',r3:'Claude 3.5',r4:'Claude 3 Haiku',r5:'Llama 70B',r6:'Llama 8B',r7:'Gemini Flash',r8:'DeepSeek R1',r9:'Mixtral'};
const ROUTER_SC = {HEALTHY:'#22c55e',DEGRADED:'#eab308',RATE_LIMITED:'#a855f7',TIMEOUT:'#f97316',AUTH_ERROR:'#ef4444',INVALID_RESPONSE:'#ef4444',UNAVAILABLE:'#ef4444',CHECKING:'#94a3b8',DISABLED:'#64748b'};
let _aiProviderData = null;
async function loadAiProviderStatus() {
    const el = document.getElementById('ai-provider-status');
    if (!el) return;
    try {
        const resp = await fetch('/api/ai/provider-status');
        const data = await resp.json();
        _aiProviderData = data;
        if (!data.available && data.error) {
            const code = data.error_code || '';
            el.innerHTML = `<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span style="color:#ef4444">●</span>
                <span>Sistem AI: <strong>${data.error}</strong> ${code ? '<code style="font-size:11px;color:var(--text3)">'+code+'</code>' : ''}</span>
                <button onclick="loadAiProviderStatus()" style="background:var(--accent);color:#fff;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:12px">Coba Lagi</button>
            </div>`;
            disableAiStart();
            return;
        }
        const routers = data.routers || {};
        const hc = data.healthy_count || 0;
        const tc = data.total_count || 9;
        const ar = data.active_model || '-';
        let html = `<span style="font-size:12px;color:var(--text3)">Router: <strong style="color:${hc>0?'#22c55e':'#ef4444'}">${hc}/${tc}</strong> sehat</span>`;
        if (ar) html += ` · <span style="font-size:11px;color:var(--text3)">Aktif: <strong>${ar}</strong></span>`;
        html += `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">`;
        for (const [rid, info] of Object.entries(routers)) {
            const sc = ROUTER_SC[info.status] || '#64748b';
            const label = ROUTER_LABELS[rid] || rid;
            const lat = info.latency_ms ? info.latency_ms.toFixed(0)+'ms' : '';
            const err = info.error_code ? ` title="${info.error_code}: ${info.sanitized_error_message||''}"` : '';
            html += `<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border:1px solid ${sc}33;border-radius:12px;font-size:11px;cursor:default"${err}>
                <span style="color:${sc};font-size:10px">●</span>${label}${lat ? ' '+lat : ''}
            </span>`;
        }
        html += `</div>`;
        html += `<button onclick="loadAiProviderStatus()" style="background:var(--bg);color:var(--text3);border:1px solid var(--border);padding:4px 12px;border-radius:4px;cursor:pointer;font-size:12px;margin-top:6px">⟳ Periksa Ulang</button>`;
        el.innerHTML = html;
        if (hc > 0) enableAiStart(); else {
            disableAiStart();
            const b = document.getElementById('ai-start-btn');
            if (b) b.title = 'Tidak ada router sehat. Periksa konfigurasi AI_ROUTER_API_KEY.';
        }
    } catch(e) {
        el.innerHTML = `<span style="color:#ef4444">Gagal memeriksa: ${e.message}</span> <button onclick="loadAiProviderStatus()" style="background:var(--accent);color:#fff;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:12px">Coba Lagi</button>`;
        disableAiStart();
    }
}
function disableAiStart() { const b=document.getElementById('ai-start-btn'); if(b){b.disabled=true;b.style.opacity='0.5';} }
function enableAiStart() { const b=document.getElementById('ai-start-btn'); if(b){b.disabled=false;b.style.opacity='1';b.title='Mulai analisis';} }

// --- Start Analysis ---
async function startAiAnalysis(mode) {
    const btn = document.getElementById('ai-start-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Memulai...'; }
    try {
        const resp = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode})
        });
        const data = await resp.json();
        if (data.active_job_id) {
            showAiNotification('Job aktif sedang berjalan ('+data.status+').', 'warning');
            startAiProgressPolling(data.active_job_id);
            if (btn) { btn.disabled = false; btn.textContent = '🚀 Mulai Analisis'; }
            return;
        }
        if (data.job_id) {
            startAiProgressPolling(data.job_id);
        } else if (data.error) {
            const errMsg = data.error_code ? data.error + ' [' + data.error_code + ']' : data.error;
            showAiNotification(errMsg, 'error');
            if (btn) { btn.disabled = false; btn.textContent = '🚀 Mulai Analisis'; }
        }
    } catch(e) {
        showAiNotification('Gagal memulai: ' + e.message, 'error');
        if (btn) { btn.disabled = false; btn.textContent = '🚀 Mulai Analisis'; }
    }
}

// --- Progress Polling ---
function startAiProgressPolling(jobId) {
    if (aiPollInterval) clearInterval(aiPollInterval);
    currentAiJobId = jobId;
    showAiProgressPanel(true);
    const cancelBtn = document.getElementById('ai-cancel-btn');
    if (cancelBtn) cancelBtn.style.display = 'inline-block';
    aiPollInterval = setInterval(() => pollAiJob(jobId), 2000);
    pollAiJob(jobId);
}
async function pollAiJob(jobId) {
    try {
        const resp = await fetch('/api/ai/jobs/' + jobId);
        const data = await resp.json();
        if (data.error) return;
        const job = data.job;
        const agents = data.agents || [];
        updateAiProgressUI(job, agents);
        if (['COMPLETED','FAILED','CANCELLED','PARTIAL'].includes(job.status)) {
            if (aiPollInterval) { clearInterval(aiPollInterval); aiPollInterval = null; }
            showAiProgressPanel(false);
            const cancelBtn = document.getElementById('ai-cancel-btn');
            if (cancelBtn) cancelBtn.style.display = 'none';
            currentAiJobId = null;
            if (job.status === 'COMPLETED') {
                showAiNotification('Analisis selesai!', 'success');
                displayAiResult(job);
            } else if (job.status === 'PARTIAL') {
                showAiNotification('Analisis sebagian selesai. Ada agent gagal.', 'warning');
                displayAiResult(job);
            } else if (job.status === 'FAILED') {
                const errCode = job.error_code ? ' [' + job.error_code + ']' : '';
                showAiNotification('Analisis gagal: ' + (job.error_message||'') + errCode, 'error');
            } else {
                showAiNotification('Analisis dibatalkan.', 'info');
            }
            loadAiHistory();
            const btn = document.getElementById('ai-start-btn');
            if (btn) { btn.disabled = false; btn.textContent = '🚀 Mulai Analisis'; btn.style.opacity='1'; }
        }
    } catch(e) {}
}
function showAiProgressPanel(show) {
    const a = document.getElementById('ai-agent-status');
    const p = document.getElementById('ai-progress');
    if (a) a.style.display = show ? 'flex' : 'none';
    if (p) p.style.display = show ? 'block' : 'none';
}
function updateAiProgressUI(job, agents) {
    const bar = document.getElementById('ai-progress-bar');
    const text = document.getElementById('ai-progress-text');
    if (bar) bar.style.width = (job.progress||0)+'%';
    const done = agents.filter(a=>a.status==='COMPLETED').length;
    const run = agents.filter(a=>a.status==='RUNNING').length;
    if (text) text.textContent = job.status + ' · ' + (job.progress||0).toFixed(0) + '% · ' + done + '/' + agents.length + ' selesai';
    const st = document.getElementById('ai-agent-status');
    if (!st) return;
    const icons = {PENDING:'○',QUEUED:'○',RUNNING:'●',WAITING_PROVIDER:'⏳',RETRYING:'↻',COMPLETED:'✓',FAILED:'✗',SKIPPED:'⊘',CANCELLED:'⊘'};
    const cols = {PENDING:'var(--text3)',QUEUED:'var(--text3)',RUNNING:'var(--accent)',WAITING_PROVIDER:'#eab308',RETRYING:'#f97316',COMPLETED:'#22c55e',FAILED:'#ef4444',SKIPPED:'var(--text3)',CANCELLED:'var(--text3)'};
    st.innerHTML = agents.map(a => {
        const ic = icons[a.status]||'?';
        const co = cols[a.status]||'var(--text3)';
        const att = a.attempt_count>1 ? ' ('+a.attempt_count+'/'+a.max_attempts+')' : '';
        const step = a.current_step ? ' · '+a.current_step : '';
        return `<span style="color:${co};padding:3px 8px;border:1px solid ${co}33;border-radius:12px;font-size:11px;white-space:nowrap">${ic} ${a.agent_type}${att}${step}</span>`;
    }).join('');
}

// --- Cancel / Retry ---
async function cancelAiJob(jobId) {
    await fetch('/api/ai/jobs/'+jobId+'/cancel', {method:'POST'});
    showAiNotification('Analisis dibatalkan.', 'info');
    if (aiPollInterval) { clearInterval(aiPollInterval); aiPollInterval = null; }
    showAiProgressPanel(false);
    loadAiHistory();
}
async function retryFailedAgents(jobId) {
    await fetch('/api/ai/jobs/'+jobId+'/retry-failed', {method:'POST'});
    showAiNotification('Mencoba ulang agent gagal...', 'info');
    startAiProgressPolling(jobId);
}

// --- History ---
async function loadAiHistory() {
    const el = document.getElementById('ai-history-list');
    if (!el) return;
    try {
        const resp = await fetch('/api/ai/history');
        const items = await resp.json();
        if (!items.length) {
            el.innerHTML = '<div style="color:var(--text3);padding:8px;font-size:13px">Belum ada riwayat analisis.</div>';
            return;
        }
        let html = '';
        items.forEach(item => {
            const d = item.duration_ms ? (item.duration_ms/1000).toFixed(1)+'s' : '-';
            const conf = item.confidence_score!=null ? (item.confidence_score*100).toFixed(0)+'%' : '-';
            const q = item.data_quality_score!=null ? (item.data_quality_score*100).toFixed(0)+'%' : '-';
            const badges = {COMPLETED:'✓',FAILED:'✗',RUNNING:'●',PARTIAL:'◐',CANCELLED:'⊘',QUEUED:'○',RETRYING:'↻',PREPARING_DATA:'○',WAITING_PROVIDER:'⏳'};
            const badge = badges[item.status] || '?';
            const running = ['RUNNING','QUEUED','PREPARING_DATA','VALIDATING_DATA','RETRYING','WAITING_PROVIDER'].includes(item.status);
            const ac = item.agent_completed||0;
            const at = item.agent_total||0;
            const router = item.router_used || item.router || '-';
            const errCode = item.error_code ? '<code style="font-size:10px;color:#ef4444">'+item.error_code+'</code>' : '';
            const errMsg = item.error_message ? ' · '+item.error_message.substring(0,60) : '';
            const canRetry = item.status==='FAILED'||item.status==='PARTIAL';
            html += `<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);font-size:12px">
                <span style="font-size:16px;min-width:20px;text-align:center">${badge}</span>
                <div style="flex:1;min-width:0">
                    <div style="font-weight:600">${item.created_at ? new Date(item.created_at).toLocaleString('id-ID') : '-'} · ${(item.mode||'').toUpperCase()}</div>
                    <div style="color:var(--text3);font-size:11px">${item.status} · ${d} · Router: ${router} · Agent: ${ac}/${at}${errCode}${errMsg}</div>
                </div>
                ${running ? `<button onclick="startAiProgressPolling('${item.id}')" style="background:var(--accent);color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Lihat Progres</button>` : ''}
                ${canRetry ? `<button onclick="retryFailedAgents('${item.id}')" style="background:#f97316;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Coba Ulang</button>` : ''}
                ${item.status==='FAILED' && item.can_continue ? `<button onclick="startAiProgressPolling('${item.id}')" style="background:var(--accent);color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Lanjutkan</button>` : ''}
            </div>`;
        });
        el.innerHTML = html;
    } catch(e) {
        el.innerHTML = `<div style="color:#ef4444;padding:8px;font-size:13px">Gagal memuat riwayat: ${e.message} <button onclick="loadAiHistory()" style="background:var(--accent);color:#fff;border:none;padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px">Coba Lagi</button></div>`;
    }
}

// --- Display Result ---
function displayAiResult(job) {
    const scoresEl = document.getElementById('ai-scores');
    const resultsCard = document.getElementById('ai-results-card');
    if (scoresEl) scoresEl.style.display = 'grid';
    if (resultsCard) resultsCard.style.display = 'block';
    const q = document.getElementById('ai-quality-score');
    const c = document.getElementById('ai-confidence-score');
    const s = document.getElementById('ai-status-text');
    const d = document.getElementById('ai-duration');
    if (q) q.textContent = job.data_quality_score!=null ? (job.data_quality_score*100).toFixed(0)+'%' : '-';
    if (c) c.textContent = job.confidence_score!=null ? (job.confidence_score*100).toFixed(0)+'%' : '-';
    if (s) s.textContent = job.status || '-';
    if (d) d.textContent = job.duration_ms ? (job.duration_ms/1000).toFixed(1)+'s' : '-';
    showAiTab('summary');
}

// --- Tab Renderer ---
let _aiLastResult = null;
function showAiTab(tab) {
    document.querySelectorAll('.ai-tab').forEach(t => t.classList.remove('active'));
    const btn = document.querySelector(`.ai-tab[onclick*="'${tab}'"]`);
    if (btn) btn.classList.add('active');
    const el = document.getElementById('ai-tab-content');
    if (!el) return;
    // Try cached result first
    if (_aiLastResult) { renderAiTab(el, tab, _aiLastResult); return; }
    // Fetch latest job
    fetch('/api/ai/history').then(r=>r.json()).then(items => {
        if (!items.length) { el.innerHTML = '<div style="color:var(--text3);padding:20px;text-align:center">Tidak ada data analisis. Mulai analisis pertama Anda.</div>'; return; }
        const job = items[0];
        return fetch('/api/ai/history/' + job.id).then(r=>r.json());
    }).then(data => {
        if (!data) return;
        const result = typeof data.job.result === 'string' ? JSON.parse(data.job.result) : (data.job.result || {});
        const agents = data.agents || [];
        _aiLastResult = {result, agents};
        renderAiTab(el, tab, _aiLastResult);
    }).catch(() => { el.innerHTML = '<div style="color:var(--text3);padding:20px;text-align:center">Gagal memuat.</div>'; });
}
function renderAiTab(el, tab, ctx) {
    const {result, agents} = ctx;
    if (tab === 'agents') {
        if (!agents.length) { el.innerHTML = '<div style="color:var(--text3);padding:20px">Tidak ada data agent.</div>'; return; }
        el.innerHTML = agents.map(a => {
            const dur = a.duration_ms ? (a.duration_ms/1000).toFixed(1)+'s' : '-';
            const err = a.error_message ? `<div style="color:#ef4444;font-size:12px;margin-top:4px">❌ ${a.error_message}</div>` : '';
            const out = a.output ? `<div style="color:var(--text3);font-size:11px;margin-top:4px;max-height:200px;overflow:auto;white-space:pre-wrap;border-top:1px solid var(--border);padding-top:4px">${aiFormatText(typeof a.output === 'string' ? a.output.substring(0,500) : JSON.stringify(a.output).substring(0,500))}</div>` : '';
            return `<div style="padding:10px 0;border-bottom:1px solid var(--border);font-size:13px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <strong>${a.agent_type}</strong>
                    <span style="font-size:11px;color:var(--text3)">${a.status} · ${a.attempt_count||0}/${a.max_attempts||3} attempts · ${(a.provider_id||'-')}/${(a.model_id||'-')} · ${dur}</span>
                </div>${err}${out}
            </div>`;
        }).join('');
    } else {
        let content;
        if (tab === 'summary') {
            content = result.summary || result.final_summary || 'Ringkasan belum tersedia.';
        } else if (tab === 'data') {
            content = 'Data snapshot tersimpan di job. Klik tab Detail Agent untuk melihat output per-agent.';
        } else {
            content = result[tab] || result[tab+'_analysis'] || result[tab+'_assessment'] || null;
            if (!content && typeof result === 'object') {
                // Try to find matching key
                for (const k of Object.keys(result)) {
                    if (k.toLowerCase().includes(tab.toLowerCase())) { content = result[k]; break; }
                }
            }
        }
        el.innerHTML = `<div style="white-space:pre-wrap;font-size:13px;line-height:1.6">${content ? aiFormatText(content) : '<span style="color:var(--text3)">Bagian ini belum tersedia.</span>'}</div>`;
    }
}
function aiFormatText(t) {
    if (!t) return '';
    if (typeof t !== 'string') t = JSON.stringify(t, null, 2);
    return t.replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/#{1,3}\s*(.*)/g,'<h4 style="margin:12px 0 4px">$1</h4>').replace(/- (.*)/g,'• $1<br>');
}

// --- Notifications ---
function showAiNotification(msg, type) {
    const el = document.getElementById('ai-agent-status');
    if (!el) return;
    const colors = {success:'#22c55e',error:'#ef4444',warning:'#eab308',info:'var(--accent)'};
    const badge = document.createElement('div');
    badge.style.cssText = 'padding:6px 12px;border-radius:6px;font-size:12px;border:1px solid '+(colors[type]||colors.info)+';margin-bottom:4px';
    badge.textContent = msg;
    el.prepend(badge);
    setTimeout(() => badge.remove(), 8000);
}

// --- Init ---
function initAiAnalysis() {
    loadAiProviderStatus();
    loadAiHistory();
    // Resume any active job
    fetch('/api/ai/history').then(r=>r.json()).then(items => {
        const active = items.find(i => ['RUNNING','QUEUED','PREPARING_DATA','VALIDATING_DATA','RETRYING','WAITING_PROVIDER'].includes(i.status));
        if (active) startAiProgressPolling(active.id);
    }).catch(() => {});
}

function closeAiModal() {
    const m = document.getElementById('ai-modal');
    if (m) m.style.display = 'none';
}

// ============ NEW TABS: Kurs, Minyak, BI Rate, CPO, Alerts ============

async function loadKursData() {
    const data = await fetchData('kurs');
    if (!data || !data.data || data.data.length === 0) return;
    const latest = data.data[data.data.length - 1];
    // Tab section
    document.getElementById('kurs-date').textContent = latest.tanggal || '-';
    document.getElementById('kurs-usd').textContent = 'Rp ' + formatIDR(latest.usd_idr);
    document.getElementById('kurs-eur').textContent = 'Rp ' + formatIDR(latest.eur_idr);
    document.getElementById('kurs-sgd').textContent = 'Rp ' + formatIDR(latest.sgd_idr);
    document.getElementById('kurs-myr').textContent = 'Rp ' + formatIDR(latest.myr_idr);
    // Overview cards
    try {
        document.getElementById('overview-usd').textContent = 'Rp ' + formatIDR(latest.usd_idr);
        document.getElementById('overview-eur').textContent = 'Rp ' + formatIDR(latest.eur_idr);
        document.getElementById('overview-sgd').textContent = 'Rp ' + formatIDR(latest.sgd_idr);
    } catch(e) {}
    // Chart
    renderLineChart('kursChart', data.data, [
        {key: 'usd_idr', label: 'USD/IDR', color: '#4CAF50'},
        {key: 'eur_idr', label: 'EUR/IDR', color: '#2196F3'},
    ]);
}

async function loadMinyakData() {
    const data = await fetchData('minyak');
    if (!data || !data.data || data.data.length === 0) return;
    const latest = data.data[data.data.length - 1];
    // Tab section
    document.getElementById('minyak-date').textContent = latest.tanggal || '-';
    document.getElementById('minyak-brent').textContent = '$' + (latest.brent || '-');
    document.getElementById('minyak-wti').textContent = '$' + (latest.wti || '-');
    document.getElementById('minyak-selisih').textContent = '$' + (latest.selisih || '-');
    // Overview cards
    try {
        document.getElementById('overview-brent').textContent = '$' + (latest.brent || '-');
        document.getElementById('overview-wti').textContent = '$' + (latest.wti || '-');
    } catch(e) {}
    renderLineChart('minyakChart', data.data, [
        {key: 'brent', label: 'Brent', color: '#FF5722'},
        {key: 'wti', label: 'WTI', color: '#FF9800'},
    ]);
}

async function loadBIData() {
    const data = await fetchData('bi-rate');
    if (!data || !data.data || data.data.length === 0) return;
    const latest = data.data[data.data.length - 1];
    document.getElementById('bi-date').textContent = latest.tanggal || '-';
    document.getElementById('bi-rate-val').textContent = (latest.bi_rate || '-') + '%';
    document.getElementById('bi-mom').textContent = (latest.inflasi_mom || '-') + '%';
    document.getElementById('bi-yoy').textContent = (latest.inflasi_yoy || '-') + '%';
    document.getElementById('bi-ihk').textContent = latest.ihk ? latest.ihk.toLocaleString() : '-';
    renderLineChart('biChart', data.data, [
        {key: 'bi_rate', label: 'BI Rate', color: '#9C27B0'},
        {key: 'inflasi_yoy', label: 'Inflasi YoY', color: '#E91E63'},
    ]);
}

async function loadCPOData() {
    const data = await fetchData('cpo');
    if (!data || !data.data || data.data.length === 0) return;
    const latest = data.data[data.data.length - 1];
    document.getElementById('cpo-date').textContent = latest.tanggal || '-';
    document.getElementById('cpo-myr').textContent = 'MYR ' + (latest.harga_myr ? latest.harga_myr.toLocaleString() : '-');
    document.getElementById('cpo-idr').textContent = 'Rp ' + (latest.harga_idr ? latest.harga_idr.toLocaleString() : '-');
    const chg = latest.perubahan_persen;
    document.getElementById('cpo-chg').textContent = chg != null ? (chg >= 0 ? '+' : '') + chg + '%' : '-';
    renderLineChart('cpoChart', data.data, [
        {key: 'harga_myr', label: 'CPO (MYR/ton)', color: '#4CAF50'},
    ]);
}

async function loadAlertsData() {
    const data = await fetchData('alerts');
    if (!data || !data.alerts || data.alerts.length === 0) return;
    const container = document.getElementById('alerts-list');
    container.innerHTML = '';
    data.alerts.forEach(alert => {
        const div = document.createElement('div');
        div.className = 'alert-item';
        div.innerHTML = `<span class="alert-icon">${alert.icon || '🚨'}</span>
            <div class="alert-body"><strong>${alert.title || ''}</strong><br><small>${alert.message || ''}</small></div>
            <span class="alert-time">${alert.time || ''}</span>`;
        container.appendChild(div);
    });
}

// ============ Generic Line Chart Renderer ============

const chartInstances = {};
function renderLineChart(canvasId, dataArray, datasets) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || dataArray.length === 0) return;
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
    const isMobile = isMobileDevice();
    const labels = dataArray.map(d => d.tanggal ? formatDate(d.tanggal) : '');
    const lines = datasets.map(ds => ({
        label: ds.label,
        data: dataArray.map(d => d[ds.key]),
        borderColor: ds.color,
        backgroundColor: ds.color + '15',
        borderWidth: 2.5,
        pointRadius: dataArray.length > 30 ? 0 : 3,
        pointHoverRadius: 5,
        pointBackgroundColor: ds.color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: true,
        tension: 0.3
    }));
    chartInstances[canvasId] = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets: lines },
        options: getChartOptions(isMobile)
    });
}

// ============ Auto-Refresh Countdown ============

const REFRESH_INTERVAL = 300; // 5 minutes
let countdown = REFRESH_INTERVAL;

function updateCountdown() {
    const el = document.getElementById('refresh-countdown');
    if (!el) return;
    const m = Math.floor(countdown / 60);
    const s = countdown % 60;
    el.textContent = `🔄 ${m}:${s.toString().padStart(2,'0')}`;
    if (countdown <= 0) {
        countdown = REFRESH_INTERVAL;
        loadAllData();
    }
    countdown--;
}

setInterval(updateCountdown, 1000);// ============ Emas Data ============

