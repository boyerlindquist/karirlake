# Data Pipeline Standardization Plan

Dokumen perencanaan teknis untuk standardisasi dan pembersihan data (*data cleansing & normalization*) pada pipeline analitik KarirLake (Glints & Kalibrr) sebelum disajikan ke Gold Data Marts dan Web Dashboard.

---

## 1. Ringkasan & Target Arsitektur

Saat ini terdapat ketidaksinkronan data antar-sumber (*schema & semantic drift*):
1. Kolom `work_type` mencampuradukkan **skema lokasi kerja** (Onsite/Hybrid/Remote) dengan **tipe kontrak** (Full-time/Contract).
2. `education_level` pada Kalibrr menyimpan **kode enum internal** (`550`, `200`, `450`), sedangkan Glints menyimpan string (`BACHELOR_DEGREE`).
3. `min_experience` bertipe `VARCHAR` dan Kalibrr menggunakan kode tier (`100`, `200`), sedangkan Glints menggunakan angka tahun (`0`, `1`, `3`).
4. `skills` memiliki duplikasi casing, singkatan vs kepanjangan (`ETL` vs `Extract, Transform, Load (ETL)`), serta polusi soft-skills (`Teamwork`).
5. `location_city` mencampuradukkan tingkat kecamatan (`Setiabudi`, `Tanah Abang`), bahasa Inggris (`South Jakarta`), dan nama kota/kabupaten.
6. `salary` memiliki entitas dummy selisih 1 rupiah (`1000000` vs `1000001`) dan asimetri nilai null.

### Rekomendasi Alur Layer dbt:
```
Bronze (Raw Parquet)
   └── Silver 1: Staging (stg_glints_jobs, stg_kalibrr_jobs) -> Type casting & field extraction
          └── Silver 2: Intermediate (int_all_jobs_cleaned) -> Normalization, mapping, standard roles
                 └── Gold: Marts (mart_salary_insights, mart_top_skills, dll.)
```

---

## 2. Checklist Eksekusi Standardisasi

### A. Skema Kerja vs. Tipe Kontrak
- [ ] **Pemisahan Kolom di Staging / Intermediate**:
  - Kolom 1: `work_arrangement` (`VARCHAR`): Skema fisik kehadiran kerja.
  - Kolom 2: `employment_type` (`VARCHAR`): Status ikatan hubungan kerja.
- [ ] **Standardisasi `work_arrangement`**:
  - `ONSITE` / `On-site` / `WFO` -> `'Onsite'`
  - `HYBRID` / `Hybrid` -> `'Hybrid'`
  - `REMOTE` / `Remote` / `WFH` -> `'Remote'`
  - Null / Kosong -> `'Not Specified'`
- [ ] **Standardisasi `employment_type`**:
  - `Full time` / `FULL_TIME` / `Permanen` -> `'Full-time'`
  - `Contractual` / `CONTRACT` / `Kontrak` -> `'Contract'`
  - `Part time` / `PART_TIME` -> `'Part-time'`
  - `Internship` / `Magang` -> `'Internship'`
  - `Freelance` / `Proyek` -> `'Freelance'`
  - Null / Kosong -> `'Not Specified'`
- [ ] **Update Mart Terkait**:
  - Perbarui `mart_work_arrangement_trends.sql` agar melakukan `GROUP BY` pada `work_arrangement` murni (bukan `work_type`).
  - (Opsional) Buat `mart_employment_type_trends.sql` jika ingin menampilkan distribusi tipe kontrak.

---

### B. Tingkat Pendidikan (`education_level`)
- [ ] **Mapping Enum Kalibrr di `stg_kalibrr_jobs.sql`**:
  ```sql
  CASE CAST(education_level AS VARCHAR)
      WHEN '550' THEN 'Bachelor'
      WHEN '500' THEN 'Bachelor'
      WHEN '450' THEN 'Diploma'
      WHEN '400' THEN 'Diploma'
      WHEN '200' THEN 'High School'
      WHEN '100' THEN 'High School'
      WHEN '600' THEN 'Master'
      WHEN '700' THEN 'Doctorate'
      ELSE COALESCE(education_level, 'Not Specified')
  END AS education_level
  ```
- [ ] **Normalisasi Glints di `stg_glints_jobs.sql`**:
  ```sql
  CASE UPPER(education_level)
      WHEN 'BACHELOR_DEGREE' THEN 'Bachelor'
      WHEN 'DIPLOMA'         THEN 'Diploma'
      WHEN 'HIGH_SCHOOL'     THEN 'High School'
      WHEN 'MASTER_DEGREE'   THEN 'Master'
      WHEN 'DOCTORATE'       THEN 'Doctorate'
      ELSE COALESCE(education_level, 'Not Specified')
  END AS education_level
  ```
