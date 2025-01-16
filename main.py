import codecs
import json

from bs4 import BeautifulSoup
import aiohttp
import asyncio
import aiofiles
import csv
from fake_useragent import UserAgent
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class Requester:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        self.user_agent = UserAgent()

    def get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.user_agent.random
        }

    async def post(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        async with self.session.post(url, headers=self.get_headers(), params=params) as response:
            response.raise_for_status()
            return await response.text()

    async def close(self) -> None:
        await self.session.close()


class BaseParser(ABC):
    def __init__(self, requester: Requester) -> None:
        self.requester = requester

    @abstractmethod
    async def get_article_links(self, page_data: Dict[str, Any]) -> List[str]:
        pass

    @abstractmethod
    async def parse_article(self, html: str) -> Dict[str, str]:
        pass


class InterexchangeParse(BaseParser):
    BASE_URL = "https://www.interexchange.org/wp-admin/admin-ajax.php"

    async def get_article_links(self, page_data: Dict[str, Any]) -> List[str]:
        links = []
        html = await self.requester.post(self.BASE_URL, params=page_data)
        html = json.loads(html)
        html = html['content']
        # html.replace(r'\/', '/')
        # html = codecs.decode(html, "unicode_escape")
        soup = BeautifulSoup(html, 'html.parser')
        for a_tag in soup.find_all('a', class_='elementor-button-link'):
            href = a_tag['href']
            full_url = href if href.startswith("http") else f"https://www.interexchange.org{href}"
            links.append(full_url)
        return links

    async def parse_article(self, html: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Без заголовка"
        content = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
        return {
            'title': title,
            'content': content,
        }

    async def fetch_all_articles(self) -> List[Dict[str, str]]:
        articles = []
        page_number = 1

        while True:
            try:
                page_data = {
                    "action": "jet_smart_filters",
                    "provider": "jet-engine/blog-list",
                    "settings[lisitng_id]": 962,
                    "props[page]":  page_number,
                    "props[query_type]": 'posts',
                    "paged": page_number + 1,

                }
                print(f"Fetching page {page_number}...")

                links = await self.get_article_links(page_data)
                if not links:
                    print(f"No links found on page {page_number}.")
                    break

                for link in links:
                    try:
                        html = await self.requester.post(link)
                        article_data = await self.parse_article(html)
                        article_data['url'] = link
                        articles.append(article_data)
                        print(f"Successfully parsed: {article_data['title']}")
                    except Exception as e:
                        print(f"Error parsing article {link}: {e}")

                # Check for the next page
                # html = await self.requester.post(self.BASE_URL, params=page_data)
                # soup = BeautifulSoup(html, 'html.parser')
                # next_page = soup.find('div', class_='jet-filters-pagination__link', string=str(page_number + 1))
                # if next_page:
                page_number += 1
                # else:
                #     break

            except Exception as e:
                print(f"Error fetching page {page_number}: {e}")
                break

        return articles


class AuPairUSABlogParser(BaseParser):
    BASE_URL = "https://blog.aupairusa.org/au-pairs/"

    async def get_article_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a_tag in soup.find_all('h2', class_='entry-title'):
            link_tag = a_tag.find('a')
            if link_tag and link_tag.has_attr('href'):
                href = link_tag['href']
                full_url = href if href.startswith("http") else href
                links.append(full_url)
        return links

    async def parse_article(self, html: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Без заголовка"
        content = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
        return {
            'title': title,
            'content': content,
        }

    async def get_all_pages(self) -> List[str]:
        pages = set([self.BASE_URL])
        html = await self.requester.post(self.BASE_URL)
        soup = BeautifulSoup(html, 'html.parser')
        pagination_div = soup.find('div', class_='col-md-8 page_navi')
        if pagination_div:
            last_page_link = pagination_div.find('a', class_='last')
            if last_page_link and last_page_link.has_attr('href'):
                last_page_url = last_page_link['href']
                total_pages = int(last_page_url.rstrip('/').split('/')[-1])
                for i in range(1, total_pages + 1):
                    page_url = f"https://blog.aupairusa.org/au-pairs/page/{i}/"
                    pages.add(page_url)
        return sorted(pages)

    async def fetch_all_articles(self) -> List[Dict[str, str]]:
        articles = []
        pages = await self.get_all_pages()

        for page in pages:
            try:
                html = await self.requester.post(page)
                links = await self.get_article_links(html)
                for link in links:
                    try:
                        article_html = await self.requester.post(link)
                        article_data = await self.parse_article(article_html)
                        article_data['url'] = link
                        articles.append(article_data)
                        print(f"Successfully parsed: {article_data['title']}")
                    except Exception as e:
                        print(f"Error parsing article {link}: {e}")
            except Exception as e:
                print(f"Error fetching page {page}: {e}")

        return articles


class IECParse(BaseParser):
    BASE_URL = "https://iec.ru"

    async def get_article_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', 'wrapper'):
            href = a_tag['href']
            full_url = self.BASE_URL + href if not href.startswith("http") else href
            links.append(full_url)
        return list(set(links))

    async def parse_article(self, html: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Без заголовка"
        content = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
        return {
            'title': title,
            'content': content
        }

    async def fetch_all_articles(self) -> List[Dict[str, str]]:
        articles = []
        main_page_html = await self.requester.post(self.BASE_URL)
        links = await self.get_article_links(main_page_html)
        for link in links:
            try:
                article_html = await self.requester.post(link)
                article_data = await self.parse_article(article_html)
                article_data['url'] = link
                articles.append(article_data)
                print(f"Successfully parsed: {article_data['title']}")
            except Exception as e:
                print(f"Error parsing article {link}: {e}")

        return articles


async def main() -> None:
    requester = Requester()
    parsers = [
        # InterexchangeParse(requester),
        AuPairUSABlogParser(requester),
        # IECParse(requester),
    ]

    try:
        all_articles = []
        for parser in parsers:
            articles = await parser.fetch_all_articles()
            all_articles.extend(articles)

        async with aiofiles.open('combined_articles.csv', 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'content', 'url'])
            await file.write("title,content,url\n")
            for article in all_articles:
                content_clean = article['content'].replace(',', ' ').replace('\n', ' ')
                await file.write(f"{article['title']},{content_clean},{article['url']}\n")

        print(f"Saved {len(all_articles)} articles to combined_articles.csv")

    except Exception as e:
        print(f"Execution error: {e}")

    finally:
        await requester.close()


if __name__ == '__main__':
    asyncio.run(main())
