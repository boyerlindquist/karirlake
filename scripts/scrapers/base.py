from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os

class BaseScraper:
    # 1. Constructor: Fungsi yang otomatis jalan pas class ini dipanggil
    def __init__(self):
        print("Membuka browser Chrome...")
        # 'self' itu ibarat tas ransel. Kita simpan drivernya di dalam 'self'
        # biar bisa diakses sama fungsi-fungsi lain di class ini.
        self.driver = self._setup_driver()
        
    # 2. Method (Fungsi): Diawali dengan underscore (_) tandanya ini fungsi internal
    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Jalan di background tanpa UI
        chrome_options.add_argument("--no-sandbox") # Wajib untuk Linux/WSL/Docker
        chrome_options.add_argument("--disable-dev-shm-usage") # Cegah error memory
        chrome_options.add_argument("--window-size=1920,1080")
        
        # --- TAMBAHAN CAMOUFLAGE ANTI-BOT ---
        # 1. Hapus tulisan "Chrome is being controlled by automated test software"
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # 2. Matiin flag Automation di internal Chrome
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 3. Hapus KTP Robot (navigator.webdriver) sebelum halaman di-load
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        return driver
        
    # 3. Utility Method: Fungsi umum yang bakal dipakai semua scraper
    def save_to_parquet(self, df: pd.DataFrame, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_parquet(file_path, index=False)
        print(f"Data berhasil disimpan ke {file_path}")

    # 4. Cleanup Method: Wajib dipanggil biar RAM nggak bocor
    def close(self):
        if self.driver:
            self.driver.quit()
            print("Browser Chrome ditutup.")

    # 5. Helper Method: Buat nyomot cookies dari browser
    def get_selenium_cookies(self):
        """
        Ngambil cookies dari Selenium dan ngubah ke format dictionary
        biar gampang dipakai sama library 'requests'.
        """
        selenium_cookies = self.driver.get_cookies()
        
        # Ubah formatnya jadi {'nama_cookie': 'value_cookie'}
        cookies_dict = {}
        for cookie in selenium_cookies:
            cookies_dict[cookie['name']] = cookie['value']
            
        return cookies_dict

    def get_user_agent(self):
        # Minta Chrome ngasih tau User-Agent aslinya dia
        return self.driver.execute_script("return navigator.userAgent;")
