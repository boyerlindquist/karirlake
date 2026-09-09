import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app_data.db"))

STAGES_ACTIVE = [
    "Wishlist",
    "Applied",
    "Interview HR",
    "Interview User 1",
    "Interview User 2",
    "Offering"
]

STAGES_SUCCESS = [
    "Diterima"
]

STAGES_GHOSTED = [
    "Ghosted"
]

STAGES_REJECTED = [
    "Ditolak"
]

VALID_STAGES = STAGES_ACTIVE + STAGES_SUCCESS + STAGES_GHOSTED + STAGES_REJECTED

VALID_TEST_TYPES = [
    "Tanpa Tes",
    "Take-Home Project",
    "Live Coding Test",
    "Online Assessment (OA)",
    "System Design Test",
    "Psikotes"
]

from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_app_db():
    """Membuat tabel users dan saved_jobs jika belum ada, migrasi kolom test_type, dan seed demo data."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Tabel Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Tabel Saved Jobs (Application Tracker)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                standard_role TEXT,
                location_city TEXT,
                work_type TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                source_platform TEXT,
                company_url TEXT,
                job_url TEXT,
                skills TEXT,
                status TEXT DEFAULT 'Wishlist',
                test_type TEXT DEFAULT 'Tanpa Tes',
                notes TEXT,
                applied_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, job_title, company_name)
            )
        """)

        # Check and migrate test_type & last_stage columns if they don't exist
        cursor.execute("PRAGMA table_info(saved_jobs)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "test_type" not in columns:
            cursor.execute("ALTER TABLE saved_jobs ADD COLUMN test_type TEXT DEFAULT 'Tanpa Tes'")
        if "last_stage" not in columns:
            cursor.execute("ALTER TABLE saved_jobs ADD COLUMN last_stage TEXT DEFAULT 'Applied'")

        # Migrate legacy & verbose statuses to clean 9 stages
        cursor.execute("UPDATE saved_jobs SET status = 'Wishlist' WHERE status IN ('Saved', 'Wishlist (Belum Apply)')")
        cursor.execute("UPDATE saved_jobs SET status = 'Interview HR' WHERE status = 'HR Interview'")
        cursor.execute("UPDATE saved_jobs SET status = 'Interview User 1' WHERE status IN ('Technical Test', 'User Interview')")
        cursor.execute("UPDATE saved_jobs SET status = 'Diterima' WHERE status LIKE 'Diterima%'")
        cursor.execute("UPDATE saved_jobs SET status = 'Ghosted' WHERE status LIKE 'Ghosted%'")
        cursor.execute("UPDATE saved_jobs SET status = 'Ditolak' WHERE status LIKE 'Ditolak%' OR status LIKE 'Gagal Nego%'")
        cursor.execute("UPDATE saved_jobs SET status = 'Offering' WHERE status LIKE 'Offering%' OR status LIKE 'Tahap Offering%'")
        cursor.execute("UPDATE saved_jobs SET last_stage = status WHERE last_stage IS NULL OR last_stage = ''")
        cursor.execute("UPDATE saved_jobs SET last_stage = 'Applied' WHERE status = 'Wishlist'")

        # 3. Seed default demo account jika belum ada
        cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@karirlake.id",))
        user = cursor.fetchone()
        if not user:
            demo_pass = generate_password_hash("admin123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, ("Demo Engineer", "demo@karirlake.id", demo_pass))
            demo_user_id = cursor.lastrowid
        else:
            demo_user_id = user["id"]

        # Check if demo user has jobs; if not, seed realistic funnel jobs
        cursor.execute("SELECT COUNT(*) as count FROM saved_jobs WHERE user_id = ?", (demo_user_id,))
        if cursor.fetchone()["count"] == 0:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sample_jobs = [
                # 1. Wishlist / Belum Apply (3)
                (demo_user_id, "Senior Data Engineer (Lakehouse)", "Gojek (GoTo)", "Data Engineer",
                 "Jakarta", "Hybrid", 28000000, 42000000, "Glints", "https://gojek.com", "https://glints.com/id/jobs/demo-1",
                 "Python, Apache Spark, Iceberg, Kafka, GCP", "Wishlist", "Wishlist", "Tanpa Tes",
                 "Menunggu update sertifikasi GCP Data Engineer sebelum apply.", None),
                (demo_user_id, "Lead Analytics Engineer", "Traveloka", "Data Engineer",
                 "Tangerang Selatan", "Remote", 24000000, 36000000, "Glints", "https://traveloka.com", "https://glints.com/id/jobs/demo-2",
                 "dbt, BigQuery, Airflow, SQL, Data Modeling", "Wishlist", "Wishlist", "Take-Home Project",
                 "Portofolio dbt modeling sedang disesuaikan dengan e-commerce analytics.", None),
                (demo_user_id, "Staff MLOps Engineer", "Tokopedia", "Data Scientist",
                 "Jakarta Selatan", "Hybrid", 26000000, 38000000, "Kalibrr", "https://tokopedia.com", "https://kalibrr.com/jobs/demo-3",
                 "Kubeflow, MLflow, Docker, Python, AWS", "Wishlist", "Wishlist", "Tanpa Tes",
                 "Tandai dulu untuk apply awal bulan depan.", None),

                # 2. Applied / Screening CV (2)
                (demo_user_id, "Data Warehouse Specialist", "PT Bank Mandiri (Persero) Tbk", "Data Engineer",
                 "Jakarta Pusat", "Onsite", 18000000, 26000000, "Kalibrr", "https://bankmandiri.co.id", "https://kalibrr.com/jobs/demo-4",
                 "Oracle, SQL, ETL Informatica, Data Warehouse", "Applied", "Applied", "Online Assessment (OA)",
                 "Lamaran terkirim via portal karir Mandiri 2 hari lalu.", now_str),
                (demo_user_id, "Big Data Engineer", "Telkomsel", "Data Engineer",
                 "Jakarta Selatan", "Hybrid", 20000000, 30000000, "Glints", "https://telkomsel.com", "https://glints.com/id/jobs/demo-5",
                 "Hadoop, Hive, Spark, Kafka, Presto", "Applied", "Applied", "Tanpa Tes",
                 "Submit aplikasi lewat Kalibrr, menunggu kabar screening HR.", now_str),

                # 3. Gugur di Screening CV (2 Ditolak, 3 Ghosted)
                (demo_user_id, "Database Administrator (PostgreSQL)", "PT Indocyber Global Teknologi", "Database Administrator",
                 "Jakarta Barat", "Contractual", 12000000, 16000000, "Kalibrr", "https://indocyber.co.id", "https://kalibrr.com/jobs/demo-6",
                 "PostgreSQL, Linux, Performance Tuning, Replication", "Ditolak", "Applied", "Tanpa Tes",
                 "Budget gaji client tidak sesuai dengan kompensasi yang diminta.", now_str),
                (demo_user_id, "Junior Data Analyst", "Astra International", "Data Analyst",
                 "Jakarta Utara", "Full Time", 10000000, 14000000, "Glints", "https://astra.co.id", "https://glints.com/id/jobs/demo-7",
                 "SQL, Excel, Tableau, Power BI", "Ditolak", "Applied", "Psikotes",
                 "Ditolak screening CV karena mencari background industri otomotif.", now_str),
                (demo_user_id, "Data Infrastructure Architect", "Shopee Indonesia", "Data Architect",
                 "Jakarta", "Full Time", 35000000, 50000000, "Glints", "https://shopee.co.id", "https://glints.com/id/jobs/demo-8",
                 "ClickHouse, Trino, Flink, Kubernetes", "Ghosted", "Applied", "Tanpa Tes",
                 "Sudah 4 minggu tidak ada respon setelah apply.", now_str),
                (demo_user_id, "ETL Pipeline Developer", "Lion Parcel", "Data Engineer",
                 "Jakarta Barat", "Onsite", 14000000, 19000000, "Kalibrr", "https://lionparcel.com", "https://kalibrr.com/jobs/demo-9",
                 "Python, MySQL, Pentaho, Cron, Airflow", "Ghosted", "Applied", "Tanpa Tes",
                 "Status di platform masih submitted tanpa follow up.", now_str),
                (demo_user_id, "Business Intelligence Lead", "Sociolla (Social Bella)", "Data Analyst",
                 "Jakarta Barat", "Hybrid", 18000000, 25000000, "Glints", "https://sociolla.com", "https://glints.com/id/jobs/demo-10",
                 "Metabase, Google BigQuery, SQL, GA4", "Ghosted", "Applied", "Tanpa Tes",
                 "Tidak ada email balasan setelah 3 minggu.", now_str),

                # 4. Interview HR (2)
                (demo_user_id, "Senior Data Engineer (Fintech)", "DANA Indonesia", "Data Engineer",
                 "Jakarta Selatan", "Hybrid", 22000000, 32000000, "Glints", "https://dana.id", "https://glints.com/id/jobs/demo-11",
                 "Python, Spark, Kafka, AWS, Kubernetes", "Interview HR", "Interview HR", "Psikotes",
                 "Interview HR lancar, dijelaskan kultur tim Data Platform & ekspektasi.", now_str),
                (demo_user_id, "Data Platform Specialist", "Kredivo Group", "Data Engineer",
                 "Jakarta Pusat", "Hybrid", 21000000, 30000000, "Kalibrr", "https://kredivo.com", "https://kalibrr.com/jobs/demo-12",
                 "Spark Streaming, Airflow, Redshift, Python", "Interview HR", "Interview HR", "Online Assessment (OA)",
                 "Menunggu hasil evaluasi HR dan undangan interview user teknis.", now_str),

                # 5. Gugur di Interview HR (2 Ditolak, 2 Ghosted)
                (demo_user_id, "Cloud Data Architect", "Xendit", "Data Architect",
                 "Jakarta", "Remote", 30000000, 45000000, "Glints", "https://xendit.co", "https://glints.com/id/jobs/demo-13",
                 "AWS Data Lake, Terraform, Kafka, Snowflake", "Ditolak", "Interview HR", "Tanpa Tes",
                 "Kandidat internal diprioritaskan untuk posisi arsitek.", now_str),
                (demo_user_id, "Database Engineer Specialist", "LinkAja", "Database Administrator",
                 "Jakarta Selatan", "Hybrid", 16000000, 23000000, "Kalibrr", "https://linkaja.id", "https://kalibrr.com/jobs/demo-14",
                 "PostgreSQL, CockroachDB, High Availability", "Ditolak", "Interview HR", "Psikotes",
                 "Tidak cocok dengan ketersediaan jadwal on-call weekend.", now_str),
                (demo_user_id, "Data Analytics Specialist", "Tiket.com", "Data Analyst",
                 "Jakarta Pusat", "Hybrid", 17000000, 24000000, "Glints", "https://tiket.com", "https://glints.com/id/jobs/demo-15",
                 "SQL, Tableau, Looker Studio, Python", "Ghosted", "Interview HR", "Online Assessment (OA)",
                 "HR menjanjikan feedback dalam 5 hari kerja tapi tidak ada kabar.", now_str),
                (demo_user_id, "Machine Learning Engineer", "eFishery", "Data Scientist",
                 "Bandung", "Hybrid", 18000000, 27000000, "Kalibrr", "https://efishery.com", "https://kalibrr.com/jobs/demo-16",
                 "PyTorch, OpenCV, IoT Analytics, Python", "Ghosted", "Interview HR", "Tanpa Tes",
                 "Interview selesai, rekruter tidak merespon follow up email.", now_str),

                # 6. Interview User 1 / Teknis (2)
                (demo_user_id, "Big Data Engineer", "PT Bank Central Asia Tbk (BCA)", "Data Engineer",
                 "Jakarta Barat", "Onsite", 20000000, 28000000, "Kalibrr", "https://bca.co.id", "https://kalibrr.com/jobs/demo-17",
                 "Hadoop, Spark, Scala, Hive, Kafka", "Interview User 1", "Interview User 1", "Live Coding Test",
                 "Live coding SQL & Spark logic selama 60 menit dengan Tech Lead.", now_str),
                (demo_user_id, "Senior Data Pipeline Engineer", "Halodoc", "Data Engineer",
                 "Jakarta Selatan", "Hybrid", 23000000, 33000000, "Glints", "https://halodoc.com", "https://glints.com/id/jobs/demo-18",
                 "Python, Airflow, Snowflake, AWS Glue, dbt", "Interview User 1", "Interview User 1", "Take-Home Project",
                 "Take-home assignment ETL Lakehouse selesai dikumpulkan.", now_str),

                # 7. Gugur di Interview User 1 (1 Ditolak, 1 Ghosted)
                (demo_user_id, "Data Platform Engineer", "Ruangguru", "Data Engineer",
                 "Jakarta Selatan", "Remote", 19000000, 27000000, "Glints", "https://ruangguru.com", "https://glints.com/id/jobs/demo-19",
                 "GCP, Airflow, BigQuery, Kubernetes, Python", "Ditolak", "Interview User 1", "Live Coding Test",
                 "Live coding algoritma graf data dinilai kurang optimal.", now_str),
                (demo_user_id, "Senior Data Analyst (Growth)", "Bibit (PT Tumbuh Bersama)", "Data Analyst",
                 "Jakarta Selatan", "Hybrid", 18000000, 26000000, "Glints", "https://bibit.id", "https://glints.com/id/jobs/demo-20",
                 "Product Analytics, Amplitude, SQL, Python", "Ghosted", "Interview User 1", "Take-Home Project",
                 "Presentasi case study selesai, belum ada konfirmasi tahap user 2.", now_str),

                # 8. Interview User 2 / VP (1 Aktif, 1 Ditolak)
                (demo_user_id, "Principal Analytics Engineer", "Bank Jago", "Data Engineer",
                 "Jakarta Selatan", "Hybrid", 28000000, 40000000, "Glints", "https://jago.com", "https://glints.com/id/jobs/demo-21",
                 "dbt, Snowflake, Airflow, Data Governance, Python", "Interview User 2", "Interview User 2", "System Design Test",
                 "Interview final dengan Head of Data & VP Engineering hari Selasa.", now_str),
                (demo_user_id, "Data Architect - Core Banking", "PT Bank Danamon Indonesia Tbk", "Data Architect",
                 "Jakarta Selatan", "Onsite", 27000000, 38000000, "Kalibrr", "https://danamon.co.id", "https://kalibrr.com/jobs/demo-22",
                 "Enterprise Data Lake, Kafka, Mainframe, Oracle", "Ditolak", "Interview User 2", "System Design Test",
                 "User membutuhkan spesialisasi arsitektur perbankan syariah.", now_str),

                # 9. Offering (2 Aktif, 1 Ditolak)
                (demo_user_id, "Lead Data Engineer", "Blibli (PT Global Digital Niaga)", "Data Engineer",
                 "Jakarta Pusat", "Hybrid", 26000000, 37000000, "Kalibrr", "https://blibli.com", "https://kalibrr.com/jobs/demo-23",
                 "Apache Spark, Iceberg, Airflow, ClickHouse, Java", "Offering", "Offering", "System Design Test",
                 "Menerima draft offering letter Rp 33.000.000 + bonus tahunan. Sedang review klausul kontrak.", now_str),
                (demo_user_id, "Staff Data Platform Specialist", "Amartha", "Data Engineer",
                 "Jakarta Selatan", "Remote", 25000000, 35000000, "Glints", "https://amartha.com", "https://glints.com/id/jobs/demo-24",
                 "Python, GCP, BigQuery, Kafka, dbt", "Offering", "Offering", "Take-Home Project",
                 "Tahap negosiasi benefit remote allowance dan health insurance.", now_str),
                (demo_user_id, "Data Engineer Specialist", "Kopi Kenangan", "Data Engineer",
                 "Jakarta Selatan", "Full Time", 17000000, 23000000, "Glints", "https://kopikenangan.com", "https://glints.com/id/jobs/demo-25",
                 "SQL, Airflow, BigQuery, Python, Metabase", "Ditolak", "Offering", "Take-Home Project",
                 "Penawaran gaji akhir di bawah expected salary minimum, lamaran di-withdraw.", now_str),

                # 10. Diterima (2)
                (demo_user_id, "Senior Analytics & Lakehouse Engineer", "Bukalapak", "Data Engineer",
                 "Jakarta", "Hybrid", 25000000, 36000000, "Glints", "https://bukalapak.com", "https://glints.com/id/jobs/demo-26",
                 "DuckDB, dbt, Airflow, Snowflake, Python", "Diterima", "Offering", "Take-Home Project",
                 "OFFERING DITERIMA! Kontrak kerja ditandatangani. Onboarding tanggal 15.", now_str),
                (demo_user_id, "Data Engineer - Data Lakehouse", "Ajaib Investasi", "Data Engineer",
                 "Jakarta Selatan", "Remote", 24000000, 34000000, "Glints", "https://ajaib.co.id", "https://glints.com/id/jobs/demo-27",
                 "Apache Kafka, Trino, Python, ClickHouse, Docker", "Diterima", "Offering", "Live Coding Test",
                 "OFFERING DITERIMA! Sepakat paket kompensasi Rp 30.000.000 + ESOP.", now_str),
            ]

            cursor.executemany("""
                INSERT OR IGNORE INTO saved_jobs (
                    user_id, job_title, company_name, standard_role,
                    location_city, work_type, salary_min, salary_max, source_platform,
                    company_url, job_url, skills, status, last_stage, test_type, notes, applied_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_jobs)
        
        conn.commit()

# --- USER AUTHENTICATION QUERIES ---

def create_user(username, email, password):
    """Mendaftarkan akun baru."""
    password_hash = generate_password_hash(password)
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username.strip(), email.strip().lower(), password_hash))
            conn.commit()
            return {"success": True, "user_id": cursor.lastrowid}
    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "email" in msg:
            return {"success": False, "error": "Email sudah terdaftar. Silakan login."}
        elif "username" in msg:
            return {"success": False, "error": "Username sudah digunakan, pilih nama lain."}
        return {"success": False, "error": "Pendaftaran gagal karena data duplikat."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_user(email, password):
    """Verifikasi email dan password untuk login."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        user = cursor.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        return None

def get_user_by_id(user_id):
    """Mengambil data user berdasarkan ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None

# --- SAVED JOBS & PROGRESS TRACKER QUERIES ---

def get_saved_jobs(user_id, status_filter=None):
    """Mengambil daftar lowongan tersimpan milik user tertentu."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT * FROM saved_jobs
            WHERE user_id = ?
        """
        params = [user_id]
        if status_filter and status_filter != "All":
            if status_filter == "Wishlist":
                query += " AND status = 'Wishlist'"
            elif status_filter == "Active":
                query += " AND status IN ('Applied', 'Interview HR', 'Interview User 1', 'Interview User 2', 'Offering')"
            elif status_filter == "Ghosted":
                query += " AND status LIKE 'Ghosted%'"
            elif status_filter == "Rejected":
                query += " AND status LIKE 'Ditolak%'"
            elif status_filter == "Success":
                query += " AND status LIKE 'Diterima%'"
            else:
                query += " AND status = ?"
                params.append(status_filter)
        
        query += " ORDER BY updated_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            item = dict(r)
            skills_raw = item.get("skills") or ""
            item["skills_list"] = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
            result.append(item)
        return result

def get_user_saved_keys(user_id):
    """Mengambil set kombinasi unik (job_title, company_name) lowongan yang tersimpan."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT job_title, company_name FROM saved_jobs WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return {f"{r['job_title']}||{r['company_name']}" for r in rows}

def save_job(user_id, job_data):
    """Menyimpan lowongan baru dari Job Explorer ke Saved Jobs."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            skills_str = ", ".join(job_data.get("skills", [])) if isinstance(job_data.get("skills"), list) else job_data.get("skills", "")
            
            cursor.execute("""
                INSERT INTO saved_jobs (
                    user_id, job_title, company_name, standard_role,
                    location_city, work_type, salary_min, salary_max, source_platform,
                    company_url, job_url, skills, status, test_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Wishlist', 'Tanpa Tes', ?)
            """, (
                user_id,
                job_data.get("job_title", "Untitled"),
                job_data.get("company_name", "Perusahaan"),
                job_data.get("standard_role", "Other"),
                job_data.get("location_city", "Indonesia"),
                job_data.get("work_type", "Full Time"),
                job_data.get("salary_min"),
                job_data.get("salary_max"),
                job_data.get("source_platform", "Portal"),
                job_data.get("company_url"),
                job_data.get("job_url"),
                skills_str,
                job_data.get("notes", "")
            ))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Lowongan ini sudah pernah Anda simpan sebelumnya."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_saved_job_status(user_id, job_id, new_status):
    """Memperbarui tahapan status lamaran."""
    if new_status not in VALID_STAGES:
        return {"success": False, "error": f"Status '{new_status}' tidak valid."}
    
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ambil status dan last_stage saat ini
        cursor.execute("SELECT status, last_stage FROM saved_jobs WHERE id = ? AND user_id = ?", (job_id, user_id))
        curr = cursor.fetchone()
        if not curr:
            return {"success": False, "error": "Lowongan tidak ditemukan."}
        
        current_status = curr["status"]
        current_last_stage = curr["last_stage"] or "Applied"

        if new_status in ["Ghosted", "Ditolak"]:
            # Jika sebelumnya bukan Ghosted/Ditolak/Wishlist, simpan status tersebut sebagai last_stage
            if current_status not in ["Ghosted", "Ditolak", "Wishlist"]:
                new_last_stage = current_status
            else:
                new_last_stage = current_last_stage
            
            cursor.execute("""
                UPDATE saved_jobs 
                SET status = ?, last_stage = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (new_status, new_last_stage, now_str, job_id, user_id))
        else:
            new_last_stage = new_status
            if new_status != "Wishlist":
                cursor.execute("""
                    UPDATE saved_jobs 
                    SET status = ?, last_stage = ?, updated_at = ?, applied_at = COALESCE(applied_at, ?)
                    WHERE id = ? AND user_id = ?
                """, (new_status, new_last_stage, now_str, now_str, job_id, user_id))
            else:
                cursor.execute("""
                    UPDATE saved_jobs 
                    SET status = ?, last_stage = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                """, (new_status, new_last_stage, now_str, job_id, user_id))
        
        conn.commit()
        return {"success": cursor.rowcount > 0}

def update_saved_job_test_type(user_id, job_id, test_type):
    """Memperbarui keterangan jenis tes teknis/assessment."""
    if test_type not in VALID_TEST_TYPES:
        return {"success": False, "error": f"Tipe tes '{test_type}' tidak valid."}
    
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE saved_jobs 
            SET test_type = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (test_type, now_str, job_id, user_id))
        conn.commit()
        return {"success": cursor.rowcount > 0}

def update_saved_job_notes(user_id, job_id, notes):
    """Menyimpan catatan wawancara atau persiapan pribadi."""
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE saved_jobs 
            SET notes = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (notes, now_str, job_id, user_id))
        conn.commit()
        return {"success": cursor.rowcount > 0}

def delete_saved_job(user_id, job_id):
    """Menghapus lowongan dari tracker."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_jobs WHERE id = ? AND user_id = ?", (job_id, user_id))
        conn.commit()
        return {"success": cursor.rowcount > 0}

def get_funnel_stats(user_id):
    """Menghitung metrik ringkasan dan data konversi bersih tanpa node in-between."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, test_type, last_stage 
            FROM saved_jobs 
            WHERE user_id = ?
        """, (user_id,))
        jobs = cursor.fetchall()
        
        total_saved = len(jobs)
        status_counts = {}
        test_counts = {}
        for j in jobs:
            s = j["status"]
            t = j["test_type"]
            status_counts[s] = status_counts.get(s, 0) + 1
            if t and t != "Tanpa Tes":
                test_counts[t] = test_counts.get(t, 0) + 1

        c_wishlist = status_counts.get("Wishlist", 0)
        c_applied = status_counts.get("Applied", 0)
        c_hr = status_counts.get("Interview HR", 0)
        c_user1 = status_counts.get("Interview User 1", 0)
        c_user2 = status_counts.get("Interview User 2", 0)
        c_offering = status_counts.get("Offering", 0)
        c_accepted = status_counts.get("Diterima", 0)
        c_ghosted = status_counts.get("Ghosted", 0)
        c_rejected = status_counts.get("Ditolak", 0)

        total_submitted = total_saved - c_wishlist
        total_interviews = c_hr + c_user1 + c_user2
        total_tests = sum(test_counts.values())

        # Build Sankey Links
        # Link map: (source, target) -> count
        links = {}
        def add_link(source, target, weight=1):
            if weight <= 0:
                return
            key = (source, target)
            links[key] = links.get(key, 0) + weight

        # Rank definition for pipeline progression
        STAGE_RANKS = {
            "Applied": 1,
            "Interview HR": 2,
            "Interview User 1": 3,
            "Interview User 2": 4,
            "Offering": 5,
            "Diterima": 6
        }

        # Stage display names
        STAGE_NAMES = {
            1: "Applied",
            2: "Interview HR",
            3: "Interview User 1",
            4: "Interview User 2",
            5: "Tahap Offering",
            6: "Diterima"
        }

        advanced_past_apply = 0

        for j in jobs:
            s = j["status"]
            last = j["last_stage"] or "Applied"

            if s == "Wishlist":
                add_link("Semua Loker Tersimpan", "Belum Apply", 1)
                continue

            # Every applied job flows from Semua Loker Tersimpan -> Applied
            add_link("Semua Loker Tersimpan", "Applied", 1)

            # Determine maximum stage reached
            if s in ["Ghosted", "Ditolak"]:
                terminal_node = s
                max_rank = STAGE_RANKS.get(last, 1)
            else:
                terminal_node = None
                max_rank = STAGE_RANKS.get(s, 1)

            if max_rank >= 2:
                advanced_past_apply += 1

            # Progression through stages
            for rank in range(1, max_rank):
                src_name = STAGE_NAMES[rank]
                tgt_name = STAGE_NAMES[rank + 1]
                add_link(src_name, tgt_name, 1)

            # If terminated at this stage with Ghosted or Ditolak
            if terminal_node:
                drop_from = STAGE_NAMES[max_rank]
                STAGE_SHORT_LABEL = {
                    1: "CV",
                    2: "HR",
                    3: "User 1",
                    4: "User 2",
                    5: "Offer"
                }
                stage_label = STAGE_SHORT_LABEL.get(max_rank, "")
                term_name = f"{terminal_node} ({stage_label})" if stage_label else terminal_node
                add_link(drop_from, term_name, 1)

        sankey_data = [[src, tgt, count] for (src, tgt), count in links.items()]

        response_rate = round(advanced_past_apply / total_submitted * 100, 1) if total_submitted > 0 else 0

        return {
            "scorecards": {
                "total_saved": total_saved,
                "wishlist": c_wishlist,
                "applied": total_submitted,
                "interviews": total_interviews,
                "tests": total_tests,
                "offering": c_offering,
                "accepted": c_accepted,
                "ghosted": c_ghosted,
                "rejected": c_rejected,
                "response_rate": response_rate
            },
            "counts": status_counts,
            "test_counts": test_counts,
            "sankey_data": sankey_data
        }
