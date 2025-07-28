import json
import logging
from typing import Any

import litellm
from fastmcp import Client
from litellm.types.utils import ModelResponse
from mcp import Tool

# 定数定義
DEFAULT_LLM_MODEL = "azure/gpt-4.1-mini"


def fastmcp_tools_to_litellm_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """
    fastmcpのTool情報をlitellm function call用tools dict形式に変換する。

    Parameters
    ----------
    tools : list[Tool]
        fastmcpで取得したToolオブジェクトのリスト

    Returns
    -------
    list[dict[str, Any]]
        litellm function call用tools(dict)リスト
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools
    ]


def call_llm_with_tools(
    messages: list[dict[str, Any]], tools: list[Tool], model: str = DEFAULT_LLM_MODEL
) -> ModelResponse:
    """
    メッセージ履歴とツール情報を渡してLLMのfunction call出力を得る。

    Parameters
    ----------
    messages : list[dict[str, Any]]
        チャット履歴（role, content, tool等を含む）
    tools : list[Tool]
        fastmcpで取得したToolオブジェクトのリスト
    model : str, optional
        利用するLLMモデル名（デフォルト: azure/gpt-4.1-mini）

    Returns
    -------
    ModelResponse
        LLMの応答
    """
    litellm_tools = fastmcp_tools_to_litellm_tools(tools)
    response = litellm.completion(
        model=model,
        messages=messages,
        tools=litellm_tools,
        tool_choice="auto",
    )
    return response  # type: ignore


async def request_completions(
    messages: list[dict],
    tools: list[Tool],
    client: Client,
    logger: logging.Logger,
):
    """
    チャット履歴とツール情報を使用してLLMからの応答を取得し、履歴を更新する。

    Notes
    -----
    ツールコールがある場合はMCPサーバのツールを実行し、結果を履歴に追加する。

    Parameters
    ----------
    messages : list[dict]
        チャット履歴（role, content）
    tools : list[Tool]
        MCPサーバのツール一覧
    client : Client
        MCPクライアント
    logger : logging.Logger
        ロガー

    Returns
    -------
    list[dict]
        追加されたメッセージ履歴（role, content）
    """
    history = messages.copy()
    logger.info(f"チャット履歴: {history}")
    while True:
        response = call_llm_with_tools(history, tools)
        logger.info("LLM（OpenAI）からの応答を受信: %s", response)
        message = response["choices"][0]["message"]
        # ツールコールがなければ終了
        if not (hasattr(message, "tool_calls") and message.tool_calls):
            history.append({"role": "assistant", "content": message["content"]})
            break

        # ツールコールがある場合
        history.append(
            {
                "role": "assistant",
                "content": f"ツールコールします: {message.tool_calls}",
                "tool_calls": message.tool_calls,
            }
        )
        # すべてのツールコールを実行
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            logger.info(f"ツール呼び出し: {tool_name}({tool_args})")
            args_dict = json.loads(tool_args)
            logger.info(f"MCPツール {tool_name} を実行: 引数 {args_dict}")
            async with client:
                tool_result = await client.call_tool(tool_name, arguments=args_dict)
            logger.info(f"ツール {tool_name} の実行結果: {tool_result}")

            history.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": str(tool_result),
                }
            )
        # ツール結果をLLMに渡してループ継続
    return history
