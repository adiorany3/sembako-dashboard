# PRD — Migrasi, Backup, dan Pemulihan Server Hermes

**Nama dokumen:** HERMES_SERVER_PRD.md
**Sistem:** Hermes + Sembako Dashboard
**Repositori utama:** adiorany3/sembako-dashboard
**Status:** Ready to implement
**Pemilik sistem:** Adi

## 1. Instruksi Wajib untuk Hermes

Saat Hermes berjalan pada VPS baru atau sesi baru, Hermes wajib melakukan hal berikut sebelum mengubah sistem:

1. **Baca dokumen ini sampai selesai.**
2. Anggap repositori Git sebagai sumber utama kode, dokumentasi, dan konfigurasi non-rahasia.
3. Anggap paket backup terenkripsi sebagai sumber utama state Hermes, data operasional, dan konfigurasi rahasia.
4. **Jangan membuat struktur server baru** sebelum memeriksa backup-manifest.json.
5. **Jangan menimpa data lama** sebelum membuat salinan rollback.
6. **Jangan menyimpan token, API key, kata sandi, private key, atau cookie** ke repositori Git.
7. Gunakan satu jalur aplikasi, satu nama service, dan satu mekanisme scheduler sesuai dokumen ini.
8. Setelah pemulihan, jalankan seluruh acceptance test pada Bab 15.
9. Catat setiap perubahan penting pada CHANGELOG_HERMES.md.
10. Jika terdapat konflik antara konfigurasi VPS lama dan dokumen ini, utamakan konfigurasi target pada dokumen ini, lalu dokumentasikan penyesuaiannya.

## 2. Latar Belakang

Hermes dan dashboard saat ini memiliki beberapa komponen:
- konfigurasi, cache, skill, dan state Hermes;
- aplikasi Flask pada repositori Sembako Dashboard;
- file data Excel, JSON, dan TXT;
- script pembaruan data;
- service aplikasi;
- scheduler untuk pembaruan data dan deployment;
- reverse proxy Nginx;
- API key dan konfigurasi rahasia;
- log operasional.

Sistem saat ini perlu dibuat portabel karena VPS dapat habis masa berlaku. VPS baru harus dapat dipulihkan hanya dengan:
- akses ke repositori Git;
- satu paket backup terakhir;
- kredensial rahasia yang disimpan di lokasi aman;
- dokumen ini.

## 4. Tujuan

### 4.1 Tujuan Utama

VPS baru harus dapat menjalankan Hermes dan Sembako Dashboard secara utuh dengan proses pemulihan yang:
- terdokumentasi;
- dapat diulang;
- aman;
- tidak bergantung pada IP lama;
- tidak bergantung pada username lama;
- tidak bergantung pada proses manual yang tidak tercatat;
- dapat diverifikasi melalui health check;
- mempunyai mekanisme rollback.

### 4.2 Target Awal

| Metric | Target |
|--------|--------|
| RTO | Maksimal 60 menit untuk VPS bersih |
| RPO state Hermes | Maksimal kehilangan perubahan 24 jam |
| RPO data dashboard | Maksimal kehilangan data 6 jam |
| Keberhasilan restore test | 100% untuk seluruh acceptance test kritis |
| Ketergantungan pada VPS lama setelah cutover | 0 |

## 6. Arsitektur Target

```
Git Repository
├── source code
├── web templates/static
├── scripts
├── deployment files
├── requirements.txt
├── .env.example
├── HERMES_SERVER_PRD.md
└── CHANGELOG_HERMES.md

Encrypted Offsite Backup
├── hermes-state.tar.zst.age
├── dashboard-data.tar.zst.age
├── server-config.tar.zst.age
├── backup-manifest.json
└── SHA256SUMS

VPS Baru
├── /opt/hermes/sembako-dashboard
├── /var/lib/hermes-dashboard/data
├── /var/lib/hermes-dashboard/cache
├── /var/log/hermes-dashboard
├── /etc/hermes-dashboard/hermes-dashboard.env
├── /etc/systemd/system/hermes-dashboard.service
├── /etc/systemd/system/hermes-update.service
├── /etc/systemd/system/hermes-update.timer
└── /etc/nginx/sites-available/hermes-dashboard
```

### 6.1 User Sistem

