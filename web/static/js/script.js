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
    document.getElementById(tabName).classList.add('active');
    
    // Mark button as active
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
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
    // Auto-fetch AI analysis & populate Summary + Recommendations
    fetchAiAnalysis();
}

// ============ Format Functions ============
function formatCurrency(value) {
    if (!value) return '-';
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatIDR(value) {
    if (!value) return '-';
    return new Intl.NumberFormat('id-ID').format(Math.round(value));
}

function formatUSD(value) {
    if (!value) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value) {
    if (!value) return '-';
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
    
    // Update overview cards
    document.getElementById('sembako-date').textContent = response.last_update || formatDate(latest.tanggal);
    document.getElementById('mini-beras').textContent = formatCurrency(latest.beras_premium);
    document.getElementById('mini-cabai').textContent = formatCurrency(latest.cabai_merah);
    document.getElementById('mini-tepung').textContent = formatCurrency(latest.tepung_terigu);
    
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
    
    // Update overview cards - Sentimen (no market cap)
    document.getElementById('crypto-mcap').textContent = latest.sentimen || 'NETRAL';
    document.getElementById('mini-btc').textContent = formatUSD(latest.btc_usd);
    document.getElementById('mini-eth').textContent = formatUSD(latest.eth_usd);
    document.getElementById('mini-sol').textContent = formatUSD(latest.sol_usd);
    
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
    
    // Update overview cards
    document.getElementById('emas-price').textContent = formatCurrency(latest.antam_beli);
    document.getElementById('mini-emas-beli').textContent = formatCurrency(latest.antam_beli);
    document.getElementById('mini-emas-back').textContent = formatCurrency(latest.antam_buyback);
    document.getElementById('mini-spread').textContent = formatCurrency(latest.selisih);
    
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
    renderPeternakanTable('all');
    
    // Setup filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderPeternakanTable(e.target.dataset.filter);
        });
    });
}

function renderPeternakanTable(filter) {
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
    const latest = data[data.length - 1];

    // Update last update
    document.getElementById('pakan-update').textContent = response.last_update || formatDate(latest.tanggal);

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
            <td>${row.headline.substring(0, 70)}...</td>
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
function getChartOptions(isMobile) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    boxWidth: isMobile ? 10 : 12,
                    padding: isMobile ? 8 : 15,
                    font: {
                        size: isMobile ? 10 : 12
                    }
                }
            },
            tooltip: {
                enabled: true,
                titleFont: {
                    size: isMobile ? 11 : 13
                },
                bodyFont: {
                    size: isMobile ? 10 : 12
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)' },
                ticks: {
                    font: {
                        size: isMobile ? 9 : 11
                    },
                    maxTicksLimit: isMobile ? 5 : 8
                }
            },
            x: {
                grid: { display: false },
                ticks: {
                    font: {
                        size: isMobile ? 9 : 11
                    },
                    maxRotation: isMobile ? 45 : 0
                }
            }
        }
    };
}

function isMobileDevice() {
    return window.innerWidth < 768;
}

function updateCryptoChart(data) {
    const labels = data.map(d => formatDate(d.tanggal));
    const btcChanges = data.map(d => d.btc_24h || 0);
    const ethChanges = data.map(d => d.eth_24h || 0);
    const solChanges = data.map(d => d.sol_24h || 0);
    
    const ctx = document.getElementById('cryptoChart');
    if (!ctx) return;
    
    if (cryptoChart) cryptoChart.destroy();
    
    const isMobile = isMobileDevice();
    
    cryptoChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'BTC 24h %',
                    data: btcChanges,
                    borderColor: '#f7931a',
                    backgroundColor: 'rgba(247, 147, 26, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: 'ETH 24h %',
                    data: ethChanges,
                    borderColor: '#627eea',
                    backgroundColor: 'rgba(98, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: 'SOL 24h %',
                    data: solChanges,
                    borderColor: '#14f195',
                    backgroundColor: 'rgba(20, 241, 149, 0.1)',
                    tension: 0.4,
                    fill: true,
                }
            ]
        },
        options: getChartOptions(isMobile)
    });
}

