import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP

mcp = FastMCP("Sample MCP Server", "これはテスト用のMCPサーバーです")  # type: ignore


@mcp.tool()
def get_address_by_postal_code(postal_code: str) -> dict:
    """
    郵便番号から住所情報を取得する。

    Parameters
    ----------
    postal_code : str
        住所を取得したい郵便番号（7桁）

    Returns
    -------
    dict
        住所情報（都道府県、市区町村、町域など）を含む辞書。該当なしの場合は空の辞書。
    """
    API_URL = "https://zipcloud.ibsnet.co.jp/api/search"
    params = {"zipcode": postal_code}
    try:
        response = requests.get(API_URL, params=params, timeout=5)
        response.raise_for_status()
        result = response.json()
        if result["status"] == 200 and result["results"]:
            return result["results"][0]
        else:
            return {}
    except Exception:
        # エラー時は空の辞書を返す
        return {}


@mcp.tool()
def get_sitemap_urls(sitemap_url: str, limit: int = 50) -> list[dict[str, Any]]:
    """
    サイトマップURLを解析して、更新された順でURLのリストを取得する。

    Parameters
    ----------
    sitemap_url : str
        解析するサイトマップのURL
    limit : int, optional
        取得するURLの最大数（デフォルト: 50）

    Returns
    -------
    List[Dict[str, Any]]
        更新日順（新しい順）でソートされたURL情報のリスト。
        各辞書には'url', 'lastmod', 'changefreq', 'priority'が含まれる。
    """
    try:
        # サイトマップを取得
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()

        # XMLを解析
        root = ET.fromstring(response.content)

        # 名前空間を考慮
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        urls = []
        # URL要素を取得
        for url_elem in root.findall(".//sitemap:url", namespace):
            url_data = {}

            # URL取得
            loc_elem = url_elem.find("sitemap:loc", namespace)
            if loc_elem is not None:
                url_data["url"] = loc_elem.text

            # 最終更新日取得
            lastmod_elem = url_elem.find("sitemap:lastmod", namespace)
            if lastmod_elem is not None:
                url_data["lastmod"] = lastmod_elem.text

            # 更新頻度取得
            changefreq_elem = url_elem.find("sitemap:changefreq", namespace)
            if changefreq_elem is not None:
                url_data["changefreq"] = changefreq_elem.text

            # 優先度取得
            priority_elem = url_elem.find("sitemap:priority", namespace)
            if priority_elem is not None:
                url_data["priority"] = priority_elem.text

            urls.append(url_data)

        # 最終更新日でソート（新しい順）
        def sort_key(item):
            lastmod = item.get("lastmod", "")
            if lastmod:
                try:
                    # ISO形式の日付をパース
                    return datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        # 別の形式を試す
                        return datetime.strptime(lastmod, "%Y-%m-%d")
                    except ValueError:
                        return datetime.min
            return datetime.min

        sorted_urls = sorted(urls, key=sort_key, reverse=True)

        # 制限数でカット
        return sorted_urls[:limit]

    except Exception:
        # エラー時は空のリストを返す
        return []


@mcp.tool()
def get_url_info(url: str) -> dict[str, Any]:
    """
    指定されたURLの情報を取得する。

    Parameters
    ----------
    url : str
        情報を取得するURL

    Returns
    -------
    Dict[str, Any]
        URL情報を含む辞書（title, description, content_preview, status_codeなど）。
        エラー時は空の辞書。
    """
    try:
        # ページを取得
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # HTMLを解析
        soup = BeautifulSoup(response.content, "html.parser")

        # 基本情報を取得
        info = {
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
        }

        # タイトル取得
        title_elem = soup.find("title")
        if title_elem:
            info["title"] = title_elem.get_text().strip()

        # メタ説明取得
        description_elem = soup.find("meta", attrs={"name": "description"})
        if description_elem and hasattr(description_elem, "get"):
            content = description_elem.get("content")
            if content:
                info["description"] = content.strip()

        # OGタイトル取得
        og_title_elem = soup.find("meta", attrs={"property": "og:title"})
        if og_title_elem and hasattr(og_title_elem, "get"):
            content = og_title_elem.get("content")
            if content:
                info["og_title"] = content.strip()

        # OG説明取得
        og_description_elem = soup.find("meta", attrs={"property": "og:description"})
        if og_description_elem and hasattr(og_description_elem, "get"):
            content = og_description_elem.get("content")
            if content:
                info["og_description"] = content.strip()

        # 最終更新日（metaタグから）
        last_modified_elem = soup.find("meta", attrs={"name": "last-modified"})
        if last_modified_elem and hasattr(last_modified_elem, "get"):
            content = last_modified_elem.get("content")
            if content:
                info["last_modified"] = content.strip()

        # コンテンツのプレビュー（最初の200文字）
        # scriptとstyleタグを除去
        for script in soup(["script", "style"]):
            script.extract()

        text_content = soup.get_text()
        # 改行や空白を整理
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        if text:
            info["content_preview"] = text[:200] + ("..." if len(text) > 200 else "")

        return info

    except Exception as e:
        # エラー時は基本情報のみ返す
        return {"url": url, "error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
