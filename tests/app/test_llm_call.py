import os

import pytest
from litellm.types.utils import Choices
from mcp.types import Tool

from app.llm_call import call_llm_with_tools, fastmcp_tools_to_litellm_tools


class TestFastmcpToolsToLitellmTools:
    def test_変換処理が正しく行われること(self):
        # GIVEN: fastmcpのTool情報
        dummy_tools = [
            Tool(
                name="get_weather",
                description="天気取得",
                inputSchema={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                },
                outputSchema={},
            ),
            Tool(
                name="get_address",
                description="住所取得",
                inputSchema={
                    "type": "object",
                    "properties": {"zipcode": {"type": "string"}},
                },
                outputSchema={},
            ),
        ]

        # WHEN: fastmcp_tools_to_litellm_toolsを呼び出す
        result = fastmcp_tools_to_litellm_tools(dummy_tools)

        # THEN: litellm function call用tools dict形式に変換される
        assert isinstance(result, list)
        assert result[0]["function"]["name"] == "get_weather"
        assert result[1]["function"]["description"] == "住所取得"
        assert "zipcode" in result[1]["function"]["parameters"]["properties"]


class TestCallLlmWithTools:
    @pytest.mark.skipif(
        os.getenv("CI") == "true", reason="CIテスト環境では実行しない。"
    )
    def test_call_llm_with_tools_azure実際にモデルへ問い合わせること(self):
        # GIVEN: Azure GPT-4.1-mini への問い合わせ用メッセージとツール
        dummy_tools = [
            Tool(
                name="get_weather",
                description="天気取得",
                inputSchema={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                },
                outputSchema={},
            ),
        ]
        messages = [
            {"role": "system", "content": "あなたはAIです。"},
            {"role": "user", "content": "「こんにちは」とだけ答えてください！"},
        ]

        # WHEN: 実際に call_llm_with_tools を呼び出す
        result = call_llm_with_tools(messages, dummy_tools, model="azure/gpt-4.1-mini")

        # THEN: レスポンスが返ること（内容はAPIの応答次第）
        assert hasattr(result, "choices"), "choices属性が存在しません"
        assert isinstance(result.choices, list), "choicesはlist型であるべきです"
        choice = result.choices[0]
        assert hasattr(choice, "message"), "message属性がありません"
        assert isinstance(choice, Choices)
        assert choice.message.content == "こんにちは", (
            f"message.contentが'こんにちは'ではありません: {choice.message.content}"
        )

    @pytest.mark.skipif(
        os.getenv("CI") == "true", reason="CIテスト環境では実行しない。"
    )
    def test_call_llm_with_tools_azureツール呼び出しパターンを検証する(self):
        # GIVEN: ツール呼び出しが期待されるメッセージとツール
        dummy_tools = [
            Tool(
                name="get_weather",
                description="天気取得",
                inputSchema={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                },
                outputSchema={},
            ),
        ]
        messages = [
            {"role": "system", "content": "あなたはAIです。"},
            {"role": "user", "content": "東京の天気をツールで取得してください。"},
        ]

        # WHEN: 実際に call_llm_with_tools を呼び出す
        result = call_llm_with_tools(messages, dummy_tools, model="azure/gpt-4.1-mini")

        # THEN: tool_callsが含まれていること（内容はAPIの応答次第）
        assert hasattr(result, "choices"), "choices属性が存在しません"
        assert isinstance(result.choices, list), "choicesはlist型であるべきです"
        choice = result.choices[0]
        assert hasattr(choice, "finish_reason"), "finish_reason属性がありません"
        assert choice.finish_reason == "tool_calls", (
            f"finish_reasonが'tool_calls'ではありません: {choice.finish_reason}"
        )
        assert hasattr(choice, "message"), "message属性がありません"
        assert isinstance(choice, Choices)
        message = choice.message
        assert message is not None, "messageがNoneです"
        assert hasattr(message, "tool_calls"), "tool_calls属性がありません"
        tool_calls = message.tool_calls
        assert isinstance(tool_calls, list), "tool_callsはlist型であるべきです"
        assert len(tool_calls) > 0, "tool_callsが空です"
        assert hasattr(tool_calls[0], "function"), "tool_callにfunction属性がありません"
        assert tool_calls[0].function.name == "get_weather", (
            "function.nameが'get_weather'ではありません"
        )
