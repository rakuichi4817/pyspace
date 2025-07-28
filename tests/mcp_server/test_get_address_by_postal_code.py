from mcp_server.sample_server import get_address_by_postal_code


def test_正しく住所情報が取れること():
    # GIVEN: 東京都千代田区千代田の郵便番号
    postal_code = "1000001"

    # WHEN: get_address_by_postal_codeを呼び出す
    result = get_address_by_postal_code.fn(postal_code)

    # THEN: 住所情報が辞書で返る
    assert isinstance(result, dict)
    assert result.get("address1") == "東京都"
    assert result.get("address2") == "千代田区"
    assert result.get("address3") == "千代田"


def test_存在しない郵便番号は空の辞書が返ること():
    # GIVEN: 存在しない郵便番号
    postal_code = "0000000"

    # WHEN: get_address_by_postal_codeを呼び出す
    result = get_address_by_postal_code.fn(postal_code)

    # THEN: 空の辞書が返る
    assert isinstance(result, dict)
    assert result == {}


def test_不正な形式は空の辞書が返ること():
    # GIVEN: 不正な形式の郵便番号
    postal_code = "abcde12"

    # WHEN: get_address_by_postal_codeを呼び出す
    result = get_address_by_postal_code.fn(postal_code)

    # THEN: 空の辞書が返る
    assert isinstance(result, dict)
    assert result == {}
