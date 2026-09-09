import requests
import json
from datetime import datetime
import pandas as pd
import os

class GlintsScraper:
    def __init__(self, keywords = ["data engineer"]):
        self.keywords = keywords
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.save_dir = "data/raw/Glints"
        self.url = "https://glints.com/api/v2-alc/graphql?op=searchJobsV3"
        self.query_string = "query searchJobsV3($data: JobSearchConditionInput!) {\n  searchJobsV3(data: $data) {\n    jobsInPage {\n      id\n      title\n      workArrangementOption\n      status\n      createdAt\n      updatedAt\n      isHot\n      isApplied\n      shouldShowSalary\n      educationLevel\n      type\n      fraudReportFlag\n      company {\n        ...CompanyFields\n        __typename\n      }\n      citySubDivision {\n        id\n        name\n        __typename\n      }\n      city {\n        ...CityFields\n        __typename\n      }\n      country {\n        ...CountryFields\n        __typename\n      }\n      salaries {\n        ...SalaryFields\n        __typename\n      }\n      location {\n        ...LocationFields\n        __typename\n      }\n      minYearsOfExperience\n      maxYearsOfExperience\n      source\n      jobSource\n      type\n      hierarchicalJobCategory {\n        id\n        level\n        name\n        children {\n          name\n          level\n          id\n          __typename\n        }\n        parents {\n          id\n          level\n          name\n          __typename\n        }\n        __typename\n      }\n      skills {\n        skill {\n          id\n          name\n          __typename\n        }\n        mustHave\n        __typename\n      }\n      traceInfo\n      __typename\n    }\n    expInfo\n    hasMore\n    __typename\n  }\n}\n\nfragment CompanyFields on Company {\n  id\n  name\n  brandName\n  logo\n  status\n  isVIP\n  IndustryId\n  industry {\n    id\n    name\n    __typename\n  }\n  verificationTier {\n    type\n    userName\n    __typename\n  }\n  __typename\n}\n\nfragment CityFields on City {\n  id\n  name\n  __typename\n}\n\nfragment CountryFields on Country {\n  code\n  name\n  __typename\n}\n\nfragment SalaryFields on JobSalary {\n  id\n  salaryType\n  salaryMode\n  maxAmount\n  minAmount\n  CurrencyCode\n  __typename\n}\n\nfragment LocationFields on HierarchicalLocation {\n  id\n  name\n  administrativeLevelName\n  formattedName\n  level\n  slug\n  latitude\n  longitude\n  parents {\n    id\n    name\n    administrativeLevelName\n    formattedName\n    level\n    slug\n    CountryCode: countryCode\n    parents {\n      level\n      formattedName\n      slug\n      __typename\n    }\n    __typename\n  }\n  __typename\n}"

        self.payload = {
            "operationName" : "searchJobsV3",
            "query"         : self.query_string,
            "variables"     : {
                "data"          : {
                    "CountryCode"           : "ID",
                    "SearchTerm"            : None,
                    "includeExternalJobs"   : True,
                    "page"                  : 1,
                    "pageSize"              : 300,
                }
            }
        }

    def fetch_data(self):
        all_fetched = {}
        for keyword in self.keywords:
            print(f"[GLINTS - {keyword.upper()}] Fetching API...")
            self.payload["variables"]["data"]["SearchTerm"] = keyword

            response = requests.post(self.url,json=self.payload, headers = self.headers)
            response.raise_for_status()
            fetched = response.json()

            all_fetched[keyword] = fetched
        
        return all_fetched
    
    def extract_jobs(self, raw_data):
        extracted_data = []

        for keyword, data in raw_data.items():
            job_list = data.get("data",{}).get("searchJobsV3",{}).get("jobsInPage",[])
            print(f"\n[GLINTS - {keyword.upper()}] Mengekstrak {len(job_list)} pekerjaan...")

            for job in job_list:
                print(f"[GLINTS - {keyword.upper()}]  -> {job.get('title')}")
                salaries = job.get("salaries", [])
                salary_data = salaries[0] if salaries else {}

                # Tarik aman dari resiko NoneType
                company = job.get("company") or {}
                industry = company.get("industry") or {}
                location = job.get("location") or {}
                country = job.get("country") or {}

                job_info = {
                    "job_id"            : job.get("id"),
                    "search_keyword"    : keyword,
                    "job_title"         : job.get("title"),
                    
                    "company_name"      : company.get("name"),
                    "company_industry"  : industry.get("name"),
                    "company_url"       : None, # API Glints nggak ngasih info ini
                    
                    "city"              : location.get("name"),
                    "country"           : country.get("name"),
                    "employment_type"   : job.get("type"),
                    "work_arrangement"  : job.get("workArrangementOption"),
                    "work_type"         : job.get("workArrangementOption"),
                    
                    "salary_min"        : salary_data.get("minAmount"),
                    "salary_max"        : salary_data.get("maxAmount"),
                    "currency"          : salary_data.get("CurrencyCode"),
                    
                    "education_level"   : job.get("educationLevel"),
                    "min_experience"    : job.get("minYearsOfExperience"),
                    
                    "posted_at"         : job.get("createdAt"),
                    "deadline_at"       : None, # API Glints nggak ngasih deadline yang jelas
                    
                    "skills"            : [s.get("skill", {}).get("name") for s in job.get("skills", []) if s.get("skill")]
                }
                
                extracted_data.append(job_info)

        return extracted_data

    def to_parquet(self,extracted_data):
        if not extracted_data:
            print("Data tidak ditemukan")
            return None

        df = pd.DataFrame(extracted_data)

        today = datetime.now().strftime("%Y-%m-%d")

        save_path = f"{self.save_dir}/glints_jobs_{today}.parquet"
        os.makedirs(self.save_dir, exist_ok=True)

        df.to_parquet(save_path)
        # df.to_excel('testz.xlsx')
        print(f"Data berhasil tersimpan di {save_path}")

        return df

    def main(self):
        raw_data = self.fetch_data()

        if not raw_data:
            print('gagal mengambil data')
            return
        jobs = self.extract_jobs(raw_data)
        df = self.to_parquet(jobs)

keywords = [
    "data engineer",
    "data analyst",
    "etl developer",
    "database admin",
    "data scientist",
    "data architect",
    # 'lab analyst icp'
]
if __name__ == "__main__":
    scraper = GlintsScraper(keywords)
    scraper.main()