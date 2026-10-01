import html
import re
from pathlib import Path

import requests

CAFE_ID = "19994344"
QUERY = "서금사a"
PER_PAGE = 10
README = Path("README.md")

API_URL = (
    f"https://apis.naver.com/cafe-web/cafe-search-api/"
    f"v2/cafes/{CAFE_ID}/search/articles"
)

START_MARKER = "<!-- ARTICLES_START -->"
END_MARKER = "<!-- ARTICLES_END -->"


def clean_title(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def fetch_articles():
    params = {
        "query": QUERY,
        "searchBy": 1,
        "sortBy": "RECENCY",
        "page": 1,
        "perPage": PER_PAGE,
        "ad": "false",
        "views": "MEMBER_LEVEL,COUNT,SALE_INFO,CAFE_MENU",
    }
    headers = {
        "Accept": "application/json",
        "Referer": "https://m.cafe.naver.com/",
        "x-cafe-product": "mweb",
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()

    return [
        entry["item"]
        for entry in payload["result"]["articleList"]
        if entry.get("type") == "ARTICLE" and entry.get("item")
    ][:PER_PAGE]


def article_url(article_id: int) -> str:
    return (
        f"https://m.cafe.naver.com/ca-fe/web/cafes/"
        f"{CAFE_ID}/articles/{article_id}"
    )


def build_section(articles) -> str:
    lines = [
        "| Article ID | 작성일 | 제목 |",
        "|---:|---|---|",
    ]

    for article in articles:
        article_id = article["articleId"]
        title = clean_title(article.get("subject", "")).replace("|", "\\|")
        added = article.get("addDate", "").replace("T", " ")[:16]
        url = article_url(article_id)
        lines.append(f"| {article_id} | {added} | [{title}]({url}) |")

    return "\n".join(lines)


def update_readme(section: str) -> bool:
    text = README.read_text(encoding="utf-8")

    if START_MARKER not in text or END_MARKER not in text:
        raise RuntimeError("README markers are missing")

    before, rest = text.split(START_MARKER, 1)
    current_section, after = rest.split(END_MARKER, 1)

    # 공백 차이를 제외하고 게시글 목록 자체가 같으면 README를 건드리지 않습니다.
    if current_section.strip() == section.strip():
        print("Article list unchanged. README will not be modified.")
        return False

    updated = (
        before
        + START_MARKER
        + "\n\n"
        + section
        + "\n\n"
        + END_MARKER
        + after
    )
    README.write_text(updated, encoding="utf-8")
    print("Article list changed. README updated.")
    return True


def main():
    articles = fetch_articles()
    if not articles:
        raise RuntimeError("Naver Cafe API returned no articles")

    print(f"Fetched {len(articles)} articles")
    for article in articles:
        print(article["articleId"], clean_title(article.get("subject", "")))

    update_readme(build_section(articles))


if __name__ == "__main__":
    main()
