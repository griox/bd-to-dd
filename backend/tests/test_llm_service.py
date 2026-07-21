import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from app.core.config import normalize_llm_model
from app.infrastructure.langchain.chains import LLMService


class LLMServiceTest(unittest.TestCase):
    def test_normalize_llm_model_maps_legacy_gemini_pro(self):
        self.assertEqual(normalize_llm_model("gemini-pro"), "gemini-2.5-flash")
        self.assertEqual(normalize_llm_model("gemini-2.5-flash"), "gemini-2.5-flash")

    def test_service_stays_disabled_without_gemini_or_google_key(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_EMBEDDING_API_KEY": "embedding-only"},
            clear=True,
        ):
            with patch("app.infrastructure.langchain.chains.LLM_API_KEY", "dummy"):
                service = LLMService()

        self.assertFalse(service.enabled)
        self.assertIsNone(service.client)

    def test_build_json_chain_falls_back_when_provider_raises(self):
        service = LLMService()
        service.client = RunnableLambda(
            lambda _: (_ for _ in ()).throw(RuntimeError("provider failure"))
        )

        chain = service.build_json_chain(
            system_prompt="Return JSON",
            user_prompt="{value}",
            fallback=lambda payload: {"source": "fallback", "value": payload["value"]},
        )

        result = chain.invoke({"value": "ok"})
        self.assertEqual(
            result,
            {"source": "fallback", "value": "ok"},
        )

    def test_build_json_chain_retries_once_after_invalid_json(self):
        service = LLMService()
        responses = iter(
            [
                "",
                '{"source": "gemini"}',
            ]
        )
        service.client = RunnableLambda(lambda _: next(responses))

        chain = service.build_json_chain(
            system_prompt="Return JSON",
            user_prompt="{value}",
            fallback=lambda _: {"source": "fallback"},
        )

        result = chain.invoke({"value": "ok"})

        self.assertEqual(result, {"source": "gemini"})

    def test_build_json_chain_falls_back_after_two_invalid_json_outputs(self):
        service = LLMService()
        call_count = {"provider": 0}

        def invalid_json(_):
            call_count["provider"] += 1
            return ""

        service.client = RunnableLambda(invalid_json)
        chain = service.build_json_chain(
            system_prompt="Return JSON",
            user_prompt="{value}",
            fallback=lambda _: {"source": "fallback"},
        )

        result = chain.invoke({"value": "ok"})

        self.assertEqual(result, {"source": "fallback"})
        self.assertEqual(call_count["provider"], 2)


if __name__ == "__main__":
    unittest.main()
