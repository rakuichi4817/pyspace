import requests
from fastmcp import FastMCP

mcp = FastMCP("Sample MCP Server", "これはテスト用のMCPサーバーです")


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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
