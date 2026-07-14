"""Bedrock prompt construction for the narrative service.

Every number handed to the model is GIVEN (already computed by the deterministic
engine). The model narrates; it never computes, predicts, or advises.
"""

from mindfolio_core.domain.models import ReconstructionResult

_SYSTEM_RULES = (
    "你是投資回顧的文案助手。以下所有數字都是後端已算好的事實，"
    "請直接引用，不要自行計算、推估或修改任何數字。\n"
    "嚴禁出現：買進／賣出等買賣建議、目標價、報酬保證或穩賺字眼、"
    "以及把投資人格說成心理疾病或診斷。\n"
    "投資人格只是可分享的產品標籤，不是心理量表。\n"
    "只輸出 JSON，格式為 "
    '{"headline": "...", "summary": "...", "insight": "..."}，'
    "三個欄位都必填、皆為繁體中文短句，不要有 JSON 以外的任何文字。"
)


def build_narrative_prompt(result: ReconstructionResult) -> str:
    """Build the user prompt from a verified result DTO."""
    scores = result.scores
    return (
        f"{_SYSTEM_RULES}\n\n"
        "以下是這位使用者 2025 投資重建的結果（皆為既定事實）：\n"
        f"- 投資人格：{result.persona_name}（代碼 {result.persona_code}）\n"
        f"- 人格標語：{result.persona_headline}\n"
        f"- 五檔平均報酬：{result.average_return:.1f}%\n"
        f"- 資料信心分數：{result.confidence}\n"
        f"- 決策力分項：成果 {scores.outcome}／進場 {scores.entry}／"
        f"掌握 {scores.capture}／資料 {scores.data}\n"
        f"- 指紋向量：{[round(v, 3) for v in result.fingerprint]}\n\n"
        "請根據上述事實，寫一段溫暖、客觀的回顧："
        "headline 點出人格；summary 用一兩句話總結平均報酬與信心；"
        "insight 給一句對其投資風格的觀察。記得只輸出 JSON。"
    )
