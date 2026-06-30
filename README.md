# ⚽ FM24 AI Recommendation Engine

Sebuah sistem analisis tingkat lanjut dan mesin pencari (scouting) cerdas untuk **Football Manager 24**. 
Sistem ini memproses data *Custom View* ekspor mentah (HTML/RTF) dari dalam gim, mengekstrak metrik performa lanjutan, dan merekomendasikan rekrutan pemain terbaik dengan menggunakan kombinasi reduksi dimensional (PCA) serta optimisasi *Pareto Frontier* layaknya platform analitik klub sepak bola profesional.

---

## 🌟 Fitur Utama

- **Data Ingestion Otomatis**: Mengurai file ekspor HTML dan RTF dari FM24, menyatukan duplikasi entitas, dan mengekstrak data finansial (gaji dan nilai transfer) yang rumit.
- **Advanced Feature Engineering**: 
  - *Multi-hot Tactical Profiling*: Menerjemahkan atribut dasar pemain menjadi skor peran yang lebih cerdas (Misal: *Advanced Forward*, *Deep Lying Playmaker*).
  - *Age Curve Penalties*: Menilai potensi pemain berdasarkan kurva umur biologis dari posisi tersebut.
- **Pareto-Optimal Transfer Optimizer**: Menemukan target transfer yang menyeimbangkan *Role Fit Score* tertinggi dengan biaya amortisasi (*Amortized Cost*) termurah.
- **Squad Retention Matrix**: Memetakan pemain yang sudah ada di skuat Anda ke dalam zona hijau (*Keep*), kuning (*Monitor*), atau merah (*Sell*).
- **Asynchronous MLOps Backend**: Dibangun di atas fondasi FastAPI, mendukung manajemen siklus data yang kuat (*schema drift detection*, *versioned data batches*).
- **Interactive Web Dashboard**: Dilengkapi antarmuka pengguna interaktif (Streamlit) dengan plot sebar 2D menggunakan Plotly.

---

## 🛠️ Instalasi & Persiapan

Sistem ini dikembangkan menggunakan Python 3.11+.

### 1. Kloning dan Siapkan Virtual Environment
Pastikan Anda sudah berada di dalam direktori `fm24-rm-system`:
```powershell
# Buat Virtual Environment
python -m venv .venv

# Aktifkan Virtual Environment (Windows)
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependensi
Karena ini menggunakan arsitektur gabungan (Data Science, Backend, dan Frontend), jalankan instalasi dari `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi ini dipisah ke dalam dua lingkungan kerja: **Backend (Mesin Utama)** dan **Frontend (Antarmuka Visual)**. Anda perlu membuka **dua jendela terminal** (Command Prompt/PowerShell) secara terpisah.

### Terminal 1: Nyalakan Backend (FastAPI)
*Engine* kalkulasi berjalan di belakang layar untuk menghitung ratusan ribu kemungkinan data.
```powershell
# Pastikan venv aktif
.\.venv\Scripts\Activate.ps1
uvicorn src.api.main:app --reload --port 8000
```

### Terminal 2: Nyalakan Dashboard (Streamlit)
*Dashboard* visual tempat Anda berinteraksi dengan data dan mesin rekomendasi.
```powershell
# Pastikan venv aktif
.\.venv\Scripts\Activate.ps1
streamlit run src/frontend/app.py --server.port 8501
```
*(Catatan: Jika saat pertama kali dijalankan Streamlit meminta alamat email, Anda bisa langsung menekan tombol `Enter` untuk melewatinya).*

---

## 📖 Cara Menggunakan Dashboard (Workflow)

Setelah UI terbuka di `http://localhost:8501`, berikut adalah alur kerja pencarian bakat yang direkomendasikan:

### Langkah 1: Data Ingestion (Memasukkan Data FM)
1. Ekspor *Custom View* yang memuat atribut pemain, nilai kontrak, umur, dll. dari dalam FM24 (Gunakan `CTRL+P` lalu simpan sebagai Web Page HTML atau Text File RTF).
2. Buka tab **📥 Data Ingestion** di *sidebar* sebelah kiri *dashboard*.
3. Seret dan lepas (drag-and-drop) file HTML/RTF tersebut.
4. Klik **Run Ingestion Pipeline**. *Backend* akan otomatis mengurai, mencari kelainan *patch*, dan menyimpannya ke dalam memori RAM secara asinkron.

### Langkah 2: Evaluasi Skuat (Squad Matrix)
1. Buka tab **📋 Squad Matrix**.
2. Masukkan nama klub yang sedang Anda tangani (misalnya: *Arsenal*).
3. Anda akan disuguhkan tabel **Retention Matrix** yang otomatis mewarnai mana pemain yang secara statistik membebani finansial tanpa memberikan kontribusi maksimal (Zonasi Merah / *Sell*), dan tabel **Squad Depth** untuk menyoroti area kelemahan taktik Anda.

### Langkah 3: Berburu Pemain (Transfer Optimizer)
1. Buka tab **💰 Pareto Transfer Optimizer**.
2. Ketik nama tim Anda agar mesin tahu untuk tidak merekomendasikan pemain yang sudah ada di klub Anda.
3. Tentukan **Target Role** (Misal: *Advanced Forward*) dan geser rentang maksimal biaya transfer serta gaji tahunan.
4. Mesin akan merender **Scatter Plot Interaktif**:
   - Anda ingin target di sisi ujung **Kiri Atas** (Kecocokan Peran Tertinggi dengan Biaya Amortisasi Terendah).
   - Arahkan kursor (*hover*) ke titik di grafik untuk melihat nama dan umur calon pemain incaran!

### Langkah 4: Tactical Config (Modifikasi Gaya Main)
Jika Anda merasa *Advanced Forward* dalam taktik Anda lebih membutuhkan atribut *Stamina* ketimbang *Pace*, Anda bisa mengubah nilai bawaan matematika ini di tab **⚙️ Tactical Config**.
Semua perubahan yang Anda lakukan di antarmuka ini akan disimpan dan akan memengaruhi cara *engine* memberikan rekomendasi di masa mendatang!

---

## 🧪 Alat Uji Matematis (Offline Evaluation)

Bagi pengguna ahli yang ingin meninjau ulang secara saintifik cara kerja mesin (tanpa UI):
```powershell
# Diagnostic: Bandingkan spesifikasi pembeda antar peran taktis
python src/evaluation/eval_archetypes.py

# Diagnostic: Jalankan pengetesan validasi untuk Backend API
pytest tests/test_api.py
```

Selamat menyempurnakan taktik dan merekrut *wonderkid* efisien!
