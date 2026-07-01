# 📊 Dashboard Monitoring Sembako

Dashboard real-time untuk monitoring harga sembako, crypto, emas, pertanian, peternakan, saham, dan keuangan.

## 🚀 Quick Start

### Local Development
```bash
cd ~/sembako
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your API keys
python3 core/app.py
# Buka http://localhost:5000
```

### VPS Production
```bash
cd ~/sembako
pip3 install -r requirements.txt --break-system-packages

# Start with systemd
sudo cp dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flask
sudo systemctl restart flask
```

## 📊 API Endpoints

| Endpoint | Deskripsi | Meta |
|----------|-----------|------|
| `GET /` | Dashboard homepage | - |
| `GET /api/health` | Health check | status, uptime |
| `GET /api/summary` | Status semua data | status, last_update |
| `GET /api/sembako` | Harga sembako (16 item) | source, status |
| `GET /api/crypto` | Harga crypto (BTC, ETH, SOL) | source, status |
| `GET /api/emas` | Harga emas (Antam, UBS) | source, status |
| `GET /api/pertanian` | Harga pertanian & ternak | source, status |
| `GET /api/peternakan` | Data peternakan lengkap | source, status |
| `GET /api/saham` | Harga saham & IHSG | source, status |
| `GET /api/kurs` | Kurs valuta asing | source, status |
| `GET /api/minyak` | Harga minyak mentah | source, status |
| `GET /api/bi-rate` | BI Rate & inflasi | source, status |
| `GET /api/cpo` | Harga CPO | source, status |
| `GET /api/sentimen` | Sentimen berita | source, status |
| `GET /api/alerts` | Price alerts | source, status |
| `GET /api/ai-analysis` | AI market analysis (Groq) | source, status |

### API Response Format

Every endpoint returns JSON with `data` and `meta`:
```json
{
  "data": [...],
  "meta": {
    "status": "valid | stale | failed | estimated",
    "source": "detik.com",
    "source_url": "https://...",
    "last_success_at": "2026-07-01T08:00:00+07:00",
    "last_attempt_at": "2026-07-01T08:05:00+07:00",
    "row_count": 33,
    "validation_errors": []
  }
}
```

## 📁 Struktur File

```
sembako/
├── core/
│   ├── app.py                    # Flask application
│   └── config.py                 # API keys (NOT in git)
├── utils/
│   ├── config.py                 # Central config, paths, constants
│   ├── excel_store.py            # Excel read/write with metadata
│   ├── validation.py             # Data validation rules
│   ├── dedup.py                  # Deduplication engine
│   └── logging_setup.py          # Standard logging setup
├── scripts/
│   ├── update_harga.py           # Sembako prices (detik.com)
│   ├── update_crypto.py          # Crypto prices (CoinGecko)
│   ├── update_emas.py            # Gold prices (Antam)
│   ├── update_pertanian.py       # Agriculture prices
│   ├── update_peternakan.py      # Livestock prices
│   ├── update_pakan_nutrisi.py   # Feed & nutrition
│   ├── update_saham.py           # Stock prices
│   ├── update_kurs.py            # Currency rates
│   ├── update_oil.py             # Oil prices
│   ├── update_bi_rate.py         # BI Rate & inflation
│   ├── update_cpo.py             # CPO prices
│   ├── sentimen_berita.py        # News sentiment
│   ├── monitor_bbm.py            # BBM price monitor
│   ├── master_update.py          # Master update script
│   ├── dedup_excel.py            # CLI dedup tool
│   ├── validate_data.py          # Data validation tool
│   ├── run_all_updates.sh        # Run all scrapers
│   └── precompute_analysis.py    # Groq AI analysis
├── data/
│   ├── harga_sembako.xlsx
│   ├── crypto_monitor.xlsx
│   ├── harga_emas.xlsx
│   ├── harga_pertanian_ternak.xlsx
│   ├── harga_peternakan_lengkap.xlsx
│   ├── harga_saham_ihsg.xlsx
│   ├── kurs_valuta.xlsx
│   ├── harga_minyak.xlsx
│   ├── bi_rate_inflasi.xlsx
│   ├── harga_cpo.xlsx
│   ├── sentimen_berita.xlsx
│   ├── harga_pakan_ternak.xlsx
│   └── cuaca_yogyakarta.xlsx
├── web/
│   ├── templates/
│   │   ├── index.html            # Dashboard HTML
│   │   └── keuangan.html         # Private finance
│   └── static/
│       ├── favicon.svg
│       ├── css/style.css
│       ├── css/extras.css
│       └── js/script.js
├── tests/
│   ├── test_app_health.py
│   ├── test_validation.py
│   └── test_dedup.py
├── logs/
├── requirements.txt
├── .env.example
├── .gitignore
├── dashboard.service             # Systemd service
├── nginx_dashboard.conf          # Nginx config
└── README.md
```

## 🔄 Data Update Pipeline

### Run all updates
```bash
bash scripts/run_all_updates.sh
```

### Run specific scraper
```bash
python3 scripts/update_harga.py
python3 scripts/update_crypto.py
python3 scripts/update_emas.py
```

### Deduplicate data
```bash
python3 scripts/dedup_excel.py --dry-run  # Preview
python3 scripts/dedup_excel.py            # Execute
```

### Validate data
```bash
python3 scripts/validate_data.py
```

## ⏰ Cron Schedule

| Schedule | Script | Dataset |
|----------|--------|---------|
| `0 8 * * *` | update_harga.py | Sembako |
| `0 9 * * *` | sentimen_berita.py | Sentimen |
| `0 10 * * *` | update_pertanian.py | Pertanian |
| `0 10 * * *` | update_peternakan.py | Peternakan |
| `0 11 * * *` | update_emas.py | Emas |
| `0 8,12,18,22 * * *` | update_crypto.py | Crypto |
| `0 7,13,19 * * *` | monitor_bbm.py | BBM |
| `0 8 * * *` | update_saham.py | Saham |
| `0 8 * * *` | update_kurs.py | Kurs |
| `0 8 * * *` | update_oil.py | Minyak |
| `0 8 * * *` | update_bi_rate.py | BI Rate |
| `0 8 * * *` | update_cpo.py | CPO |
| `0 */8 * * *` | precompute_analysis.py | AI Analysis |

## 🧪 Testing

```bash
# Run all tests
pytest -q

# With coverage
pytest --cov=utils --cov=core

# Manual acceptance
python3 core/app.py
curl http://localhost:5000/api/health
curl http://localhost:5000/api/summary
```

## 🔒 Security

- API keys stored in `.env` (never committed)
- Private data (`/keuangan`) has no nav link
- `.gitignore` excludes `.env`, `logs/`, `__pycache__/`

## 🛠️ Troubleshooting

### Flask down
```bash
sudo systemctl restart flask
# or
cd ~/sembako/core && python3 app.py &
```

### Data stale/missing
```bash
# Check last update
curl http://localhost:5000/api/summary

# Force update
bash scripts/run_all_updates.sh

# Dedup after update
python3 scripts/dedup_excel.py
```

### Port conflict
```bash
lsof -i :5000
kill -9 <PID>
```

---

**Created by adioranye** 📊
