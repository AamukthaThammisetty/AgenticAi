from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller
import concurrent.futures

chromedriver_autoinstaller.install() 
from bs4 import BeautifulSoup
import time

def fetch_linkedin(keyword, location):
    try:

        chromedriver_autoinstaller.install()
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--lang=en-IN")
        options.add_argument("accept-language=en-IN,en;q=0.9")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"Failed to initialize with autoinstaller: {e}")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        results = []
        url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        print(f"Fetching LinkedIn people from: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "base-card")))
        
        try:
            dismiss_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal__dismiss")))
            dismiss_button.click()
            time.sleep(1)
        except Exception as e:
            print("No login popup or couldn't dismiss")

        print("Scrolling to load more peoples...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            try:
                dismiss_button = driver.find_element(By.CSS_SELECTOR, "button.modal__dismiss")
                dismiss_button.click()
            except:
                pass
                
            print(f"Scroll {i+1}/5 completed")
            
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        people = soup.find_all("div", class_="base-card")
        
        total_people = len(people)
        print(f"Total LinkedIn people found: {total_people}")
        
        for job in people[:200]:
            try:
                title = job.find("h3", class_="base-search-card__title")
                company = job.find("h4", class_="base-search-card__subtitle")
                job_location = job.find("span", class_="job-search-card__location")
                link = job.find("a", class_="base-card__full-link")
                
                job_data = {
                    "title": title.text.strip() if title else "N/A",
                    "company": company.text.strip() if company else "N/A",
                    "location": job_location.text.strip() if job_location else "N/A",
                    "link": link["href"] if link and link.has_attr("href") else "N/A",
                    "platform": "LinkedIn"
                }
                results.append(job_data)
            except Exception as e:
                print(f"Error parsing job: {e}")
        
    except Exception as e:
        print(f"LinkedIn scraping error: {str(e)}")
        return {"error": str(e)}
    finally:
        if 'driver' in locals():
            driver.quit()
            
    return results