- [ ] **Nilai Standar Kanonikal**:
  `['High School', 'Diploma', 'Bachelor', 'Master', 'Doctorate', 'Not Specified']`

---

### C. Pengalaman Kerja (`min_experience`)
- [ ] **Konversi ke Angka Numerik (`min_experience_years` INTEGER)**:
  - Glints:
    ```sql
    TRY_CAST(min_experience AS INTEGER) AS min_experience_years
    ```
  - Kalibrr:
    ```sql
    CASE CAST(work_experience AS VARCHAR)
        WHEN '100' THEN 0   -- Fresh Graduate / Kurang dari 1 tahun
        WHEN '200' THEN 1   -- 1 - 3 tahun (pilih batas bawah)
        WHEN '300' THEN 3   -- 3 - 5 tahun
        WHEN '400' THEN 5   -- 5+ tahun
        ELSE TRY_CAST(work_experience AS INTEGER)
    END AS min_experience_years
    ```
- [ ] **Pembuatan Kolom Kategori (`experience_tier` VARCHAR)**:
  - `< 1 tahun`: Fresh Graduate
  - `1 - 2 tahun`: Junior
  - `3 - 4 tahun`: Mid-Level
  - `5+ tahun`: Senior

---

### D. Keahlian & Keterampilan (`skills`)
- [ ] **Deduplikasi Casing & Whitespace**:
  - Trim dan kapitalisasi judul (Title Case / Upper Case standar).
- [ ] **Penyatuan Sinonim & Akronim Teknis**:
  - `Extract, Transform, Load (ETL)` -> `ETL`
  - `Amazon Web Services (AWS)` / `Amazon Web Services` -> `AWS`
  - `Google Cloud Platform` -> `GCP`
  - `Data analysis` / `Data Analytics` / `Analytical Skills` -> `Data Analysis`
  - `Microsoft SQL Server` / `MS SQL Server` -> `SQL Server`
  - `Microsoft Excel` / `MS Excel` -> `Excel`
  - `Microsoft Power BI` -> `Power BI`
- [ ] **Pemisahan Dimensi Skill**:
  - Filter atau beri tag untuk memisahkan **Hard Skills / Tools** (`Python`, `SQL`, `dbt`, `Airflow`, `Tableau`) dari **Soft Skills** (`Teamwork`, `Critical Thinking`, `Communication`).
  - Bisa diimplementasikan via dbt seed: `seeds/seed_skills_taxonomy.csv` (`raw_skill`, `canonical_skill`, `skill_category`).

---

### E. Lokasi & Wilayah (`location_city` & `location_province`)
- [ ] **Penyatuan Granularitas Jakarta**:
  - Sub-district/Kecamatan & Bahasa Inggris:
    - `Setiabudi`, `Kebayoran Baru`, `Kebayoran Lama`, `Tebet`, `Mampang Prapatan`, `Pasar Minggu`, `Pesanggrahan`, `South Jakarta` -> `Jakarta Selatan`
    - `Tanah Abang`, `Gambir`, `Menteng`, `Central Jakarta` -> `Jakarta Pusat`
    - `Penjaringan`, `Tanjung Priok`, `North Jakarta` -> `Jakarta Utara`
    - `Kebon Jeruk`, `Kembangan`, `West Jakarta` -> `Jakarta Barat`
    - `East Jakarta` -> `Jakarta Timur`
    - Jika hanya `Jakarta` -> Tetap `Jakarta`
- [ ] **Penyatuan Wilayah Lain**:
  - `Serpong` -> `Tangerang Selatan`
  - `Kapanewon Gamping`, `Kapanewon Depok` -> `Sleman` (atau kelompokkan ke `Yogyakarta`)
  - `Genteng` -> `Surabaya`
- [ ] **Kolom Baru `location_province`**:
  - `Jakarta Selatan`, `Jakarta Pusat`, `Jakarta Utara`, `Jakarta Barat`, `Jakarta Timur` -> `DKI Jakarta`
  - `Tangerang`, `Tangerang Selatan` -> `Banten`
  - `Sleman`, `Bantul`, `Yogyakarta` -> `DI Yogyakarta`
  - `Surabaya`, `Malang` -> `Jawa Timur`
  - `Bandung` -> `Jawa Barat`

---