function updateEmasChart(data) {
    const labels = data.map(d => formatDate(d.tanggal));
    const antamBeli = data.map(d => d.antam_beli || 0);
    const antamBuyback = data.map(d => d.antam_buyback || 0);
    const ubs = data.map(d => d.ubs_beli || 0);
    
    const ctx = document.getElementById('emasChart');
    if (!ctx) return;
    
    if (emasChart) emasChart.destroy();
    
    const isMobile = isMobileDevice();
    
    emasChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Antam Beli',
                    data: antamBeli,
                    borderColor: '#ffd700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: 'Antam Buyback',
                    data: antamBuyback,
                    borderColor: '#daa520',
                    backgroundColor: 'rgba(218, 165, 32, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: 'UBS Beli',
                    data: ubs,
                    borderColor: '#c0a060',
                    backgroundColor: 'rgba(192, 160, 96, 0.1)',
                    tension: 0.4,
                    fill: true,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: isMobile ? 10 : 12,
                        padding: isMobile ? 8 : 15,
                        font: {
                            size: isMobile ? 10 : 12
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    titleFont: {
                        size: isMobile ? 11 : 13
                    },
                    bodyFont: {
                        size: isMobile ? 10 : 12
                    },
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += 'Rp ' + context.parsed.y.toLocaleString('id-ID');
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: {
                        font: {
                            size: isMobile ? 9 : 11
                        },
                        maxTicksLimit: isMobile ? 5 : 8,
                        callback: function(value) {
                            return 'Rp ' + (value / 1000000).toFixed(0) + 'M';
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: {
                            size: isMobile ? 9 : 11
                        },
                        maxRotation: isMobile ? 45 : 0
                    }
                }
            }
        }
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

    document.getElementById('ihsg-value').textContent = latest.ihsg ? latest.ihsg.toLocaleString('id-ID') : '-';
    document.getElementById('ihsg-change').textContent = latest.change_pct ? (latest.change_pct > 0 ? '+' : '') + latest.change_pct + '%' : '-';
    document.getElementById('ihsg-change').className = 'metric-change ' + (latest.change_pct > 0 ? 'positive' : 'negative');
    document.getElementById('ihsg-high').textContent = latest.high ? latest.high.toLocaleString('id-ID') : '-';
    document.getElementById('ihsg-low').textContent = latest.low ? latest.low.toLocaleString('id-ID') : '-';
}

