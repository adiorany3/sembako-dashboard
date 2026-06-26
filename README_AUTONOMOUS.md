# 🌐 Autonomous Dashboard System

## Sistem berjalan sendiri tanpa bergantung ke Hermes Agent

---

## 📋 Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub                                │
│              (adiorany3/sembako-dashboard)                   │
│                                                             │
│   ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│   │ app.py  │  │ templates│  │  scripts  │  │  data    │  │
│   └────┬────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘  │
└────────┼────────────┼──────────────┼──────────────┼────────┘
         │            │              │              │
         │  git push  │              │              │
         │    ↓       │              │              │
    ┌────┴────────────┴──────────────┴──────────────┴────┐
    │                        VPS                            │
    │                                                      │
    │   ┌─────────────────────────────────────────────┐   │
    │   │  Cron: git pull origin main (setiap jam)    │   │
    │   └─────────────────────────────────────────────┘   │
    │                         ↓                           │
    │   ┌─────────────────────────────────────────────┐   │
    │   │  Cron: update data (7AM, 12PM, 6PM)         │   │
    │   │  • update_harga.py                          │   │
    │   │  • update_crypto.py                         │   │
    │   │  • update_emas.py                          │   │
    │   └─────────────────────────────────────────────┘   │
    │                         ↓                           │
    │   ┌─────────────────────────────────────────────┐   │
    │   │  Flask Dashboard (port 5000)                │   │
    │   │  • http://43.153.196.161:5000/             │   │
    │   │  • http://43.153.196.161:5000/keuangan     │   │
    │   └─────────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (VPS Baru)

```bash
# 1. Clone repo
cd ~
git clone https://github.com/adiorany3/sembako-dashboard.git
cd sebaikko-dashboard

# 2. Run setup
chmod +x autonomous_setup.sh
./autonomous_setup.sh

# 3. Cek status
sudo systemctl status flask
crontab -l
```

---

## 🔄 Cara Kerja Auto-Update

### 1. Update Kode (Hermes Agent)
```
Hermes Agent → push ke GitHub → selesai
```
- Kamu minta aku update kode
- Aku push ke GitHub (token一次性, sekali aja)
- Tidak perlu action lain

### 2. Update Kode (Tanpa Hermes)
```
GitHub → git pull → Flask restart otomatis
```
- Buka https://github.com/adiorany3/sembako-dashboard
- Edit file langsung di GitHub, atau
- Push dari komputer lain (butuh token 1x untuk setup)

### 3. Update Data (Otomatis)
```
Cron jobs → jalankan script → update Excel files
```
- Setiap jam: `git pull` dari GitHub
- Setiap 7AM, 12PM, 6PM: update data dari web

---

## 📂 Struktur File

```
sembako-dashboard/
├── app.py                    # Flask backend
├── templates/
│   ├── index.html            # Dashboard utama
│   └── keuangan.html         # Halaman keuangan (private)
├── static/
│   ├── css/style.css         # Styling
│   ├── js/script.js          # JavaScript
│   └── favicon.svg           # Favicon
├── scripts/
│   ├── update_harga.py       # Update harga Sembako
│   ├── update_crypto.py      # Update crypto prices
│   ├── update_emas.py        # Update harga emas
│   ├── sentimen_berita.py    # Analisis sentimen berita
│   └── monitor_bbm.py        # Monitor BBM
├── data/
│   ├── harga_sembako.xlsx    # Data Sembako
│   ├── crypto_monitor.xlsx   # Data Crypto
│   ├── harga_emas.xlsx       # Data Emas
│   └── keuangan.xlsx         # Data Keuangan
├── pull_from_github.sh       # Script auto-pull
├── run_updates.sh            # Script update data
├── autonomous_setup.sh       # Setup script
└── README.md
```

---

## ⏰ Cron Jobs

| Cron | Command | Fungsi |
|------|---------|--------|
| `0 * * * *` | `pull_from_github.sh` | Pull update dari GitHub setiap jam |
| `0 7,12,18 * * *` | `run_updates.sh` | Update data 3x sehari |
| `@reboot` | `systemctl start flask` | Auto-start Flask saat boot |

---

## 🔧 Maintenance

### Manual Update dari GitHub
```bash
cd ~/sembako
git pull origin main
sudo systemctl restart flask
```

### Cek Status
```bash
# Flask
sudo systemctl status flask

# Cron jobs
crontab -l

# Logs
tail -f ~/sembako/flask.log
tail -f ~/sembako/pull.log
tail -f ~/sembako/update.log
```

### Restart Manual
```bash
cd ~/sembako
sudo systemctl restart flask
```

---

## 🔐 Keamanan

- **Keuangan tab**: Tidak muncul di navigasi, hanya bisa diakses via `/keuangan`
- **Flask service**: Jalan sebagai user `ubuntu` (bukan root)
- **Auto-restart**: Flask akan restart otomatis jika crash

---

## 📡 Endpoints

| URL | Description |
|-----|-------------|
| `http://43.153.196.161:5000/` | Dashboard utama |
| `http://43.153.196.161:5000/keuangan` | Halaman Keuangan |
| `http://43.153.196.161:5000/api/sembako` | API Sembako |
| `http://43.153.196.161:5000/api/crypto` | API Crypto |
| `http://43.153.196.161:5000/api/emas` | API Emas |
| `http://43.153.196.161:5000/api/pertanian` | API Pertanian |
| `http://43.153.196.161:5000/api/keuangan` | API Keuangan |
| `http://43.153.196.161:5000/api/health` | Health check |

---

## 🛠 Troubleshooting

### Flask tidak jalan
```bash
sudo systemctl status flask
journalctl -u flask -n 50
```

### Cron tidak jalan
```bash
sudo service cron status
grep CRON /var/log/syslog | tail -10
```

### Git pull gagal
```bash
cd ~/sembako
git pull origin main
# Jika error, check token di .git/config
```

---

## 📌 Catatan

- **Token GitHub**: Hanya perlu untuk initial setup atau push manual
- **Data**: Update otomatis 3x sehari (7AM, 12PM, 6PM)
- **Kode**: Update otomatis setiap jam dari GitHub
- **Boot**: Flask auto-start saat VPS menyala
