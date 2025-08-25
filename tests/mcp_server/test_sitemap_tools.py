from unittest.mock import Mock, patch

from mcp_server.sample_server import get_sitemap_urls, get_url_info


class TestGetSitemapUrls:
    @patch("mcp_server.sample_server.requests.get")
    def test_正常なサイトマップを解析できること(self, mock_get):
        # GIVEN: 正常なサイトマップのレスポンス
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2024-01-15T10:00:00Z</lastmod>
                <changefreq>daily</changefreq>
                <priority>0.8</priority>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
                <lastmod>2024-01-10T10:00:00Z</lastmod>
                <changefreq>weekly</changefreq>
                <priority>0.6</priority>
            </url>
        </urlset>"""

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = sitemap_xml.encode("utf-8")
        mock_get.return_value = mock_response

        sitemap_url = "https://example.com/sitemap.xml"

        # WHEN: get_sitemap_urlsを呼び出す
        result = get_sitemap_urls.fn(sitemap_url)

        # THEN: 更新日順でソートされたURLリストが返る
        assert isinstance(result, list)
        assert len(result) == 2
        # 新しい順にソートされているかチェック
        assert result[0]["url"] == "https://example.com/page1"
        assert result[0]["lastmod"] == "2024-01-15T10:00:00Z"
        assert result[1]["url"] == "https://example.com/page2"
        assert result[1]["lastmod"] == "2024-01-10T10:00:00Z"

    @patch("mcp_server.sample_server.requests.get")
    def test_limit引数で結果数を制限できること(self, mock_get):
        # GIVEN: 複数URLを含むサイトマップ
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/page1</loc><lastmod>2024-01-15T10:00:00Z</lastmod></url>
            <url><loc>https://example.com/page2</loc><lastmod>2024-01-14T10:00:00Z</lastmod></url>
            <url><loc>https://example.com/page3</loc><lastmod>2024-01-13T10:00:00Z</lastmod></url>
        </urlset>"""

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = sitemap_xml.encode("utf-8")
        mock_get.return_value = mock_response

        sitemap_url = "https://example.com/sitemap.xml"

        # WHEN: limit=2でget_sitemap_urlsを呼び出す
        result = get_sitemap_urls.fn(sitemap_url, limit=2)

        # THEN: 2件のURLが返る
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com/page1"
        assert result[1]["url"] == "https://example.com/page2"

    @patch("mcp_server.sample_server.requests.get")
    def test_サイトマップ取得エラー時は空リストが返ること(self, mock_get):
        # GIVEN: サイトマップ取得でエラーが発生
        mock_get.side_effect = Exception("Network error")

        sitemap_url = "https://example.com/sitemap.xml"

        # WHEN: get_sitemap_urlsを呼び出す
        result = get_sitemap_urls.fn(sitemap_url)

        # THEN: 空のリストが返る
        assert result == []

    @patch("mcp_server.sample_server.requests.get")
    def test_不正なXMLの場合は空リストが返ること(self, mock_get):
        # GIVEN: 不正なXMLレスポンス
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"Invalid XML content"
        mock_get.return_value = mock_response

        sitemap_url = "https://example.com/sitemap.xml"

        # WHEN: get_sitemap_urlsを呼び出す
        result = get_sitemap_urls.fn(sitemap_url)

        # THEN: 空のリストが返る
        assert result == []


class TestGetUrlInfo:
    @patch("mcp_server.sample_server.requests.get")
    def test_正常なHTMLページの情報を取得できること(self, mock_get):
        # GIVEN: 正常なHTMLレスポンス
        html_content = """
        <html>
        <head>
            <title>テストページ</title>
            <meta name="description" content="テストページの説明">
            <meta property="og:title" content="OGテストページ">
            <meta property="og:description" content="OGテストページの説明">
        </head>
        <body>
            <h1>メインコンテンツ</h1>
            <p>これはテストページのコンテンツです。</p>
        </body>
        </html>
        """

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = html_content.encode("utf-8")
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_get.return_value = mock_response

        url = "https://example.com/test-page"

        # WHEN: get_url_infoを呼び出す
        result = get_url_info.fn(url)

        # THEN: URL情報が正しく取得される
        assert isinstance(result, dict)
        assert result["url"] == url
        assert result["status_code"] == 200
        assert result["title"] == "テストページ"
        assert result["description"] == "テストページの説明"
        assert result["og_title"] == "OGテストページ"
        assert result["og_description"] == "OGテストページの説明"
        assert "content_preview" in result
        assert (
            "メインコンテンツ これはテストページのコンテンツです。"
            in result["content_preview"]
        )

    @patch("mcp_server.sample_server.requests.get")
    def test_URL取得エラー時はエラー情報が返ること(self, mock_get):
        # GIVEN: URL取得でエラーが発生
        mock_get.side_effect = Exception("Network error")

        url = "https://example.com/test-page"

        # WHEN: get_url_infoを呼び出す
        result = get_url_info.fn(url)

        # THEN: エラー情報を含む辞書が返る
        assert isinstance(result, dict)
        assert result["url"] == url
        assert "error" in result
        assert result["error"] == "Network error"

    @patch("mcp_server.sample_server.requests.get")
    def test_メタタグがない場合でも基本情報は取得できること(self, mock_get):
        # GIVEN: メタタグのないシンプルなHTML
        html_content = """
        <html>
        <head><title>シンプルページ</title></head>
        <body><p>シンプルなコンテンツ</p></body>
        </html>
        """

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = html_content.encode("utf-8")
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        url = "https://example.com/simple-page"

        # WHEN: get_url_infoを呼び出す
        result = get_url_info.fn(url)

        # THEN: 基本情報は取得される
        assert result["url"] == url
        assert result["status_code"] == 200
        assert result["title"] == "シンプルページ"
        # メタタグは存在しないがエラーにならない
        assert "description" not in result or result.get("description") == ""
