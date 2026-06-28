#!/usr/bin/env python3
"""
WordPress Article Generator v4 — Catatan Insani
================================================
Pure peternakan articles. No forced data.
Each article is a coherent blog post on a farming topic.
7 rotating topics.
"""

import json, random
from datetime import datetime
from pathlib import Path

WP_DIR = Path(__file__).resolve().parent.parent / "data" / "wp_articles"
WP_DIR.mkdir(exist_ok=True)


# ================================================================
# 7 ARTICLE TYPES — each is a complete, coherent blog post
# ================================================================

ARTICLES = [
    # 1
    {
        "title": "Cara Memilih Bibit Ayam Broiler yang Bagus: Panduan untuk Pemula",
        "category": "Tips Ternak",
        "body": """
<p>Memilih bibit DOC (Day Old Chick) yang berkualitas adalah langkah pertama menentukan keberhasilan ternak ayam broiler. Banyak pemula yang salah memilih bibit hanya karena harganya murah, padahal kualitas DOC menentukan 60-70% hasil akhir.</p>

<h4>Ciri DOC Sehat yang Harus Diperhatikan</h4>
<ul>
<li><strong>Postur tubuh tegak</strong> — DOC sehat berdiri kokoh, tidak jatuh atau miring. Jika ada yang terus terjatuh, kemungkinan ada masalah kaki atau syaraf.</li>
<li><strong>Mata cerah dan bersih</strong> — mata berair, kusam, atau tertutup lendir adalah tanda infeksi awal.</li>
<li><strong>Pusar kering dan bersih</strong> — pusar yang basah atau berdarah menandakan sanitasi inkubator buruk. Ini pintu masuk infeksi bakteri.</li>
<li><strong>Bulu kering dan halus</strong> — DOC sehat memiliki bulu halus yang mengembang. Bulu lepek atau kusut menandakan dehidrasi atau stres.</li>
<li><strong>Suara aktif</strong> — DOC sehat bersuara aktif dan merata. Jika ada yang terus mencekik atau diam, kemungkinan sakit.</li>
<li><strong>Berat badan seragam</strong> — DOC standar broiler 40-45 gram. Berat yang terlalu ringan (di bawah 38g) biasanya berasal dari indukan kurang gizi.</li>
</ul>

<h4>Sumber DOC Terpercaya</h4>
<p>Hindari membeli DOC dari pengepul yang tidak jelas asal-usulnya. Pilih distributor resmi seperti:</p>
<ul>
<li>PT Charoen Pokphand Indonesia (CP)</li>
<li>PT Japfa Comfeed Indonesia</li>
<li>PT Santosa Agrindo (Sierad Produce)</li>
<li>PT Panca Budi Investama</li>
</ul>
<p>Distributor resmi memberikan jaminan vaksinasi awal (ND + IBD) dan riwayat kesehatan indukan (parent stock).</p>

<h4>Harga DOC vs Kualitas</h4>
<p>DOC broiler berkisar Rp4.000-6.500 per ekor. Harga ini fluktuatif tergantung musim dan permintaan. Jangan tergiur DOC murah di bawah Rp3.500 — kemungkinan besar berasal dari DOC reject atau indukan tua.</p>
<p>Sebagai gambaran: DOC kualitas baik dari indukan muda (umur 30-45 minggu) menghasilkan pertumbuhan lebih cepat dan FCR lebih rendah dibanding DOC dari indukan tua (>60 minggu).</p>

<h4>Tips Setelah DOC Sampai</h4>
<ol>
<li><strong>Langsung masukkan ke brooding</strong> — suhu brooding harus 32-34°C di minggu pertama. Turunkan 0.5°C per minggu.</li>
<li><strong>Air gula hangat</strong> — berikan air hangat dengan gula 5% selama 6 jam pertama untuk mengurangi stres transportasi.</li>
<li><strong>Pakan starter sesegera mungkin</strong> — dalam 24 jam pertama. DOC yang lambat makan = pertumbuhan terhambat.</li>
<li><strong>Amati 3 hari pertama</strong> — 72 jam pertama adalah masa kritis. Jika ada DOC yang terus diam atau tidak makan, langsung singkirkan.</li>
</ol>

<h4>Kesimpulan</h4>
<p>Investasi di bibit yang baik akan terbayar di akhir panen. DOC berkualitas = pertumbuhan seragam, kematian rendah, dan FCR optimal. Jangan korbankan kualitas bibit demi menghemat seribu-dua ribu rupiah per ekor.</p>
"""
    },
    # 2
    {
        "title": "Formulasi Pakan Ayam Broiler: Cara Racik Sendiri untuk Hemat Biaya",
        "category": "Optimasi Biaya",
        "body": """
<p>Pakan komersial memang praktis, tapi harganya terus naik. Dengan meracik pakan sendiri, peternak bisa menghemat 20-30% biaya pakan tanpa mengorbankan pertumbuhan ternak.</p>

<h4>Prinsip Dasar Formulasi Pakan</h4>
<p>Pakan ternak harus memenuhi 4 kebutuhan utama:</p>
<ul>
<li><strong>Energi</strong> — sumber utama dari jagung, beras, atau singkong. Untuk broiler finisher: 3.000-3.200 kkal/kg.</li>
<li><strong>Protein</strong> — dari bungkil kedelai, bungkil kelapa, atau ampas tahu. Untuk broiler finisher: 19-21% protein kasar.</li>
<li><strong>Serat</strong> — dari dedak padi atau rumput. Maksimal 5-7% untuk broiler. Terlalu banyak serat mengurangi daya cerna.</li>
<li><strong>Vitamin & mineral</strong> — dari premix atau konsentrat. Tidak bisa diabaikan.</li>
</ul>

<h4>Contoh Ransum Broiler Finisher (Minggu 5-6)</h4>
<table style="width:100%;border-collapse:collapse;margin:12px 0">
<tr style="background:#0073aa;color:#fff"><th style="padding:8px;text-align:left">Bahan</th><th style="padding:8px;text-align:right">Komposisi</th><th style="padding:8px;text-align:left">Fungsi</th></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Jagung kuning</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">55%</td><td style="padding:6px;border-bottom:1px solid #eee">Sumber energi utama</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Bungkil kedelai</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">22%</td><td style="padding:6px;border-bottom:1px solid #eee">Sumber protein</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Dedak padi</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">12%</td><td style="padding:6px;border-bottom:1px solid #eee">Serat + energi tambahan</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Minyak sawit</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">5%</td><td style="padding:6px;border-bottom:1px solid #eee">Energy density tinggi</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Premix broiler</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">3%</td><td style="padding:6px;border-bottom:1px solid #eee">Vitamin & mineral</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Kalsium fosfat</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">2%</td><td style="padding:6px;border-bottom:1px solid #eee">Tulang & cangkang</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Garam dapur</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">0.5%</td><td style="padding:6px;border-bottom:1px solid #eee">Elektrolit</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Metionin</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">0.3%</td><td style="padding:6px;border-bottom:1px solid #eee">Amino acid esensial</td></tr>
<tr><td style="padding:6px;border-bottom:1px solid #eee">Lysin HCl</td><td style="padding:6px;border-bottom:1px solid #eee;text-align:right">0.2%</td><td style="padding:6px;border-bottom:1px solid #eee">Amino acid esensial</td></tr>
</table>

<h4>Alternatif Pengganti Bungkil Kedelai</h4>
<p>Bungkil kedelai sering mahal. Beberapa alternatif yang bisa dicampur:</p>
<ul>
<li><strong>Ampas tahu</strong> — protein 20-25%, tapi kadar air tinggi. Perlu dikeringkan dulu. Cocok untuk campuran 10-15%.</li>
<li><strong>Bungkil kelapa</strong> — protein 18-22%, lebih murah dari kedelai. Tapi rendah lisin.</li>
<li><strong>Onggok</strong> — protein 18-20%, hasil sampingan industri tapi. Murah tapi perlu fermentasi.</li>
<li><strong>Limbah roti/biskuit</strong> — protein 10-12%, tapi tinggi karbohidrat. Campur maksimal 10%.</li>
</ul>

<h4>Cara Membuat Pakan Fermentasi</h4>
<ol>
<li>Campur semua bahan kering sesuai formulasi.</li>
<li>Larutkan ragi roti (5 gram/kg pakan) dalam air hangat.</li>
<li>Siram rata ke campuran pakan, aduk hingga lembab.</li>
<li>Simpan dalam wadah tertutup rapat selama 24-48 jam di tempat gelap.</li>
<li>Jika tercium aroma seperti tape — fermentasi berhasil.</li>
</ol>
<p>Fermentasi meningkatkan daya cerna pakan 15-25% karena mikroorganisme memecah serat kompleks menjadi nutrisi yang lebih mudah diserap.</p>

<h4>Kesimpulan</h4>
<p>Meracik pakan sendiri bukan tentang mengurangi kualitas — tapi tentang memahami kebutuhan nutrisi ternak dan memanfaatkan bahan lokal yang tersedia. Mulai dengan ransum sederhana, pantau pertumbuhan, lalu sesuaikan formulasi dari pengalaman.</p>
"""
    },
    # 3
    {
        "title": "Manajemen Kesehatan Ternak: Pencegahan Lebih Murah dari Pengobatan",
        "category": "Kesehatan Ternak",
        "body": """
<p>Seorang peternak sukses pernah berkata: "Uang yang saya keluarkan untuk vaksin Rp500 per ekor, tapi uang yang saya habiskan untuk mengobati wabak Rp50 juta." Pencegahan memang jauh lebih murah dari pengobatan.</p>

<h4>Vaksinasi: Jadwal yang Wajib Dipatuhi</h4>
<p>Untuk unggas (ayam broiler):</p>
<ul>
<li><strong>Hari 1</strong>: Vaksin ND (Newcastle Disease) + IB (Infectious Bronchit) tetes mata atau hidung</li>
<li><strong>Hari 7-10</strong>: Vaksin ND + IB ulang</li>
<li><strong>Hari 14</strong>: Vaksin IBD (Infectious Bursal Disease / Gumboro) per oral</li>
<li><strong>Hari 21</strong>: Vaksin ND laju (booster)</li>
<li>Untuk layer: booster ND tiap 4-6 minggu selama masa produksi</li>
</ul>
<p>Harga vaksin ND berkisar Rp200-500 per dosis. Dengan vaksinasi tepat waktu, risiko wabak ND bisa diturunkan hingga 90%.</p>

<h4>Biosekuriti Dasar</h4>
<p>Biosekuriti bukan soal membangun gedung mahal. Ini adalah kebiasaan sehari-hari yang mencegah penyakit masuk ke kandang:</p>
<ol>
<li><strong>Footbath di pintu masuk</strong> — larutan formalin 2% atau glutaraldehyde. Ganti setiap 2-3 hari.</li>
<li><strong>Ganti pakaian dan sepatu</strong> — siapa pun yang masuk kandang harus pakai pakaian dan sepatu khusus kandang.</li>
<li><strong>Batasi kunjungan</strong> — semakin banyak orang masuk kandang, semakin besar risiko kontaminasi.</li>
<li><strong>Karantina ternak baru</strong> — minimal 7-14 hari sebelum bergabung dengan kawanan utama.</li>
<li><strong>Pisahkan area</strong> — kandang anakan, pembesaran, dan produksi harus terpisah secara fisik.</li>
</ol>

<h4>Tanda-Tanda Penyakit yang Harus Diwaspadai</h4>
<ul>
<li>Nafsu makan menurun drastis pada lebih dari 5% kawanan</li>
<li>Aktivitas berkurang — ternak lebih banyak diam dari biasanya</li>
<li>Demam — cek suhu rektal. Normal ayam 40-42°C. Di atas 43°C = demam.</li>
<li>Produksi telur menurun mendadak (untuk layer)</li>
<li>Ngorok atau napas berat pada unggas</li>
<li>Diare atau kotoran berwarna abnormal (hijau, kuning, atau berdarah)</li>
<li>Bengkak di kepala atau wajah (untuk unggas)</li>
<li>Kematian mendadak pada beberapa ekor dalam waktu singkat</li>
</ul>
<p>Jika menemukan tanda-tanda ini, langkah pertama adalah isolasi ternak sakit. Jangan coba-coba obati sendiri tanpa diagnosis yang jelas. Hubungi dokter hewan atau penyuluh peternakan setempat.</p>

<h4>Manajemen Limbah Kandang</h4>
<p>Limbah kandang yang tidak dikelola dengan baik menjadi sumber penyakit. Praktik dasar:</p>
<ul>
<li>Ganti alas kandang minimal 2x seminggu</li>
<li>Kompos limbah kandang — bisa jadi pupuk organik bernilai jual</li>
<li>Cuci kandang dengan disinfektan setiap selesai panen (sebelum DOC baru masuk)</li>
<li>Tunggu minimal 7 hari empty setelah cuci sebelum isi DOC baru</li>
</ul>

<h4>Biaya Pencegahan vs Pengobatan</h4>
<ul>
<li>Vaksinasi per ekor/bulan: Rp200-500</li>
<li>Disinfektan per kandang/bulan: Rp100.000-300.000</li>
<li>Biaya pengobatan wabak ringan: Rp2.000.000-10.000.000</li>
<li>Biaya wabak berat (kematian massal): Rp10.000.000-100.000.000</li>
</ul>
<p>Investasi Rp500.000/bulan untuk pencegahan bisa mencegah kerugian Rp50 juta. Itu matematika sederhana yang sering dilupakan.</p>
"""
    },
    # 4
    {
        "title": "Ternak Sapi Potong: Dari Pemilihan Bibit hingga Masa Panen",
        "category": "Panduan Ternak",
        "body": """
<p>Ternak sapi potong menjanjikan margin keuntungan yang besar per ekor, meski modal awal lebih tinggi dibanding unggas. Siklus pemeliharaan 8-12 bulan, dan permintaan daging sapi di Indonesia terus meningkat setiap tahun.</p>

<h4>Memilih Bibit Sapi Potong</h4>
<p>Bibit yang baik menentukan 70% keberhasilan. Berdasarkan pengalaman peternak di Jawa dan Sumatera:</p>
<ul>
<li><strong>Jenis sapi</strong>: Crossbreed seperti Simental, Limousin, dan Brahman Cross (BX) paling umum. Sapi lokal (Madura, Bali) lebih tahan penyakit tapi pertumbuhan lebih lambat.</li>
<li><strong>Berat ideal saat dibeli</strong>: 200-250 kg (feeder/bakalan). Di atas 250 kg sudah terlalu tua untuk dibesarkan, di bawah 200 kg terlalu rentan sakit.</li>
<li><strong>Usia</strong>: 12-18 bulan. Cek dari gigi — sapi umur 12-18 bulan biasanya sudah mulai tumbuh gigi permanen.</li>
<li><strong>Fisik</strong>: tubuh berisi (bukan kurus kering), punggung lurus, tidak pincang, nafsu makan aktif.</li>
</ul>

<h4>Persiapan Kandang</h4>
<p>Untuk pemula, kandang individu lebih mudah dikelola daripada kandang kelompok.</p>
<ul>
<li><strong>Ukuran kandang</strong>: minimal 3x3 meter per ekor. Sapi butuh ruang untuk berdiri, berbaring, dan berputar.</li>
<li><strong>Alas kandang</strong>: semen berlubang atau tanah dengan jerami/sekam setebal 15-20 cm. Ganti minimal 2x seminggu.</li>
<li><strong>Tempat pakan</strong>: palung semen atau besi. Ketinggian 60-80 cm dari lantai.</li>
<li><strong>Tempat minum</strong>: tersedia 24 jam. Sapi potong minum 30-50 liter per hari tergantung ukuran dan suhu.</li>
<li><strong>Atap</strong>: terpal atau genteng. Yang penting kandang tidak kepanasan di siang hari dan tidak bocor saat hujan.</li>
</ul>

<h4>Pakan Sapi Potong</h4>
<p>Target pertumbuhan: 0,8-1,2 kg per hari. Untuk mencapai target ini, ransum harus mengandung cukup energi dan protein.</p>
<ul>
<li><strong>Hijauan</strong>: rumput gajah, kolonjono, king grass, atau rumput lapangan. 30-40 kg per ekor per hari.</li>
<li><strong>Konsentrat</strong>: campuran ampas tahu (40%), bekatul (30%), jagung giling (25%), dan garam (5%). 5-8 kg per ekor per hari.</li>
<li><strong>Mineral</strong>: blok mineral atau campuran garam kasar + kapur tulis. Sapi kekurangan mineral = nafsu makan turun.</li>
<li><strong>Air minum</strong>: bersih, tidak terbatas, tidak terlalu dingin.</li>
</ul>
<p>Rasio hijauan:konsentrat yang ideal adalah 70:30. Terlalu banyak konsentrat bisa menyebabkan asidosis (pH rumen turun drastis), yang berujung pada diare dan bahkan kematian.</p>

<h4>Pemeliharaan Harian</h4>
<ol>
<li><strong>Pagi (06:00)</strong>: beri pakan hijauan segar, cek air minum, amati perilaku ternak.</li>
<li><strong>Siang (12:00)</strong>: beri konsentrat, cek kandang (kotoran, kelembaban).</li>
<li><strong>Sore (17:00)</strong>: beri pakan hijauan lagi, bersihkan tempat minum.</li>
<li><strong>Mingguan</strong>: timbang perkembangan berat badan, catat di buku.</li>
<li><strong>Bulanan</strong>: dehelmintasi (obat cacing), evaluasi FCR.</li>
</ol>

<h4>Analisis Biaya Sederhana</h4>
<ul>
<li>Bibit 200-250 kg: Rp15-22 juta (tergantung jenis dan lokasi)</li>
<li>Pakan 8 bulan (hijauan + konsentrat): Rp6-10 juta</li>
<li>Obat & vaksin: Rp500.000-1.000.000</li>
<li>Biaya kandang & lain-lain: Rp2-3 juta</li>
<li><strong>Total modal per ekor</strong>: Rp23-36 juta</li>
<li><strong>Target berat jual</strong>: 350-450 kg</li>
<li><strong>Harga jual</strong>: Rp70.000-85.000/kg tergantung lokasi dan musim</li>
</ul>
<p>Margin per ekor bisa mencapai Rp5-12 juta tergantung efisiensi pakan dan timing jual.</p>

<h4>Kesimpulan</h4>
<p>Ternak sapi potong bukan bisnis instan. Butuh kesabaran 8-12 bulan untuk hasil. Tapi dengan manajemen yang benar — bibit bagus, pakan tepat, kesehatan terjaga — margin per ekor bisa menjanjikan. Mulai dari 2-3 ekor, pelajari dari pengalaman, lalu scale up.</p>
"""
    },
    # 5
    {
        "title": "Cara Membuat Pakan Fermentasi untuk Ternak: Hemat & Efektif",
        "category": "Optimasi Biaya",
        "body": """
<p>Fermentasi pakan adalah teknik sederhana yang bisa meningkatkan daya cerna pakan hingga 25%. Mikroorganisme dalam proses fermentasi memecah serat kompleks menjadi nutrisi yang lebih mudah diserap oleh ternak. Hasilnya: ternak tumbuh lebih cepat dengan pakan yang sama.</p>

<h4>Mengapa Fermentasi Efektif?</h4>
<ul>
<li><strong>Meningkatkan protein</strong> — jamur dan bakteri baik menghasilkan protein sel tunggal yang bergizi.</li>
<li><strong>Mengurai serat</strong> — selulosa dan hemiselulosa dipecah menjadi gula sederhana.</li>
<li><strong>Probiotik alami</strong> — mikroorganisme baik membantu kesehatan pencernaan ternak.</li>
<li><strong>Mengurangi bau kotoran</strong> — pencernaan lebih efisien = limbah lebih sedikit dan tidak berbau.</li>
<li><strong>Mengawetkan pakan</strong> — pakan fermentasi bisa disimpan lebih lama dari pakan basah biasa.</li>
</ul>

<h4>Resep Fermentasi Pakan Unggas</h4>
<p>Bahan:</p>
<ul>
<li>Dedak padi: 40 kg</li>
<li>Jagung giling: 30 kg</li>
<li>Bungkil kedelai: 20 kg</li>
<li>Ampas tahu segar: 10 kg</li>
<li>Ragi roti (Fermipan): 50 gram</li>
<li>Gula pasir: 200 gram</li>
<li>Air secukupnya (sampai lembab, bukan basah)</li>
</ul>
<p>Cara membuat:</p>
<ol>
<li>Campur semua bahan kering hingga rata.</li>
<li>Larutkan ragi dan gula dalam 2 liter air hangat (30-35°C). Diamkan 15 menit sampai berbusa.</li>
<li>Siram larutan ragi ke campuran pakan. Aduk rata.</li>
<li>Tambah air sedikit-sedikit sampai pakan lembab tapi tidak menetes saat digenggam.</li>
<li>Masukkan ke dalam drum atau karung tertutup rapat. Padatkan untuk mengurangi udara.</li>
<li>Fermentasi selama 24-48 jam di tempat teduh.</li>
<li>Pakan siap pakai jika tercium aroma seperti tape atau roti发酵.</li>
</ol>
<p>Jika tercium bau busuk atau berlendir hitam, fermentasi gagal. Jangan pakai — buang dan mulai ulang.</p>

<h4>Fermentasi Pakan Ternak Besar (Sapi/Kambing)</h4>
<p>Bahan:</p>
<ul>
<li>Jerami padi: 50 kg (dipotong 3-5 cm)</li>
<li>Dedak padi: 15 kg</li>
<li>Ampas tahu: 10 kg</li>
<li>Molase: 3 liter</li>
<li>Urea: 1 kg</li>
<li>Air: 50-60 liter</li>
</ul>
<p>Cara:</p>
<ol>
<li>Jerami dipotong pendek agar mudah difermentasi.</li>
<li>Campur jerami, dedak, dan ampas tahu.</li>
<li>Larutkan molase dan urea dalam air, siram ke campuran.</li>
<li>Padatkan dalam drum tertutup atau lobang tanah yang dialasi plastik.</li>
<li>Fermentasi 3-4 minggu.</li>
<li>Pakan siap jika jerami sudah lunak dan berbau manis seperti silase.</li>
</ol>
<p>Pakan hasil fermentasi untuk ternak besar ini bisa menggantikan 20-30% kebutuhan harian. Jerami yang tadinya tidak bergizi menjadi sumber energi yang layak.</p>

<h4>Kesalahan Umum yang Harus Dihindari</h4>
<ul>
<li><strong>Terlalu basah</strong> — pakan yang terlalu basah cepat busuk. Genggam: jika air menetes, terlalu basah.</li>
<li><strong>Tidak tertutup rapat</strong> — udara masuk = kontaminasi jamur. Tutup rapat dengan karet atau tali.</li>
<li><strong>Wadah kotor</strong> — cuci wadah dengan air panas sebelum pakai.</li>
<li><strong>Terlalu lama</strong> — fermentasi lebih dari 3 hari untuk unggas sudah berlebihan. Nutrisi mulai rusak.</li>
<li><strong>Langsung pakai tanpa cek</strong> — selalu cek aroma dulu. Bau busuk = jangan dipakai.</li>
</ul>

<h4>Manfaat untuk Peternak Kecil</h4>
<p>Untuk peternak dengan 100-500 ekor unggas, fermentasi pakan bisa menghemat Rp1-3 juta per bulan dari selisih harga bahan baku vs pakan komersial. Investasi awal hanya Rp200.000-500.000 untuk ragi dan wadah fermentasi.</p>
"""
    },
    # 6
    {
        "title": "Menjalankan Usaha Ternak Kambing untuk Pemula: Langkah Awal yang Tepat",
        "category": "Tips Ternak",
        "body": """
<p>Ternak kambing adalah salah satu usaha peternakan dengan modal menengah yang menjanjikan. Permintaan daging kambing cukup stabil sepanjang tahun, dan meningkat signifikan menjelang Idul Adha. Berikut panduan langkah demi langkah untuk pemula.</p>

<h4>Pilih Jenis Kambing yang Tepat</h4>
<ul>
<li><strong>Kambing Etawa (PE)</strong>: postur besar, pertumbuhan cepat, cocok untuk peternakan daging. Harga bibir Rp3-6 juta.</li>
<li><strong>Kambing Kacang</strong>: kambing lokal, tahan panas dan penyakit. Pertumbuhan lebih lambat tapi biaya perawatan rendah.</li>
<li><strong>Kambing Boer</strong>: jenis impor dari Afrika Selatan, pertumbuhan sangat cepat. Harga bibit tinggi (Rp5-10 juta).</li>
<li><strong>Domba</strong>: bulu tebal, cocok di dataran tinggi. Permintaan tinggi menjelang Qurban.</li>
</ul>
<p>Untuk pemula, kambing PE atau Kacang lebih disarankan karena lebih mudah didapat dan biaya awal lebih rendah.</p>

<h4>Persiapan Kandang</h4>
<ul>
<li><strong>Ukuran</strong>: minimal 1.5x1.5 meter per ekor untuk kandang kelompok.</li>
<li><strong>Tipe</strong>: kandang panggung (stilt house) dengan ketinggian 50-80 cm dari tanah. Kelebihannya: kotoran langsung jatuh ke bawah, kandang tetap kering.</li>
<li><strong>Alas</strong>: bambu berjarak 1-2 cm atau besi hollow. Tidak boleh terlalu lebar (kaki masuk) atau terlalu sempit (kotoran tersangkut).</li>
<li><strong>Atap</strong>: genteng atau aspal. Pastikan tidak bocor. Sapi kambing rentan pneumonia jika basah terus.</li>
<li><strong>Atap</strong>: pastikan kandang teduh dari sinar matahari langsung. Kambing tidak tahan panas berlebih.</li>
</ul>

<h4>Pakan Kambing</h4>
<ul>
<li><strong>Hijauan</strong>: rumput gajah, lamtoro, kacang panjang, daun singkong. 2-3 kg per ekor per hari.</li>
<li><strong>Konsentrat</strong>: bekatul, ampas tahu, kulit kedelai. 0.5-1 kg per ekor per hari.</li>
<li><strong>Suplemen</strong>: mineral block, garam kasar. Penting untuk kesehatan pencernaan.</li>
<li><strong>Air minum</strong>: 2-4 liter per ekor per hari. Bersih dan segar.</li>
</ul>
<p>Kambing adalah hewan browsing — mereka lebih suka makan daun dan dedaunan daripada rumput. Manfaatkan tanaman limbah pertanian seperti daun ubi jalar, daun pisang, atau lamtoro.</p>

<h4>Reproduksi</h4>
<ul>
<li><strong>Indukan betina</strong>: siap kawin pada usia 8-10 bulan (berat minimal 25-30 kg).</li>
<li><strong>Indukan jantan</strong>: siap kawin pada usia 10-12 bulan (berat minimal 30-35 kg).</li>
<li><strong>Masa kebuntingan</strong>: 150 hari (5 bulan).</li>
<li><strong>Anak per kelahiran</strong>: biasanya 1-2 ekor. Dengan manajemen nutrisi baik, bisa mencapai kembar 3.</li>
<li><strong>Jarak kelahiran</strong>: 8-12 bulan antara kelahiran. Artinya 1 indukan bisa menghasilkan 2-3 anak per tahun.</li>
</ul>
<p>Satu ekor indukan yang produktif bisa menghasilkan pendapatan Rp6-12 juta per tahun dari penjualan anak. Dengan 10 indukan, potensi pendapatan Rp60-120 juta per tahun.</p>

<h4>Manajemen Kesehatan</h4>
<ul>
<li><strong>Vaksinasi</strong>: vaksin POX (kudis) dan tetanus untuk semua anak kambing.</li>
<li><strong>Dehelmintasi</strong>: obat cacing tiap 3-4 bulan. Cacing internal adalah pembunuh diam-diam yang mengurangi nafsu makan dan berat badan.</li>
<li><strong>Obat luar</strong>: salep untuk kudis atau luka. Siapkan betadine dan salep antibiotik.</li>
<li><strong>Isolasi</strong>: pisahkan kambing sakit dari kawanan segera.</li>
</ul>

<h4>Analisis Biaya untuk 5 Ekor Indukan</h4>
<ul>
<li>Indukan PE 5 ekor: Rp15-25 juta</li>
<li>Kandang (5x3 meter): Rp5-8 juta</li>
<li>Pakan per bulan (5 indukan + anak): Rp1.5-2.5 juta</li>
<li>Obat & vaksin per tahun: Rp500.000-1.000.000</li>
<li><strong>Total modal awal</strong>: Rp22-37 juta</li>
<li><strong>Potensi pendapatan per tahun</strong>: Rp30-60 juta (10-15 anak x Rp3-5 juta/anak)</li>
</ul>
<p>ROI bisa mencapai 50-100% di tahun kedua setelah populasi indukan stabil. Kunci utama: manajemen reproduksi dan kesehatan yang konsisten.</p>
"""
    },
    # 7
    {
        "title": "Pemanfaatan Limbah Peternakan: Dari Masalah Jadi Peluang Bisnis",
        "category": "Peluang Bisnis",
        "body": """
<p>Limbah peternakan sering dianggap sebagai masalah — bau, polusi, dan tempat berkembangbiaknya lalat. Tapi sebenarnya, limbah ini adalah sumber pendapatan yang belum dimanfaatkan oleh kebanyakan peternak.</p>

<h4>Jenis Limbah Peternakan dan Nilai Jualnya</h4>
<ul>
<li><strong>Kotoran kering</strong>: bisa diolah jadi pupuk organik Rp1.500-3.000/kg.</li>
<li><strong>Kotoran segar</strong>: bahan baku biogas untuk memasak atau listrik.</li>
<li><strong>Bulu ayam</strong>: bahan baku pupuk, pakan ternak, atau isolasi termal.</li>
<li><strong>Tulang & ampas</strong>: bahan baku pakan ternak (tepung tulang) atau pupuk.</li>
<li><strong>Air cucian kandang</strong>: pupuk cair organik untuk tanaman.</li>
</ul>

<h4>Pupuk Organik dari Kotoran Ternak</h4>
<p>Proses pembuatan pupuk organik sederhana dan bisa dilakukan di lahan kecil:</p>
<ol>
<li><strong>Pengumpulan</strong>: kumpulkan kotoran kering (jika kandang panggung, langsung jatuh ke kolong). Untuk unggas, kotoran + sekam bisa langsung difermentasi.</li>
<li><strong>Fermentasi</strong>: campur kotoran dengan EM4 (Effektive Microorganism 4) atau ragi. Biarkan 2-4 minggu di tempat teduh.</li>
<li><strong>Pengeringan</strong>: jemur pupuk hasil fermentasi sampai kering. Gunakan mesin pengering sederhana atau jemur matahari.</li>
<li><strong>Pengemasan</strong>: kemas dalam karung plastik 5 kg atau 10 kg. Beri label: nama produk, komposisi, tanggal produksi.</li>
</ol>
<p>Harga pupuk organik kandang di pasaran Rp1.500-3.000 per kg. Untuk kandang dengan 1.000 ekor ayam,produksi kotoran bisa mencapai 200-300 kg per minggu. Potensi pendapatan tambahan: Rp1.2-3.6 juta per bulan.</p>

<h4>Biogas dari Limbah Peternakan</h4>
<p>Biogas adalah solusi energi sekaligus pengelolaan limbah. Prinsipnya sederhana: kotoran difermentasi dalam reactor tertutup menghasilkan metana yang bisa digunakan untuk memasak atau menghasilkan listrik.</p>
<ul>
<li><strong>Investasi awal</strong>: Rp5-15 juta untuk reactor biogas sederhana (kapasitas 2-5 m³).</li>
<li><strong>Bahan baku</strong>: kotoran sapi/kambing. Untuk unggas perlu dicampur air karena kotorannya terlalu kering.</li>
<li><strong>Produksi gas</strong>: 1 kg kotoran sapi menghasilkan 0,04 m³ gas. Cukup untuk 1-2 jam memasak.</li>
<li><strong>Masa pakai</strong>: reactor bisa bertahan 10-15 tahun dengan perawatan minimal.</li>
</ul>
<p>Untuk peternakan sapi dengan 50 ekor, biogas bisa menggantikan kebutuhan LPG 3 kg sebanyak 2-3 tabung per minggu. Penghematan: Rp60.000-90.000 per minggu = Rp240.000-360.000 per bulan.</p>

<h4>Pupuk Cair Organik (POC)</h4>
<p>Kotoran ternak juga bisa diolah jadi pupuk cair untuk tanaman:</p>
<ol>
<li>Campur kotoran segar dengan air (1:5).</li>
<li>Tambahkan EM4 atau gula merah sebagai biang fermentasi.</li>
<li>Fermentasi 2 minggu dalam wadah tertutup.</li>
<li>Saring dan encerkan (1:10) sebelum disiram ke tanaman.</li>
</ol>
<p>POC organik sangat dicari petani sayur dan buah karena harganya lebih mahal dari pupuk kimia dan hasilnya lebih bagus untuk jangka panjang.</p>

<h4>Bulu Ayam: Limbah Bernilai Tinggi</h4>
<ul>
<li><strong>Pupuk bulu</strong>: bulu difermentasi menghasilkan pupuk nitrogen tinggi. Rp500-1.000/kg.</li>
<li><strong>Pakan ternak</strong>: bulu dihancurkan dan difermentasi menjadi bahan protein untuk pakan ikan atau unggas.</li>
<li><strong>Isolasi termal</strong>: bulu ayam digunakan sebagai bahan isolasi alami yang ramah lingkungan.</li>
</ul>

<h4>Kesimpulan</h4>
<p>Limbah peternakan bukan masalah — ini aset yang belum dimanfaatkan. Dengan investasi kecil (Rp2-5 juta untuk peralatan dasar), peternak bisa menghasilkan pupuk organik, biogas, atau produk lain yang menambah pendapatan. Mulai dari satu jenis limbah, kuasai prosesnya, lalu diversifikasi.</p>
"""
    },
]


def main():
    now = datetime.now()
    ds = now.strftime("%d %B %Y")

    # Pick article (rotate daily)
    random.seed(now.timetuple().tm_yday)
    art = random.choice(ARTICLES)

    print("=" * 60)
    print("WordPress Article Generator v4")
    print("=" * 60)
    print(f"  Title:    {art['title']}")
    print(f"  Category: {art['category']}")
    print(f"  Date:     {ds}")
    print(f"{'=' * 60}")

    # Save
    meta_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.json"
    html_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.html"

    meta_path.write_text(json.dumps({
        "title": art["title"],
        "category": art["category"],
        "content": art["body"],
        "date": ds,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    html_path.write_text(art["body"], encoding="utf-8")

    print(f"\n  Files: {meta_path.name}, {html_path.name}")
    print(f"  Open http://43.153.196.161:5000/article to copy.")


if __name__ == "__main__":
    main()
