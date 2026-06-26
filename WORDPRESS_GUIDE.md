# 📧 Cara Mengirim Artikel ke WordPress

## Setup Email-to-Post WordPress

Pertama, pastikan fitur **Email-to-Post** aktif di WordPress:

### 1. Aktifkan di WordPress Dashboard

1. Login ke `https://catataninsani.wordpress.com/wp-admin`
2. Settings → Writing
3. Cari "Post via Email" (atau "Email Publishing")
4. Aktifkan fitur
5. Note: Email tujuan = `xuxa564muxo@post.wordpress.com`

---

## Cara Pakai Script

### Opsi A: Menggunakan Gmail

```bash
python3 send_to_wordpress.py
```

Ikuti prompt:
1. Email: `your-email@gmail.com`
2. Password: **App Password** (bukan password biasa!)
3. File: `artikel_peternakan.md`
4. Status: `publish` (langsung tayang)

### Opsi B: Menggunakan Script Python Direct

```python
from send_to_wordpress import WordPressEmailPoster

poster = WordPressEmailPoster(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender_email="your-email@gmail.com",
    sender_password="your-app-password"
)

poster.send_article_from_file(
    "artikel_peternakan.md",
    status="publish"
)
```

---

## 🔐 Cara Generate App Password Gmail

Gmail tidak allow password biasa. Harus pakai App Password:

1. Buka: https://myaccount.google.com/security
2. Two-Step Verification harus aktif dulu
3. Klik: "App passwords"
4. Pilih: Mail + Windows Computer
5. Generate password baru (16 karakter)
6. **Copy & simpan** password tersebut
7. Gunakan password itu di script

---

## 📌 Email Format

Artikel akan dikirim dalam format:

```
To: xuxa564muxo@post.wordpress.com
Subject: 🐔 Strategi Bisnis Peternakan Modern di Indonesia 2026
Body: [Konten artikel lengkap dalam Markdown]
```

WordPress akan otomatis:
- ✅ Buat post baru
- ✅ Parse title dari Subject
- ✅ Convert Markdown ke HTML
- ✅ Publish (atau draft, terganti setting)

---

## ⏱️ Timeline

- Email dikirim → langsung terkirim
- WordPress memproses → 2-5 menit
- Post tayang di blog → otomatis

---

## ✅ Status Opsi

```
publish  → Langsung tayang di blog
draft    → Tersimpan sebagai draft
private  → Hanya owner bisa lihat
```

---

## 🐛 Troubleshooting

### Email stuck / tidak terkirim
- Check App Password (bukan password biasa)
- Pastikan Two-Step Verification aktif di Gmail
- Check inbox spam di Gmail

### Post tidak muncul di WordPress
- Cek Email-to-Post aktif di WordPress Settings
- Cek email `xuxa564muxo@post.wordpress.com` sudah terdaftar
- Cek status post (publish vs draft)

### Format artikel berantakan
- Pastikan file Markdown valid
- Check title pakai `# Title` (H1)
- Markdown convert otomatis ke HTML

---

## 🚀 Siap Kirim?

Mari kita tes! Adi tinggal:

1. **Konfirmasi:** App Password Gmail
2. **Jalankan:** `python3 send_to_wordpress.py`
3. **Enter:** Email + App Password
4. **Pilih:** File + status
5. **Done!** ✅

