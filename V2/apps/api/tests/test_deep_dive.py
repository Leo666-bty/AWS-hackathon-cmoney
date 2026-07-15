"""AI Deep Dive language, ownership and evidence guardrail tests.

The fake Bedrock client keeps the suite deterministic and proves that provider
output cannot take ownership of server metadata or leak an English report into
the zh-TW product surface.
"""

from __future__ import annotations

import json
from typing import Any

from mindfolio_api.ai.deep_dive import PROMPT_VERSION, cache_key, generate_report
from mindfolio_api.config import Settings


class FakeBedrockClient:
    def __init__(self, payload: dict[str, Any] | list[dict[str, Any]]):
        self.payloads = payload if isinstance(payload, list) else [payload]
        self.request: dict[str, Any] | None = None
        self.requests: list[dict[str, Any]] = []

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.request = kwargs
        self.requests.append(kwargs)
        payload = self.payloads[min(len(self.requests) - 1, len(self.payloads) - 1)]
        return {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(payload, ensure_ascii=False)}],
                },
            },
        }


def _context() -> dict[str, Any]:
    return {
        "context_version": "investment-ai-context-v2",
        "model_version": "2025-v1",
        "content_sha256": "a" * 64,
        "result": {
            "persona_name": "深潛集中派",
            "average_return": 50.51,
            "confidence": 78,
        },
        "trades": [
            {
                "stock_id": "6770",
                "name": "力積電",
                "buy_month": "2025-01",
                "return_pct": 136.47,
                "trade_ref": "trade:0",
                "market_ref": "market:6770:2025-01",
            },
            {
                "stock_id": "2382",
                "name": "廣達",
                "buy_month": "2025-01",
                "return_pct": 2.14,
                "trade_ref": "trade:1",
                "market_ref": "market:2382:2025-01",
            },
        ],
        "evidence": {
            "trade:0": {"return_pct": 136.47},
            "trade:1": {"return_pct": 2.14},
            "market:6770:2025-01": {
                "regime_label": "法人資金偏多",
                "anomaly_level": "general",
                "anomaly_score": 0.7796,
                "evidence": {
                    "monthly_return": 0.270701,
                    "institutional_net": -11412.219,
                    "institutional_flow_ratio": -0.037026,
                },
            },
            "market:2382:2025-01": {
                "regime_label": "盤整觀察",
                "anomaly_level": "general",
                "anomaly_score": 0.7148,
                "evidence": {
                    "monthly_return": -0.037493,
                    "institutional_net": -87701.923,
                    "institutional_flow_ratio": -0.236136,
                },
            },
        },
        "display_facts": {
            "portfolio": {
                "persona_name": "深潛集中派",
                "average_reconstruction_return": "50.5%",
                "data_confidence_score": "78",
            },
            "trades": {
                "trade:0": {
                    "stock_id": "6770",
                    "stock_name": "力積電",
                    "buy_month": "2025-01",
                    "holding_period_reconstruction_return": "136.5%",
                },
                "trade:1": {
                    "stock_id": "2382",
                    "stock_name": "廣達",
                    "buy_month": "2025-01",
                    "holding_period_reconstruction_return": "2.1%",
                },
            },
            "markets": {
                "market:6770:2025-01": {
                    "stock_id": "6770",
                    "stock_name": "力積電",
                    "buy_month": "2025-01",
                    "buy_month_label": "2025 年 1 月",
                    "market_regime_cluster_label": "法人資金偏多",
                    "anomaly_level": "general",
                    "anomaly_interpretation": "一般級，不得描述為異常事件或高度異常",
                    "anomaly_score": "0.780",
                    "market_monthly_return": "27.1%",
                    "institutional_net": "-11,412",
                    "institutional_direction": "法人淨流出",
                    "institutional_flow_ratio": "-3.7%",
                },
                "market:2382:2025-01": {
                    "stock_id": "2382",
                    "stock_name": "廣達",
                    "buy_month": "2025-01",
                    "buy_month_label": "2025 年 1 月",
                    "market_regime_cluster_label": "盤整觀察",
                    "anomaly_level": "general",
                    "anomaly_interpretation": "一般級，不得描述為異常事件或高度異常",
                    "anomaly_score": "0.715",
                    "market_monthly_return": "-3.7%",
                    "institutional_net": "-87,702",
                    "institutional_direction": "法人淨流出",
                    "institutional_flow_ratio": "-23.6%",
                },
            },
        },
    }


