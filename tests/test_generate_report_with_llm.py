from __future__ import annotations

import copy
import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_report_with_codex as report_module


def make_response(
    content: str | None,
    *,
    finish_reason: str = "stop",
    reasoning_content: str | None = None,
) -> SimpleNamespace:
    reasoning_tokens = len(reasoning_content or "")
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(
                    content=content,
                    reasoning_content=reasoning_content,
                ),
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=reasoning_tokens + len(content or ""),
            total_tokens=100 + reasoning_tokens + len(content or ""),
            completion_tokens_details=SimpleNamespace(reasoning_tokens=reasoning_tokens),
        ),
    )


class FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []

    def create(self, **request: object) -> object:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class GenerateReportWithLlmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.top3 = [
            {
                "full_name": f"owner/repo-{index}",
                "html_url": f"https://github.com/owner/repo-{index}",
            }
            for index in range(1, 4)
        ]

    def run_generation(
        self,
        responses: list[object],
        *,
        verification_result: tuple[bool, list[str]] = (True, []),
        max_attempts: int | None = None,
    ) -> tuple[object, FakeCompletions, Mock, list[dict[str, object]], list[tuple[str, str]]]:
        completions = FakeCompletions(responses)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        openai_module = types.ModuleType("openai")
        openai_module.OpenAI = lambda **_: fake_client

        verify_mock = Mock(return_value=verification_result)
        verify_module = types.ModuleType("verify_report")
        verify_module.verify_report = verify_mock

        status_writes: list[dict[str, object]] = []
        text_writes: list[tuple[str, str]] = []
        config = {
            "llm": {
                "enabled": True,
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "base_url": "https://api.deepseek.com",
                "api_key_env": "TEST_DEEPSEEK_API_KEY",
                "thinking": "disabled",
                "max_output_tokens": 8000,
                "max_attempts": max_attempts or len(responses),
                "temperature": 0.4,
                "require_success": False,
            }
        }

        with (
            patch.dict(os.environ, {"TEST_DEEPSEEK_API_KEY": "test-key"}),
            patch.dict(sys.modules, {"openai": openai_module, "verify_report": verify_module}),
            patch.object(
                report_module,
                "write_json",
                side_effect=lambda _path, data: status_writes.append(copy.deepcopy(data)),
            ),
            patch.object(
                report_module,
                "write_text",
                side_effect=lambda path, text: text_writes.append((path, text)),
            ),
        ):
            result = report_module.generate_report_with_llm(self.top3, config, baseline=False)

        return result, completions, verify_mock, status_writes, text_writes

    def test_empty_content_is_detected_before_deterministic_sections_are_added(self) -> None:
        result, completions, verify_mock, statuses, text_writes = self.run_generation(
            [make_response("", finish_reason="length", reasoning_content="reasoning")],
            max_attempts=1,
        )

        self.assertIsNone(result)
        verify_mock.assert_not_called()
        self.assertEqual(text_writes, [("data/latest_llm_report_failed.md", "")])
        self.assertEqual(statuses[-1]["reason"], "LLM report generation returned empty text (finish_reason=length)")
        self.assertEqual(statuses[-1]["attempts"][0]["result"], "empty_content")
        self.assertEqual(statuses[-1]["attempts"][0]["reasoning_chars"], len("reasoning"))
        self.assertEqual(
            completions.requests[0]["extra_body"],
            {"thinking": {"type": "disabled"}},
        )

    def test_empty_first_attempt_is_retried_and_second_attempt_can_succeed(self) -> None:
        result, completions, verify_mock, statuses, _ = self.run_generation(
            [
                make_response("", finish_reason="length", reasoning_content="reasoning"),
                make_response("# 模型生成的报告"),
            ]
        )

        self.assertIsInstance(result, str)
        self.assertIn("# 模型生成的报告", result)
        self.assertEqual(len(completions.requests), 2)
        verify_mock.assert_called_once()
        self.assertEqual([attempt["result"] for attempt in statuses[-1]["attempts"]], ["empty_content", "success"])
        self.assertTrue(statuses[-1]["used_llm"])
        self.assertFalse(statuses[-1]["fallback"])

    def test_verification_failure_keeps_its_original_reason_for_fallback(self) -> None:
        result, _, _, statuses, text_writes = self.run_generation(
            [make_response("# 格式不合格的报告")],
            verification_result=(False, ["missing required headings"]),
            max_attempts=1,
        )

        self.assertIsNone(result)
        self.assertEqual(statuses[-1]["reason"], "LLM report failed verification")
        self.assertEqual(statuses[-1]["attempts"][0]["result"], "verification_failed")
        self.assertNotIn("unexpectedly", statuses[-1]["reason"])
        self.assertEqual(text_writes[-1][0], "data/latest_llm_report_failed.md")

    def test_generate_report_uses_a_locally_verified_fallback(self) -> None:
        from verify_report import verify_report

        config = {"report": {"title": "GitHub 趋势项目观察"}}
        with patch.object(report_module, "generate_report_with_llm", return_value=None):
            report = report_module.generate_report(self.top3, config, baseline=False)

        ok, errors = verify_report(report, self.top3)
        self.assertTrue(ok, errors)
        self.assertEqual(report.count("#### 项目简介"), 3)


if __name__ == "__main__":
    unittest.main()