### F. Gaji & Kompensasi (`salary_min`, `salary_max`, `salary_currency`)
- [ ] **Pembersihan Anomali Dummy Step 1 Rupiah**:
  - Jika `salary_max - salary_min <= 1` dan keduanya tidak null:
    Set `salary_max = salary_min` (merupakan gaji tetap/flat, bukan range).
- [ ] **Sanity Check Range**:
  - Jika `salary_min > salary_max`: Tukar posisi keduanya.
- [ ] **Penanganan Null Asimetris**:
  - Buat kolom terhitung `salary_mid`:
    ```sql
    CASE 
        WHEN salary_min IS NOT NULL AND salary_max IS NOT NULL THEN (salary_min + salary_max) / 2
        WHEN salary_min IS NOT NULL THEN salary_min
        WHEN salary_max IS NOT NULL THEN salary_max
        ELSE NULL
    END AS salary_mid
    ```
- [ ] **Flag Ketersediaan Gaji**:
  - `has_disclosed_salary` (`BOOLEAN`): `salary_min IS NOT NULL OR salary_max IS NOT NULL`
- [ ] **Standardisasi Mata Uang**:
  - Pastikan `salary_currency` default `'IDR'` dan uppercase.

---

### G. Klasifikasi Peran (`standard_role`) & Senioritas
- [ ] **Urutan Evaluasi Role (Specific to Generic)**:
  - Urutkan `CASE WHEN` agar role spesifik dievaluasi terlebih dahulu sebelum role umum:
    1. `Data Architect` (Cek arsitektur lebih dahulu)
    2. `Database Administrator` (DBA)
    3. `Data Scientist / ML Engineer`
    4. `Data Engineer`
    5. `Data Analyst / BI`
- [ ] **Ekstraksi Tingkat Senioritas (`seniority_level`)**:
  - Deteksi dari `job_title`:
    - `Lead`, `Head`, `Principal`, `VP`, `Manager`, `Director` -> `'Lead / Executive'`
    - `Senior`, `Sr.`, `Sr` -> `'Senior'`
    - `Junior`, `Jr.`, `Jr`, `Associate`, `Intern` -> `'Junior / Entry'`
    - Sisanya -> `'Mid-Level'`

---

## 3. Matriks Transformasi Skema

| Kolom Input | Transformasi Logis | Kolom Output Target | Tipe Data Target |
| :--- | :--- | :--- | :--- |
| `work_type` (Glints) | Onsite/Hybrid/Remote classification | `work_arrangement` | `VARCHAR` |
| `employment_type` (Kalibrr) | Full-time/Contract classification | `employment_type` | `VARCHAR` |
| `education_level` | Mapping enum Kalibrr & Glints string | `education_level` | `VARCHAR` |
| `min_experience` | Ekstraksi integer tahun | `min_experience_years` | `INTEGER` |
| `min_experience` | Pengelompokan tier | `experience_tier` | `VARCHAR` |
| `city` / `location_city` | Normalisasi nama kota & kecamatan | `location_city` | `VARCHAR` |
| `city` / `location_city` | Mapping provinsi | `location_province` | `VARCHAR` |
| `salary_min` & `salary_max` | Dummy 1 IDR fix & swap sanity | `salary_min`, `salary_max` | `BIGINT` |
| `salary_min` & `salary_max` | Rata-rata tengah | `salary_mid` | `BIGINT` |
| `skills` (Array) | Lower-trim, mapping synonym & dedupe | `skills` | `VARCHAR[]` |
| `job_title` | Priority regex classification | `standard_role` | `VARCHAR` |
| `job_title` | Keyword seniority parsing | `seniority_level` | `VARCHAR` |

---

## 4. Rencana Validasi Data Quality (Soda & dbt Tests)

Setelah pipeline dbt diperbarui oleh developer, tambahkan checks berikut pada `soda/checks_gold.yml` atau `schema.yml`:

1. **Check `work_arrangement`**:
   - `invalid_count(work_arrangement) = 0` dengan list valid: `['Onsite', 'Hybrid', 'Remote', 'Not Specified']`.
2. **Check `education_level`**:
   - Tidak boleh ada nilai angka/enum mentah (`550`, `200`, `450`).
3. **Check `salary`**:
   - `salary_max >= salary_min` untuk semua baris yang gajinya terisi.
   - `salary_min > 0`.
4. **Check `location_city`**:
   - Pastikan Setiabudi, Tanah Abang, Kebayoran Baru sudah teragregasi ke `Jakarta Selatan` / `Jakarta Pusat`.

---
*Dokumen ini dibuat sebagai panduan kerja dan tracking standardisasi data pipeline KarirLake.*
