# Implementation Roadmap — FM24 Player Recommendation System

Roadmap ini menerjemahkan desain arsitektur (ingestion, feature engineering, scoring engine, optimization, API, evaluation, deployment — termasuk age-curve modeling) menjadi urutan fase yang bisa dieksekusi. Setiap fase punya exit criteria yang jelas sehingga fase berikutnya tidak dimulai di atas fondasi yang belum stabil. Urutan ini sengaja linear di awal (Fase 0–3) karena setiap layer bergantung penuh pada layer sebelumnya, lalu bercabang di Fase 4–7 begitu data dan scorer dasar sudah berjalan.

---

## Fase 0 — Fondasi & Registry

**Tujuan:** menyiapkan struktur yang akan dipakai semua fase berikutnya, supaya tidak ada hardcoding kolom/role di tengah jalan.

- Canonical attribute dictionary: mapping semua singkatan FM (Tck, Wor, Vis, Cmp, Ant, dst) ke key internal stabil + kategori (technical/mental/physical/GK).
- Role & formation registry: daftar role-duty resmi FM (Sweeper Keeper, Complete Wing Back, Deep Lying Playmaker, dst) plus daftar formasi yang akan didukung, sebagai controlled vocabulary — bukan free text.
- Skema penyimpanan player store yang versioned/partitioned per batch ingestion (bukan upsert table biasa), karena ini prasyarat untuk backtesting di Fase 6.

**Exit criteria:** registry dan skema canonical sudah didefinisikan dan bisa divalidasi terhadap header dari sample file (arsenal_*, senior, u-21, left/right_defender, left/right_winger).

---

## Fase 1 — Data Ingestion Pipeline

**Tujuan:** semua file mentah (HTML squad/scouting view, RTF) bisa diubah jadi record ternormalisasi yang konsisten.

- Parser HTML table + parser RTF pipe-table → intermediate representation yang sama.
- Header-driven column mapping (parse header row per file, jangan asumsikan posisi kolom tetap).
- Parser field finansial: Transfer Value (banded range → low/high/midpoint), Salary (normalisasi ke periode tahunan).
- Parser status: kolom Inf (Wnt/Inj/Lst, dst) → flag boolean (is_injured, is_wanted, is_listed, is_unsettled).
- Scouting confidence: Knowledge level + masking Ability/Potential → confidence tier per record.
- Validasi baris: rentang atribut 1–20, field wajib, deteksi duplikat dalam satu klub.
- Entity resolution & merge logic: lintas file (squad vs scouting export) pakai composite key (nama + kebangsaan + age band + klub), konflik diresolusi ke record dengan confidence Knowledge lebih tinggi.

**Exit criteria:** seluruh sample file berhasil di-parse ke skema canonical tanpa kolom hilang/salah map, dan field finansial + status ter-decode dengan benar (tervalidasi manual terhadap beberapa baris sample yang sudah dicek).

---

## Fase 2 — Feature Engineering Layer

**Tujuan:** mengubah atribut mentah jadi fitur yang benar-benar dipakai scoring engine.

- Weight matrix role × atribut (v1) — bisa mulai dari formula yang dikenal komunitas FM analytics, disimpan sebagai config yang bisa diubah, bukan logic di kode.
- Role-fit score per (player, role, duty).
- Encoding versatilitas posisi (multi-hot dari Position eligibility string) + skor versatilitas.
- Tactical compatibility vector: role-fit per slot formasi + match profil fisik/mental terhadap playing style + indikator coverage slot formasi.
- Fitur finansial: value midpoint, band-width, salary tahunan, rasio value-efficiency (log-scaled).
- **Age-curve modeling** (3 sinyal terpisah, sesuai desain sebelumnya):
  - current-fit trajectory (kurva decline yang aware terhadap role — role berbasis fisik/pace decay lebih cepat dari role berbasis teknik/mental)
  - potential-realization signal untuk pemain muda (Age + Potential bila ter-unmask + trajectory role-fit → kategori "developing fit")
  - value-trajectory signal (Age vs band Transfer Value, untuk logika "jual sekarang sebelum value turun")
- Confidence-weighted features: setiap skor turunan bawa bobot confidence dari Knowledge level + band-width.
- Normalisasi (percentile) dalam populasi pembanding yang relevan per role, bukan global.

**Exit criteria:** untuk satu role contoh (misal Deep Lying Playmaker) dan satu sample squad, role-fit score yang dihasilkan korelasinya masuk akal dibanding Best Role/Best Duty bawaan FM pada baris yang sudah fully scouted.

---

## Fase 3 — Core Scoring Engine

**Tujuan:** mesin scoring content-based yang deterministik dan explainable, berfungsi penuh tanpa data feedback apa pun.

- Scorer utama: hitung role-fit + tactical compatibility per player terhadap query (formasi, style, role, duty) yang diberikan.
- Similarity embedding terpisah (PCA/reduksi dimensi, role-aware) untuk use case "cari pengganti pemain X" / analisis kedalaman skuad — independen dari scorer utama, jangan dicampur.
- Desain "three-mode routing": satu scorer yang sama dipanggil dengan framing input/output berbeda untuk squad optimization, transfer recommendation, retention/sale.

