from typing import Optional, Type, Any
from pydantic.v1 import BaseModel, Field
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from deep_translator import GoogleTranslator

from src.helpers.enums import ActionType
from src.api.websocket_manager import WebSocketManager
from src.agent.session_manager import ChatSessionManager
from src.message_templates.websocket_message_template import (
    UserProfile,
    WebsocketMessageTemplate,
)
from src.helpers.conf_loader import DAILOGUE, server_config_loader


class InformationInput(BaseModel):
    """Schema for InformationTool input."""
    question: str = Field(description="ユーザーからの質問内容。")


class InformationTool(BaseTool):
    """Generic RAG-based tool for retrieving knowledge from a specific dataset."""
    name: str = "information_tool"
    description: str = "知識ベース(FAQやサポート情報など)から情報を検索し、回答するためのツール。"
    args_schema: Type[BaseModel] = InformationInput

    retriever: Optional[Any] = None
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    user_profile: Optional[UserProfile] = None
    current_language: str = server_config_loader.get_language()
    return_direct: bool = False

    def _get_base_language_code(self, lang_code: str) -> str:
        """Extract base language code from locale (e.g., 'en-US' -> 'en')."""
        if '-' in lang_code:
            return lang_code.split('-')[0].lower()
        return lang_code.lower()

    # ----------- Translation Helper -----------
    def _translate_to_japanese(self, query: str) -> str:
        """Translate query to Japanese if not already in Japanese."""
        self.current_language = self._get_base_language_code(self.current_language)
        if self.current_language == "ja":
            return query
        
        try:
            translator = GoogleTranslator(source=self.current_language, target='ja')
            translated = translator.translate(query)
            print(f"[Translation] {self.current_language} -> ja: '{query}' -> '{translated}'")
            return translated
        except Exception as e:
            print(f"[Translation Error] {e}, using original query")
            return query

    # ----------- Main sync execution -----------
    def _run(
        self,
        question: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if not self.retriever:
            return "RAG Retrieverが設定されていません。"

        japanese_question = self._translate_to_japanese(question)

        try:
            results = self.retriever.invoke(japanese_question)
        except Exception as e:
            print(f"[RAG Error] {e}")
            return DAILOGUE.get("rag_fallback_message", "情報を取得できませんでした。")

        if not results:
            return DAILOGUE.get("rag_fallback_message", "関連する情報が見つかりませんでした。")

        return self._format_results(results, keyword=question)

    # ----------- Async version -----------
    async def _arun(
        self,
        question: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        if not self.retriever:
            return "RAG Retrieverが設定されていません。"

        self.session_manager.context.last_tool_name = self.name

        japanese_question = self._translate_to_japanese(question)

        try:
            results = await self.retriever.ainvoke(japanese_question)
        except Exception as e:
            print(f"[RAG Async Error] {e}")
            return DAILOGUE.get("rag_fallback_message", "情報を取得できませんでした。")

        if not results:
            return DAILOGUE.get("rag_fallback_message", "関連する情報が見つかりませんでした。")

        return self._format_results(results, keyword=question)

    # ----------- Helper -----------
    def _format_results(self, results: list, keyword: str = "") -> str:
        """Format retrieved exhibits into the standard response template."""
        seen_nos = set()
        entries = []

        for doc in results:
            m = doc.metadata
            no = m.get("no", "")
            if no in seen_nos:
                continue
            seen_nos.add(no)

            company = m.get("company", "")
            title = m.get("title", "")
            summary = m.get("summary", "")
            appeal = m.get("appeal", "")
            detail = f"{summary}{appeal}".strip()

            prefix = "次に、" if entries else ""
            entries.append(
                f"{prefix}展示No.{no}・{company}社「{title}」：{detail}を展示しております。"
            )

        if not entries:
            return DAILOGUE.get("rag_fallback_message", "関連する情報が見つかりませんでした。")

        keyword_part = f"「{keyword}」についてですが、" if keyword else ""
        body = " ".join(entries)
        return f"{keyword_part}{body} 詳細は、各展示場所にてご確認ください。"