- User: `hermes`
- Group: `hermes`
- Shell: `/bin/bash`
- Home: `/home/hermes`

**Aplikasi tidak boleh berjalan sebagai root.**

### 6.2 Path Standar

| Kebutuhan | Path |
|-----------|------|
| Kode aplikasi | /opt/hermes/sembako-dashboard |
| Data aktif | /var/lib/hermes-dashboard/data |
| Cache aplikasi | /var/lib/hermes-dashboard/cache |
| State Hermes | /home/hermes/.hermes |
| Environment rahasia | /etc/hermes-dashboard/hermes-dashboard.env |
| Log | /var/log/hermes-dashboard |
| Backup sementara | /var/backups/hermes-dashboard |

## 7. Sumber Kebenaran

### 7.1 Repositori Git
Kode aplikasi, HTML/CSS/JS, script, systemd unit template, Nginx template, requirements, script backup/restore, dokumentasi.

### 7.2 Backup Terenkripsi
`/home/hermes/.hermes`, data Excel/JSON/TXT, konfigurasi rahasia, state publisher, cache, konfigurasi Nginx & systemd aktif.

### 7.3 Secret Manager
Rahasia disimpan di luar repositori (password manager, encrypted archive, private object storage).

**Rahasia yang harus didokumentasikan (bukan nilainya):**
- GROQ_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- WORDPRESS_EMAIL
- WORDPRESS_APP_PASSWORD
- GITHUB_DEPLOY_TOKEN
- BACKUP_ENCRYPTION_RECIPIENT

## 8. Perubahan Teknis yang Wajib Dilakukan

| ID | Deskripsi |
|----|-----------|
| FR-01 | Hilangkan hardcoded path — gunakan environment variable |
| FR-02 | Satu entrypoint: `/opt/hermes/sembako-dashboard/core/app.py` via Gunicorn |
| FR-03 | Satu service: `hermes-dashboard.service` |
| FR-04 | Satu scheduler: systemd timer (bukan cron) |
| FR-05 | Dependency lock dengan requirements.txt dan venv |
| FR-06 | Konfigurasi rahasia di `/etc/hermes-dashboard/hermes-dashboard.env` |
| FR-07 | Nginx meneruskan ke 127.0.0.1:5000 |
| FR-08 | Health check di `/api/health` |
| FR-09 | Logging ke journald dan `/var/log/hermes-dashboard` |
| FR-10 | Backup offsite terenkripsi |
| FR-11 | Retensi: 7 daily, 4 weekly, 6 monthly |
| FR-12 | Backup manifest dengan checksum |

## 10. Prosedur Migrasi

### Fase A — Persiapan VPS Lama
1. Catat IP, hostname, timezone, OS
2. Catat service aktif
3. Catat cron dan timer
4. Catat commit Git aktif
5. Jalankan validasi data
6. Push seluruh kode yang sudah disetujui
7. Hentikan sementara updater
8. Buat backup final dengan checksum
9. Upload ke lokasi offsite
10. Verifikasi backup dapat diunduh

### Fase B — Provision VPS Baru
```bash
sudo apt-get install -y git nginx python3 python3-venv python3-pip curl jq rsync unzip zstd ca-certificates

sudo useradd --create-home --shell /bin/bash hermes || true
sudo mkdir -p /opt/hermes /var/lib/hermes-dashboard/{data,cache} /var/log/hermes-dashboard /etc/hermes-dashboard /var/backups/hermes-dashboard
sudo chown -R hermes:hermes /opt/hermes /var/lib/hermes-dashboard /var/log/hermes-dashboard /var/backups/hermes-dashboard
```

### Fase C — Restore Kode
```bash
sudo -u hermes git clone https://github.com/adiorany3/sembako-dashboard.git /opt/hermes/sembako-dashboard
cd /opt/hermes/sembako-dashboard
sudo -u hermes git checkout <COMMIT_DARI_MANIFEST>
```

### Fase D — Restore State dan Data
```bash
sha256sum -c SHA256SUMS
sudo rsync -aHAX --delete restore/dashboard-data/ /var/lib/hermes-dashboard/data/
sudo rsync -aHAX restore/hermes-state/ /home/hermes/.hermes/
sudo chown -R hermes:hermes /home/hermes/.hermes /var/lib/hermes-dashboard
```

