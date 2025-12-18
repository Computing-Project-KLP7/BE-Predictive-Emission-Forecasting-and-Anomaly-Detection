# Predictive Emission Forecasting And Anomaly Detection

## Objectives

Tujuan utama proyek ini adalah mentransformasikan data telematika **TransTRACK** menjadi keputusan operasional yang terukur dan strategis.

### O1 – Predictive Emission Forecasting

Menyediakan estimasi dan peramalan emisi **CO₂ harian per kendaraan** secara akurat, dilengkapi dengan:

* Intensitas emisi (gCO₂/km)
* Pemisahan kondisi **idle** dan **moving**

Kapabilitas ini mendukung manajemen dalam memantau baseline emisi, menetapkan target reduksi, serta mengevaluasi efektivitas intervensi.

### O2 – Emission & Fuel Anomaly Detection

Sistem secara proaktif mendeteksi anomali yang dapat ditindaklanjuti, antara lain:

* Dugaan penyalahgunaan atau pencurian BBM
* Inefisiensi operasional
* Potensi malfungsi sensor

Setiap anomali diprioritaskan dan dikirimkan melalui **notifikasi real-time** dengan konteks pendukung untuk investigasi lapangan.

### O3 – Insight & Recommendation

Melengkapi siklus dari data hingga tindakan melalui:

* Analisis faktor penyebab utama (root cause)
* Rekomendasi tindakan praktis yang mudah dipahami tim non-teknis

---

## Team

* **Mitra**: TransTRACK
* **Project Manager**: Ulil
* **Backend Engineer**: Amirah
* **Frontend Engineer**: Marcel
* **Data Analyst**: Aisya
* **AI Engineer**: Ziza

---

## Table of Contents

1. Problem Statement
2. Success Metrics

   * Product Metrics
   * North Star Metrics
3. Product Requirements

   * Product Modules
4. Roadmap

---

## 1. Problem Statement

Manajer armada kesulitan mengubah data telematika mentah menjadi wawasan operasional yang strategis. Tidak tersedia metrik emisi harian yang kredibel, prediksi konsumsi yang andal, maupun peringatan dini atas insiden operasional kritis. Akibatnya, efisiensi operasional, pengendalian biaya BBM, dan pencapaian target emisi menjadi tidak optimal.

### Pain Point & Solution

| Problem                                    | Pain Point                                                                          | Solution                                                                       |
| ------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Tidak ada angka emisi harian yang kredibel | Perhitungan manual dari data mentah rentan error dan tidak konsisten                | Sistem estimasi emisi CO₂ harian otomatis dengan metrik standar (gCO₂/km)      |
| Sulit mendeteksi inefisiensi BBM           | Fuel loss, idle berlebih, dan gaya berkendara boros sulit dibedakan dari noise data | Deteksi anomali berbasis model untuk fuel theft, idle ekstrem, dan inefisiensi |
| Kesulitan merencanakan target reduksi      | Tidak ada prediksi tren emisi dan konsumsi                                          | Fitur forecasting emisi & BBM 7–30 hari                                        |
| Lambat dari deteksi ke perbaikan           | Laporan hanya data mentah tanpa insight                                             | Explainability & rekomendasi tindakan praktis                                  |

Analisis akar masalah divisualisasikan menggunakan pendekatan **Fishbone Analysis** berdasarkan major partner pain point.

---

## 2. Success Metrics

### 2.1 Product Metrics

| Category       | Metrics                  | Deskripsi                                                  | Target      |
| -------------- | ------------------------ | ---------------------------------------------------------- | ----------- |
| Kinerja Model  | MAE Estimasi Emisi       | Selisih absolut rata-rata antara prediksi dan nilai aktual | MAE < 15%   |
| Kinerja Model  | F1-Score Deteksi Anomali | Precision & Recall gabungan untuk anomali                  | F1 > 0.80   |
| Fungsionalitas | Kelengkapan Visualisasi  | Persentase metrik kunci tampil di dashboard                | 100%        |
| Fungsionalitas | Keberhasilan Notifikasi  | Anomali kritis memicu notifikasi                           | 100%        |
| Kinerja Sistem | Latensi Pemrosesan       | Waktu proses per kendaraan per hari                        | < 30 detik  |
| Stabilitas     | Batch Processing         | Proses data tanpa crash                                    | 100% sukses |

### 2.2 North Star Metrics

> Penurunan intensitas emisi CO₂ rata-rata armada (gCO₂/km) dalam periode operasional tertentu.

---

## 3. Product Requirements

### 3.1 Product Modules

| Module                          | Description                                            | Dependencies                | Priority     |
| ------------------------------- | ------------------------------------------------------ | --------------------------- | ------------ |
| Data Integration & Processing   | Integrasi API TransTRACK, cleansing & structuring data | API TransTRACK              | Must Have    |
| Emission Prediction Engine      | Estimasi emisi CO₂ & intensitas per kendaraan          | Data Integration            | Must Have    |
| Anomaly Detection Engine        | Deteksi fuel theft, idle ekstrem, inefisiensi          | Data Integration            | Must Have    |
| Dashboard & Visualization       | UI visual & interaktif                                 | Prediction & Anomaly Engine | Must Have    |
| Notification System             | Alert via Email / Telegram                             | Anomaly Engine              | Must Have    |
| Forecasting Engine              | Prediksi tren emisi & BBM                              | Emission Engine             | Nice to Have |
| Explainability & Recommendation | Insight penyebab & rekomendasi                         | Prediction & Detection      | Nice to Have |
| User & Fleet Management         | Manajemen user & armada                                | -                           | Nice to Have |

---

## 4. Roadmap

### 4.1 Milestone

| Phase                  | Duration |
| ---------------------- | -------- |
| Concept Presentation   | 1 week   |
| Design Presentation    | 1 week   |
| Development            | 9 weeks  |
| Ready to Quality Check | 1 week   |

---

## License

Internal MVP – TransTRACK