**Exit criteria:** scorer bisa dijalankan terhadap squad file dan scouting file dengan output role-fit + breakdown kontribusi atribut yang bisa ditelusuri (explainability), tanpa perlu data feedback apa pun.

---

## Fase 4 — Multi-Objective Optimization Layer

**Tujuan:** mengubah skor mentah jadi rekomendasi buy/sell/keep yang menimbang fit, finansial, dan usia sekaligus, bukan satu angka tunggal yang menyembunyikan trade-off.

- Hard filter budget & struktur gaji (diterapkan duluan, kandidat infeasible dikeluarkan/ditandai terpisah).
- Pareto frontier: fit / value-efficiency / age-adjusted return ditampilkan sebagai tiga sumbu, plus opsi blended score dengan bobot yang bisa dikonfigurasi.
- Logika sell-side: kombinasi role-fit + value-trajectory + wage burden → klasifikasi must-keep/contested/sell-candidate, dengan proteksi eksplisit agar pemain muda "developing fit" tidak otomatis jadi kandidat jual.
- Squad balance sebagai soft constraint: depth coverage, distribusi age-curve (hindari banyak pemain kunci menua bareng di window 2–3 tahun yang sama), redundansi role/duty.

**Exit criteria:** untuk satu skenario nyata (misal kebutuhan transfer di satu posisi dengan budget tertentu), output berupa daftar kandidat dengan klasifikasi feasible/infeasible dan breakdown tiga sumbu Pareto yang masuk akal secara manual.

---

## Fase 5 — API / Service Layer

**Tujuan:** membungkus scoring + optimization engine jadi endpoint yang bisa dipakai berulang.

- Endpoint squad analysis, transfer recommendation, retention/sale scoring (sesuai desain sebelumnya).
- Endpoint pendukung: ingestion/upload, konfigurasi weight matrix, feedback (untuk Fase 7).
- Validasi input tactical constraint (formasi/role/duty) terhadap registry dari Fase 0 — gagal cepat untuk kombinasi tidak valid.

**Exit criteria:** ketiga endpoint utama bisa dipanggil end-to-end dari file mentah sampai output rekomendasi terstruktur, tanpa perlu campur tangan manual di tengah.

---

## Fase 6 — Evaluation & Validation

**Tujuan:** memastikan scorer dan weight matrix tidak hanya jalan secara teknis, tapi juga masuk akal secara taktis.

- Konsistensi internal: bandingkan ranking role-fit terhadap Best Role/Best Duty bawaan FM pada pemain yang sudah fully scouted (sanity check bug, bukan target optimasi).
- Grounding eksternal: cek weight matrix terhadap definisi role yang dikenal di analitik sepak bola umum (independen dari FM).
- Siapkan mekanisme backtesting: simpan snapshot squad/transfer window untuk dibandingkan dengan keputusan aktual di kemudian hari (baru bisa dieksekusi penuh setelah beberapa siklus berjalan).

**Exit criteria:** tidak ada divergensi sistematis yang tidak bisa dijelaskan antara role-fit engine dan Best Role FM; weight matrix sudah didokumentasikan rasionalnya per role.

---

## Fase 7 — Learned Re-ranking Layer (opsional, setelah feedback cukup)

**Tujuan:** lapisan tambahan yang menyesuaikan skor berdasarkan keputusan yang benar-benar kamu ambil (accept/reject rekomendasi).

- Kumpulkan label feedback via endpoint Fase 5.
- Re-ranker berbasis gradient-boosted tree, dengan cold-start guard (baru aktif setelah jumlah label minimum tercapai).
- Fallback otomatis ke pure content-based scoring jika volume feedback terlalu rendah atau setelah patch besar (lihat Fase 8).

**Exit criteria:** layer ini terbukti meningkatkan precision@k terhadap label feedback dibanding scorer dasar, bukan sekadar overfit ke sample kecil.

---

## Fase 8 — Deployment & Iterasi Berkelanjutan

**Tujuan:** sistem tetap akurat seiring patch FM, save progression, dan window transfer berjalan.

- Versioning skema canonical & weight matrix dengan metadata kompatibilitas (versi FM/patch).
- Deteksi otomatis kolom baru/hilang atau role tak dikenal saat ingestion → flag review, jangan silently drop.
- Re-baselining statistik normalisasi secara periodik (bukan dibekukan di ingestion pertama).
- Review konfigurasi weight matrix pasca-patch (bukan retraining penuh, karena scorer inti deterministik).
- Downgrade/nonaktifkan sementara learned re-ranker (Fase 7) pasca-patch besar sampai feedback baru terkumpul.

**Exit criteria:** ada proses terdokumentasi untuk menangani patch baru tanpa merombak ulang seluruh pipeline.

---

## Ringkasan Dependensi

Fase 0 → 1 → 2 → 3 bersifat linear (wajib berurutan, masing-masing fondasi fase berikutnya). Fase 4 dan 6 bisa mulai paralel setelah Fase 3 selesai, karena keduanya sama-sama konsumen dari core scoring engine tapi tidak saling bergantung. Fase 5 butuh Fase 3 (minimal) dan idealnya Fase 4 sudah ada agar endpoint transfer/retention punya nilai penuh. Fase 7 murni opsional dan butuh Fase 5 berjalan dulu untuk mengumpulkan feedback. Fase 8 berjalan terus-menerus begitu sistem live, bukan fase sekali jalan.
