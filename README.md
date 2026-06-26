# 📊 Dashboard Monitoring Adi

Dashboard real-time untuk monitoring harga sembako, crypto, emas, pertanian, dan keuangan pribadi.

## 🚀 Quick Start

### Lokal (Development)
```bash
cd ~/sembako
pip install -r requirements.txt
python3 app.py
# Buka http://localhost:5000
```

### Production (VPS/Server)

#### 1. Install dependencies
```bash
sudo apt-get update
sudo apt-get install python3-pip nginx -y
cd ~/sembako
pip install -r requirements.txt
pip install gunicorn
```

#### 2. Setup Gunicorn + Systemd
```bash
# Copy service file
sudo cp dashboard.service /etc/systemd/system/

# Enable & start
sudo systemctl daemon-reload
sudo systemctl enable dashboard.service
sudo systemctl start dashboard.service
```

#### 3. Setup Nginx
```bash
# Copy nginx config
sudo cp nginx_dashboard.conf /etc/nginx/sites-available/dashboard
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/

# Test & reload
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Verify
```bash
curl http://localhost/api/health
curl http://localhost/
```

## 📊 API Endpoints

| Endpoint | Deskripsi |
|----------|-----------|
| `GET /` | Dashboard homepage |
| `GET /api/health` | Health check |
| `GET /api/sembako` | Harga sembako (16 item) |
| `GET /api/crypto` | Harga crypto |
| `GET /api/emas` | Harga emas (Antam, UBS, dll) |
| `GET /api/pertanian` | Harga pertanian & ternak |
| `GET /api/keuangan` | Transaksi keuangan |
| `GET /api/summary` | Status semua data |

## 📁 Struktur File

```
sembako/
├── app.py                      # Flask app
├── templates/
│   └── index.html             # Dashboard HTML
├── static/
│   ├── css/
│   │   ├── style.css          # Main styles
│   │   └── extras.css         # Badges, utilities
│   └── js/
│       └── script.js          # Dashboard JS + Charts
├── *.xlsx                     # Data files (Excel)
├── requirements.txt           # Python deps
├── nginx_dashboard.conf       # Nginx config
├── dashboard.service          # Systemd service
└── README.md                  # This file
```

## 🔄 Auto-Update via Cron

Dashboard akan auto-refresh setiap 30 detik. Data Excel diupdate otomatis oleh cron jobs:

- **08:00 WIB** — Harga Sembako
- **09:00 WIB** — Sentimen Berita
- **10:00 WIB** — Pertanian & Ternak
- **11:00 WIB** — Harga Emas
- **3x sehari** — Crypto (08:00, 12:00, 18:00, 22:00)
- **3x sehari** — Monitor BBM (07:00, 13:00, 19:00)

## 💻 Port & URLs

- **Development**: http://localhost:5000
- **Production** (Nginx): http://your-vps-ip (port 80)
- **API Health**: http://your-vps-ip/api/health

## 🛠️ Troubleshooting

### Port 5000 already in use
```bash
lsof -i :5000
kill -9 <PID>
```

### Nginx 502 Bad Gateway
```bash
sudo systemctl status dashboard
sudo journalctl -u dashboard -n 50
```

### Data not loading
```bash
curl http://localhost:5000/api/sembako
# Check if Excel files exist: ls ~/sembako/*.xlsx
```

## 📝 Notes

- Data disimpan dalam Excel format untuk mudah diakses
- Charts menggunakan Chart.js
- Responsive design (mobile-friendly)
- Auto-refresh setiap 30 detik
- No database required (file-based)

## 🚀 Deploy ke VPS

Untuk deploy ke VPS Adi (jika ada):

```bash
# 1. Upload semua file ke VPS
scp -r ~/sembako user@your-vps:~/

# 2. SSH ke VPS dan jalankan setup
ssh user@your-vps
cd ~/sembako
sudo bash -c 'pip install -r requirements.txt && \
  cp dashboard.service /etc/systemd/system/ && \
  systemctl enable dashboard && \
  systemctl start dashboard'

# 3. Setup Nginx
sudo cp nginx_dashboard.conf /etc/nginx/sites-available/dashboard
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

---

**Created by adioranye for Adi** 📊