### Fase E — Restore Environment
Buat `/etc/hermes-dashboard/hermes-dashboard.env` dengan nilai rahasia.

### Fase F — Install Dependency
```bash
cd /opt/hermes/sembako-dashboard
sudo -u hermes python3 -m venv .venv
sudo -u hermes .venv/bin/pip install --upgrade pip
sudo -u hermes .venv/bin/pip install -r requirements.txt
```

### Fase G — Install Service dan Timer
```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo cp deploy/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-dashboard.service hermes-update.timer hermes-backup.timer
```

### Fase H — Install Nginx
```bash
sudo cp deploy/nginx/hermes-dashboard.conf /etc/nginx/sites-available/
sudo ln -sfn /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Fase I — Verifikasi Sebelum Cutover
Jalankan acceptance test pada Bab 15.

### Fase J — Cutover
1. Turunkan TTL DNS
2. Arahkan domain ke VPS baru
3. Verifikasi dari jaringan luar
4. Biarkan VPS lama standby
5. Setelah stabil, nonaktifkan scheduler lama

## 11. Urutan Boot Hermes pada VPS Baru

1. Baca HERMES_SERVER_PRD.md
2. Baca backup-manifest.json
3. Pastikan commit Git sesuai manifest
4. Pastikan environment file tersedia
5. Pastikan state Hermes dipulihkan
6. Pastikan data dashboard dipulihkan
7. Periksa service hermes-dashboard
8. Periksa timer update dan backup
9. Jalankan health check
10. Jalankan validasi data
11. Periksa endpoint utama
12. Catat hasil pada CHANGELOG_HERMES.md
13. **Jangan melakukan pengembangan baru** sebelum status restore PASS

## 15. Acceptance Test

| ID | Test | Command |
|----|------|---------|
| AT-01 | Git | `git status --short && git rev-parse HEAD` |
| AT-02 | Dependency | `.venv/bin/pip check` |
| AT-03 | Service | `systemctl is-enabled hermes-dashboard && systemctl is-active hermes-dashboard` |
| AT-04 | Health | `curl http://127.0.0.1/api/health` |
| AT-05 | Nginx | `nginx -t && curl http://localhost/api/health` |
| AT-06 | Endpoints | `curl /api/sembako`, `/api/crypto`, `/api/emas`, `/api/pertanian`, `/api/summary` |
| AT-07 | Validasi | `python scripts/validate_data.py` |
| AT-08 | Timer | `systemctl list-timers --all \| grep hermes` |
| AT-09 | Manual Update | `systemctl start hermes-update.service` |
| AT-10 | Backup | `systemctl start hermes-backup.service` |
| AT-11 | Reboot | `sudo reboot` then verify |
| AT-12 | Hermes State | Verify skills, memory, instructions restored |

## 17. Struktur File yang Ditambahkan ke Repositori

```
deploy/
├── nginx/
│   └── hermes-dashboard.conf
├── systemd/
│   ├── hermes-dashboard.service
│   ├── hermes-update.service
│   ├── hermes-update.timer
│   ├── hermes-backup.service
│   └── hermes-backup.timer
└── scripts/
    └── install.sh

scripts/
├── backup.sh
├── restore.sh
├── verify.sh
└── run_all_updates.sh (placeholder)

.env.example
requirements.txt (update if needed)
HERMES_SERVER_PRD.md
CHANGELOG_HERMES.md
BACKUP_MANIFEST.example.json
```

## 20. Format Changelog

```markdown
## YYYY-MM-DD — <judul perubahan>
- Server:
- Commit:
- Perubahan:
- Backup sebelum perubahan:
- Service yang terdampak:
- Hasil health check:
- Hasil validasi data:
- Status rollback:
- Catatan:
```

## 21. Ringkasan Satu Menit

Untuk memindahkan Hermes ke VPS lain:
1. Push kode ke Git
2. Backup state Hermes, data, secret, dan konfigurasi server
3. Enkripsi dan upload backup keluar VPS
4. Buat manifest dan checksum
5. Siapkan VPS baru
6. Clone commit yang tercatat
7. Restore state dan data
8. Install dependency
9. Aktifkan satu service, timer update, timer backup, dan Nginx
10. Jalankan semua acceptance test
11. Arahkan trafik ke VPS baru
12. Matikan VPS lama hanya setelah backup baru dan reboot test berhasil
