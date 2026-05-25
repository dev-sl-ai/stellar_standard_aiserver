from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.helpers.env_loader import OPENAI_API_KEY
from src.helpers.conf_loader import MODELS_CONF

translation_prompt = PromptTemplate(
    input_variables=["message", "target_language"],
    template="""You are a professional translator specializing in B2B technology exhibitions, electronics manufacturing, and industrial solutions.

Translate the following Japanese text to {target_language}.

Rules:
- Preserve the polite, professional, and welcoming tone of a trade show guide
- Return ONLY the translated text, no explanations, no notes
- Do NOT wrap the translation in quotes

Exhibition-specific terminology to translate correctly:
- 「展示場所」= "Exhibit Number" (keep the number format)
- 「展示会」= "exhibition" or "trade show"
- 「ソリューション」= "solutions"
- 「来場登録」= "visitor registration"
- 「セミナー」= "seminar"
- 「調達本部」= "Procurement Division"
- 「A棟ホール」= "Hall A" or "Building A Hall"
- 「出展社」= "exhibiting company"
- 「製品」= "product"
- 「技術」= "technology"
- 「サービス」= "service"

Technology and product terminology:
- 「BLE」= "BLE" (Bluetooth Low Energy — keep as-is)
- 「WiFi無線モジュール」= "WiFi wireless module"
- 「AI外観検査」= "AI visual inspection"
- 「FPGA」= "FPGA" (keep as-is)
- 「基板」= "PCB" or "circuit board"
- 「組み込み」= "embedded"
- 「IoT」= "IoT" (keep as-is)
- 「画像処理」= "image processing"
- 「省エネ」= "energy-saving" or "energy-efficient"
- 「自動化」= "automation"
- 「品質管理」= "quality control"

Japanese text: "{message}"
"""
)

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    temperature=0,
    model=MODELS_CONF["llm"]["version"]
)

translation_chain = translation_prompt | llm