from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin
import time

from crawl4ai import AsyncWebCrawler

def selenium_task(key_word):
    
    driver = webdriver.Chrome()
    try:
        driver.get("https://scholar.google.com/")
        search_bar = driver.find_element(By.NAME, 'q')
        search_bar.send_keys(key_word)
        search_bar.send_keys(Keys.RETURN)

        time.sleep(3)

        links = []
        links_element = driver.find_elements(By.XPATH, '//h3[@class="gs_rt"]/a')

        for elements in links_element:
            href = elements.get_attribute("href")
            if href:
                links.append(href)

        if len(links) != 0:
            print(f"Tìm thấy {len(links)} link: ")
            for link in links:
                print(link)
            return links
        else:
            print("Can't find anything")
    finally:
        driver.quit()
        
async def crawling_web(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        link = None
        soup = BeautifulSoup(result.html, "html.parser")
        for i in soup.find_all("a", href = True):
            href = i["href"]
            if "/doi/reader" in href.lower():
                link = urljoin(url, href)
                break
        return link
    
if __name__ == "__main__":
    key_word = input("Nhập vào từ khoá: ")
    link_list = selenium_task(key_word)
    if link_list:
        links = []
        for url in link_list:
            links.append(asyncio.run(crawling_web(url)))
        for i in links:
            print(i)
    else:
        print("No result.")