def _zh_tw_payload() -> dict[str, Any]:
    return {
        "title": "五檔交易呈現深潛集中派的投資輪廓",
        "executive_summary": (
            "五檔交易的平均重建報酬為 50.5%，資料信心分數為 78。"
            "這是歷史情境重建，不代表未來績效。"
        ),
        "strengths": [{
            "title": "主要報酬貢獻",
            "body": "力積電的持有期間重建報酬為 136.5%，是五檔中最突出的一筆。",
            "evidence_refs": ["trade:0"],
        }],
        "watchouts": [{
            "title": "值得回看的交易",
            "body": "廣達的持有期間重建報酬為 2.1%，其買進月份市場月報酬為負。",
            "evidence_refs": ["trade:1", "market:2382:2025-01"],
        }],
        "market_moments": [{
            "title": "買進月份市場情境",
            "body": "力積電所屬的市場情境群集標記為法人資金偏多，但當月法人淨流量為負。",
            "evidence_refs": ["market:6770:2025-01"],
        }],
    }


def _settings() -> Settings:
    return Settings(bedrock_enabled=True, bedrock_model_id="fake.model-v1")


def test_valid_zh_tw_content_uses_server_owned_metadata_and_question_labels() -> None:
    client = FakeBedrockClient(_zh_tw_payload())

    report = generate_report(_context(), client, _settings())

    assert report.source == "bedrock"
    assert report.versions == {
        "context": "investment-ai-context-v2",
        "model": "2025-v1",
        "prompt": PROMPT_VERSION,
    }
    assert [(item.id, item.label) for item in report.suggested_questions] == [
        ("why-persona", "為什麼我是這種投資人格？"),
        ("most-influential-trade", "哪筆交易最影響結果？"),
        ("why-anomalous-month", "哪個買進月份最不尋常？"),
    ]
    assert client.request is not None
    prompt = client.request["messages"][0]["content"][0]["text"]
    assert "台灣繁體中文" in prompt
    assert "資料信心分數" in prompt
    assert "持有期間重建報酬" in prompt
    assert "市場情境群集標籤" in prompt
    assert "anomaly_level" in prompt
    assert "evidence_keys" in prompt
    assert "136.5%" in prompt
    assert "136.47" not in prompt


def test_english_content_is_rejected_and_uses_chinese_fallback() -> None:
    payload = _zh_tw_payload()
    payload.update({
        "title": "2025 Annual Holding Review for a Deep Concentrated Portfolio",
        "executive_summary": "The portfolio achieved a strong average return with a confidence level of 78.",
    })
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"
    assert "歷史資料回顧" in report.executive_summary


def test_english_paragraphs_with_chinese_stock_names_are_still_rejected() -> None:
    payload = _zh_tw_payload()
    payload["executive_summary"] = (
        "The portfolio held 力積電 and 廣達 throughout 2025 and achieved an average "
        "return of 50.51 percent with a confidence level of 78."
    )
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"


def test_unknown_evidence_reference_is_rejected() -> None:
    payload = _zh_tw_payload()
    payload["strengths"][0]["evidence_refs"] = ["market:9999:2025-01"]
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"


def test_number_not_preformatted_by_backend_is_rejected() -> None:
    payload = _zh_tw_payload()
    payload["strengths"][0]["body"] = (
        "力積電的持有期間重建報酬為 136.47%，這個精度不是後端允許的顯示值。"
    )
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"


def test_negative_institutional_flow_cannot_be_reframed_as_bullish() -> None:
    payload = _zh_tw_payload()
    payload["market_moments"][0]["body"] = (
        "力積電當月法人流向有利，顯示法人實際淨流入並支撐後續表現。"
    )
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"


def test_general_anomaly_level_cannot_be_called_highly_anomalous() -> None:
    payload = _zh_tw_payload()
    payload["market_moments"][0]["body"] = (
        "力積電買進月份出現高度異常事件，是五檔中需要特別注意的偏離。"
    )
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "fallback"


def test_benign_trade_contribution_language_does_not_force_fallback() -> None:
    payload = _zh_tw_payload()
    payload["strengths"][0]["body"] = (
        "力積電的持有期間重建報酬為 136.5%，是五檔中的主要貢獻並帶動整體結果。"
    )
    client = FakeBedrockClient(payload)

    report = generate_report(_context(), client, _settings())

    assert report.source == "bedrock"


def test_guardrail_rejection_gets_one_repair_attempt() -> None:
    english = _zh_tw_payload()
    english["title"] = "2025 Annual Holding Review"
    english["executive_summary"] = (
        "The portfolio achieved a strong average return with a confidence level of 78."
    )
    client = FakeBedrockClient([english, _zh_tw_payload()])

    report = generate_report(_context(), client, _settings())

    assert report.source == "bedrock"
    assert len(client.requests) == 2
    retry_prompt = client.requests[1]["messages"][0]["content"][0]["text"]
    assert "language" in retry_prompt


def test_deep_dive_prompt_version_invalidates_previous_cached_report() -> None:
    context = _context()

    assert PROMPT_VERSION == "investment-report-v2-zh-tw"
    assert cache_key(context).endswith("|investment-report-v2-zh-tw")
