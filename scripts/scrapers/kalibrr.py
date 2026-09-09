import requests
import json
from datetime import datetime
import pandas as pd
import os
import re

class KalibrrScraper:
    def __init__(self, keywords=["data engineer"]):
        
        self.keywords = keywords
        # self.build_id = "3EDBwuZJCrtpU2Eq5zsO-"    
        self.build_id = self.get_build_id()    
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.save_dir = "data/raw/Kalibrr"
    
    def get_build_id(self):
        try:
            res = requests.get("https://www.kalibrr.id/id-ID/home/te/data-engineer", headers=self.headers, timeout=10)
            res.raise_for_status()
            match = re.search(r'"buildId":"([^"]+)"', res.text)

            if match:
                build_id = match.group(1)
                return build_id
        except Exception as e:
            print(e)
        
        return "b9eTYtNV9E-1VCnb5ujsJ"

    def fetch_data(self):
        """
        Method untuk melakukan HTTP GET request ke URL Kalibrr
        """

        all_fetched = {}
        for keyword in self.keywords:
            print(f"[KALIBRR - {keyword.upper()}] Fetching API...")
            formatted_keyword = keyword.replace(" ","-").lower()

            url = f"https://www.kalibrr.id/_next/data/{self.build_id}/id-ID/home/te/{formatted_keyword}.json?param=te&param={formatted_keyword}"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            fetched = response.json()
            all_fetched[keyword] = fetched

        return all_fetched

    def extract_jobs(self, raw_data):
        """
        Method untuk mengambil data spesifik dari response JSON
        """
        
        extracted_data = []

        for keyword, data in raw_data.items():
            job_list = data.get("pageProps",{}).get("jobs",[])
            print(f"\n[KALIBRR - {keyword.upper()}] Mengekstrak {len(job_list)} pekerjaan...")

            for job in job_list:
                print(f"[KALIBRR - {keyword.upper()}]  -> {job.get('name')}")
                job_info = {
                    # 1. Identitas & Info Utama
                    "job_id"            : job.get("id"),
                    "search_keyword"    : keyword,
                    "title"             : job.get("name"),
                    "job_function"      : job.get("function"),         # Contoh: "IT and Software"
                    "employment_type"   : job.get("tenure"),           # Contoh: "Full time"
                    
                    # 2. Perusahaan
                    "company_name"      : job.get("companyName"),
                    "company_industry"  : job.get("companyInfo", {}).get("industry"),
                    "company_url"       : job.get("companyInfo", {}).get("url"),
                    
                    # 3. Lokasi & Tipe Kerja
                    "city"              : job.get("googleLocation", {}).get("addressComponents", {}).get("city"),
                    "region"            : job.get("googleLocation", {}).get("addressComponents", {}).get("region"),
                    "is_wfh"            : job.get("isWorkFromHome"),
                    "is_hybrid"         : job.get("isHybrid"),
                    "work_arrangement"  : "Remote" if job.get("isWorkFromHome") else ("Hybrid" if job.get("isHybrid") else "Onsite"),
                    
                    # 4. Syarat & Pengalaman
                    "education_level"   : job.get("educationLevel"),   # Enum mentah (nanti diolah di dbt)
                    "work_experience"   : job.get("workExperience"),   # Enum mentah
                    "open_for_freshgrad": job.get("isOpenToFreshGrads"),
                    
                    # 5. Gaji (Sering kosong/null, tapi wajib disiapkan tempatnya)
                    "base_salary"       : job.get("baseSalary"),
                    "max_salary"        : job.get("maximumSalary"),
                    "salary_currency"   : job.get("salaryCurrency"),
                    
                    # 6. Timestamps (Waktu)
                    "posted_at"         : job.get("createdAt"),
                    "deadline_at"       : job.get("applicationEndDate"),
                    
                    # 7. SKILLSET
                    "skills"            : [skill.get("sdsSkill", {}).get("name") for skill in job.get("jobSdsSkills", []) if skill.get("sdsSkill")]
                }

                extracted_data.append(job_info)
        
        return extracted_data
    
    def to_parquet(self,extracted_data):
        if not extracted_data:
            print("Data tidak ditemukan")
            return None

        df = pd.DataFrame(extracted_data)

        today = datetime.now().strftime("%Y-%m-%d")

        save_path = f"{self.save_dir}/kalibrr_jobs_{today}.parquet"
        os.makedirs(self.save_dir, exist_ok=True)

        df.to_parquet(save_path)
        # df.to_excel('test.xlsx')
        print(f"Data berhasil tersimpan di {save_path}")

        return df


    def main(self):
        print("Mulai scraping Kalibrr...")
        
        print("Fetching data...")
        raw_data = self.fetch_data()
        
        if not raw_data:
            print("Gagal mengambil data.")
            return

        print("Mengekstrak data pekerjaan...")
        jobs = self.extract_jobs(raw_data)

        print("Exporting to Parquet")
        df = self.to_parquet(jobs)
        
        print(f"Berhasil mengekstrak {len(jobs)} data pekerjaan!")
        

keywords = [
    "data engineer",
    "data analyst",
    "etl developer",
    "database admin",
    "data scientist",
    "data architect",
]

if __name__ == "__main__":
    scraper = KalibrrScraper(keywords)
    scraper.main()
