// Dashboard JavaScript
// Part 1: Setup, Tab Navigation, and API Functions

const API_BASE = '/api';
let cryptoChart, emasChart;

// ============ Initialize ============
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
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
        checkHealth()
    ]);
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
    const latest = data[data.length - 1];
    
    // Update overview cards
    document.getElementById('sembako-date').textContent = response.last_update || formatDate(latest.tanggal);
    document.getElementById('mini-beras').textContent = formatCurrency(latest.beras_premium);
    document.getElementById('mini-telur').textContent = formatCurrency(latest.telur_ras);
    document.getElementById('mini-ayam').textContent = formatCurrency(latest.ayam_ras);
    
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
    const latest = data[data.length - 1];
    
    // Update overview cards
    document.getElementById('crypto-mcap').textContent = latest.market_cap ? 
        '$' + (latest.market_cap / 1e12).toFixed(2) + 'T' : '-';
    document.getElementById('mini-btc').textContent = formatUSD(latest.btc_usd);
    document.getElementById('mini-eth').textContent = formatUSD(latest.eth_usd);
    document.getElementById('mini-sol').textContent = formatUSD(latest.sol_usd);
    
    // Fill table
    const tbody = document.getElementById('crypto-tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        const btc24hClass = row.btc_24h < 0 ? 'text-danger' : 'text-success';
        tr.innerHTML = `
            <td>${formatDate(row.tanggal)}</td>
            <td>${formatUSD(row.btc_usd)}</td>
            <td>${formatCurrency(row.btc_idr)}</td>
            <td class="${btc24hClass}">${formatPercent(row.btc_24h)}</td>
            <td>${formatUSD(row.eth_usd)}</td>
            <td>${formatCurrency(row.eth_idr)}</td>
            <td>${formatUSD(row.sol_usd)}</td>
            <td>${row.market_cap ? '$' + (row.market_cap / 1e12).toFixed(2) + 'T' : '-'}</td>
            <td><span class="badge">${row.sentimen || 'NETRAL'}</span></td>
        `;
        tbody.appendChild(tr);
    });
    
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
    document.getElementById('mini-spread').textContent = formatPercent(latest.spread_persen);
    
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