function renderSektorList() {
    const container = document.getElementById('sektor-list');
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

// ============ AI Analysis (Groq) ============
let aiAnalysisCache = null;
let aiAnalysisTime = null;

async function openAiAnalysis() {
    const content = document.getElementById('ai-analysis-content');
    const loading = '<div class="loading">🤖 Mengambil analisis dari Groq AI...</div>';
    content.innerHTML = loading;

    try {
        const response = await fetch('/api/ai-analysis');
        const data = await response.json();

        if (data.status === 'success') {
            // Format the analysis text
            let formatted = data.analysis;
            formatted = formatted.replace(/\n/g, '<br>');
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/#{1,3}\s*(.*)/g, '<h4>$1</h4>');
            formatted = formatted.replace(/- (.*)/g, '• $1<br>');

            content.innerHTML = `
                <div class="ai-analysis-box">
                    <div class="ai-meta">
                        <span class="ai-badge">🤖 Groq Llama 3.1 8B</span>
                        <span class="ai-time">${data.timestamp}</span>
                    </div>
                    <div class="ai-text">${formatted}</div>
                </div>
            `;

            aiAnalysisCache = data.analysis;
            aiAnalysisTime = data.timestamp;

            // Update summary items
            updateAISummary();
        } else {
            content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
        }
    } catch (e) {
        content.innerHTML = `<div class="error">Gagal mengambil data: ${e.message}</div>`;
    }
}

async function refreshAiAnalysis() {
    openAiAnalysis();
}

function updateAISummary() {
    // IHSG
    const ihsgEl = document.getElementById('ai-ihsg');
    if (sahamData.ihsg && sahamData.ihsg.length > 0) {
        const latest = sahamData.ihsg[sahamData.ihsg.length - 1];
        ihsgEl.textContent = latest.ihsg ? Number(latest.ihsg).toLocaleString() : '-';
    }

    // BTC
    const btcEl = document.getElementById('ai-btc');
    if (cryptoData && cryptoData.data && cryptoData.data.length) {
        const cv = cryptoData.data[cryptoData.data.length - 1];
        if (cv.btc_usd) btcEl.textContent = '$' + Number(cv.btc_usd).toLocaleString(undefined, {maximumFractionDigits: 0});
    }

    // Emas
    const emasEl = document.getElementById('ai-emas');
    if (emasData && emasData.data && emasData.data.length) {
        const ev = emasData.data[emasData.data.length - 1];
        if (ev.antam_beli) emasEl.textContent = 'Rp' + Number(ev.antam_beli).toLocaleString();
    }

    // Top Mover — find biggest % change from sembako
    const moverEl = document.getElementById('ai-top-mover');
    if (sembakoData && sembakoData.data && sembakoData.data.length > 1) {
        const rows = sembakoData.data;
        if (rows.length >= 2) {
            const curr = rows[rows.length - 1];
            const prev = rows[rows.length - 2];
            let topName = '-', topChg = 0;
            const keys = Object.keys(curr).filter(k => k !== 'Tanggal' && prev[k] && curr[k]);
            for (const k of keys) {
                const c = Number(curr[k]), p = Number(prev[k]);
                if (p > 0) {
                    const chg = ((c - p) / p) * 100;
                    if (Math.abs(chg) > Math.abs(topChg)) { topChg = chg; topName = k.replace(/_/g, ' '); }
                }
            }
            moverEl.textContent = topName + (topChg !== 0 ? ' ' + (topChg > 0 ? '↑' : '↓') + Math.abs(topChg).toFixed(1) + '%' : '');
        }
    }

    // Extract recommendations from analysis markdown
    if (aiAnalysisCache) {
        const recEl = document.getElementById('ai-recommendations');
        const sections = aiAnalysisCache.split(/\n/);
        let inRec = false;
        let recLines = [];
        for (const line of sections) {
            if (/💡\s*Rekomendasi/.test(line)) { inRec = true; continue; }
            if (/^##/.test(line) && inRec) break; // next section
            if (inRec && line.trim()) recLines.push(line);
        }
        if (recLines.length > 0) {
            recEl.innerHTML = recLines.map(l => {
                const bold = l.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                const bullet = bold.replace(/^[-•]\s*/, '• ');
                return bullet.startsWith('  ') ? '<div style="padding-left:1rem;color:#888;font-size:0.85em">' + bullet.trim() + '</div>' : '<div style="margin-bottom:0.4em">' + bullet + '</div>';
            }).join('');
        }
    }
}

function closeAiModal() {
    document.getElementById('ai-modal').style.display = 'none';
}

// ============ NEW TABS: Kurs, Minyak, BI Rate, CPO, Alerts ============

async function loadKursData() {
    const data = await fetchData('kurs');
    if (!data || !data.data || data.data.length === 0) return;
    const latest = data.data[data.data.length - 1];
    document.getElementById('kurs-date').textContent = latest.tanggal || '-';
    document.getElementById('kurs-usd').textContent = 'Rp ' + formatIDR(latest.usd_idr);
    document.getElementById('kurs-eur').textContent = 'Rp ' + formatIDR(latest.eur_idr);
    document.getElementById('kurs-sgd').textContent = 'Rp ' + formatIDR(latest.sgd_idr);
    document.getElementById('kurs-myr').textContent = 'Rp ' + formatIDR(latest.myr_idr);
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
    document.getElementById('minyak-date').textContent = latest.tanggal || '-';
    document.getElementById('minyak-brent').textContent = '$' + (latest.brent || '-');
    document.getElementById('minyak-wti').textContent = '$' + (latest.wti || '-');
    document.getElementById('minyak-selisih').textContent = '$' + (latest.selisih || '-');
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
    // Destroy old instance
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    const labels = dataArray.map(d => d.tanggal ? d.tanggal.slice(5) : ''); // MM-DD
    const lines = datasets.map(ds => ({
        label: ds.label,
        data: dataArray.map(d => d[ds.key]),
        borderColor: ds.color,
        backgroundColor: ds.color + '20',
        fill: true,
        tension: 0.3,
        pointRadius: dataArray.length > 30 ? 0 : 3,
    }));
    chartInstances[canvasId] = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets: lines },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8', maxTicksLimit: 10 }, grid: { color: '#1e293b' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } }
            }
        }
    });
}

// ============ Dark Mode ============

function toggleDarkMode() {
    document.body.classList.toggle('light-mode');
    const isLight = document.body.classList.contains('light-mode');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    document.getElementById('dark-toggle').textContent = isLight ? '☀️' : '🌙';
}

// Load saved theme
(function() {
    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
        document.body.classList.add('light-mode');
        setTimeout(() => { const btn = document.getElementById('dark-toggle'); if(btn) btn.textContent = '☀️'; }, 100);
    }
})();

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

