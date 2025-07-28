import asyncio
from logging import INFO, basicConfig, getLogger

import streamlit as st
from fastmcp import Client
from mcp.types import Tool

from app.llm_call import request_completions

# 定数定義
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"
PAGE_TITLE = "PySpace チャット"
CHAT_RESET_BUTTON_LABEL = "対話ログをリセットする"
CHAT_RESET_SUCCESS_MSG = "対話ログをリセットしました。"
CHAT_INPUT_LABEL = "メッセージを入力してください"
LOG_NAME = "pyspace-chat"

# ロギング設定
basicConfig(level=INFO)
logger = getLogger(LOG_NAME)

# アプリタイトル設定
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(PAGE_TITLE)

client = Client(MCP_SERVER_URL)


def initialize_session_state():
    """
    session_stateの初期化

    Notes
    -----
    Streamlitのsession_stateに'messages'キーがなければ空リストで初期化する。
    """
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


async def get_tools(client: Client) -> list[Tool]:
    """
    MCPサーバからツール一覧を取得する

    Parameters
    ----------
    client : Client
        MCPクライアント

    Returns
    -------
    list[Tool]
        MCPサーバのツール一覧
    """

    async with client:
        return await client.list_tools()


async def process_chat():
    """
    チャット処理のメイン関数

    Notes
    -----
    ユーザー入力を受け付け、LLMとツールを使用して応答を生成する。
    """
    tools = await get_tools(client)
    st.success("MCPサーバへの接続成功！")
    logger.info("MCPサーバへの接続成功！")

    # 履歴表示
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ユーザー入力受付
    user_input = st.chat_input(CHAT_INPUT_LABEL)
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state["messages"].append({"role": "user", "content": user_input})
        updated_history = await request_completions(
            st.session_state["messages"], tools, client, logger
        )
        logger.info("更新されたメッセージ履歴: %s", updated_history)
        # 新規追加分のみ表示
        for msg in updated_history[len(st.session_state["messages"]) :]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        st.session_state["messages"] = updated_history


def main():
    """
    アプリケーションのメインエントリーポイント

    Notes
    -----
    サイドバーにチャット設定（リセットボタン）を表示し、チャット処理を開始する。
    """
    with st.sidebar:
        st.subheader("チャット設定")
        if st.button(CHAT_RESET_BUTTON_LABEL):
            st.session_state["messages"] = []
            st.success(CHAT_RESET_SUCCESS_MSG)

    try:
        asyncio.run(process_chat())
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        logger.error(f"チャット処理中にエラーが発生: {str(e)}", exc_info=True)


if __name__ == "__main__":
    initialize_session_state()
    main()
