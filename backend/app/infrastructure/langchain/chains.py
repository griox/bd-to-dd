import json
import time
from typing import Any, Callable, Dict

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import LLM_API_KEY, LLM_MODEL
from app.core.logging import logger

MAX_JSON_ATTEMPTS = 2


class LLMService:
    def __init__(self) -> None:
        self.enabled = LLM_API_KEY != "dummy"
        self.client = None
        if self.enabled:
            self.client = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                google_api_key=LLM_API_KEY,
                retries=1,
                timeout=120,
            )

    def build_json_chain(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Callable[[Dict[str, Any]], Dict[str, Any]],
        chain_name: str = "unnamed",
    ) -> Runnable[Dict[str, Any], Dict[str, Any]]:
        if not self.client:
            def invoke_disabled(payload: Dict[str, Any]) -> Dict[str, Any]:
                logger.warning(
                    "[llm_call] chain=%s provider=disabled model=%s event=fallback payload_keys=%s",
                    chain_name,
                    LLM_MODEL,
                    sorted(payload.keys()),
                )
                return fallback(payload)

            return RunnableLambda(invoke_disabled)
        chain = (
            ChatPromptTemplate.from_messages(
                [("system", system_prompt), ("user", user_prompt)]
            )
            | self.client
            | JsonOutputParser()
            | RunnableLambda(lambda payload: json.loads(json.dumps(payload)))
        )

        def invoke_or_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
            for attempt in range(1, MAX_JSON_ATTEMPTS + 1):
                started_at = time.perf_counter()
                logger.info(
                    "[llm_call] chain=%s provider=gemini model=%s event=invoke_start attempt=%s/%s payload_keys=%s",
                    chain_name,
                    LLM_MODEL,
                    attempt,
                    MAX_JSON_ATTEMPTS,
                    list(payload.keys()),
                )
                try:
                    result = chain.invoke(payload)
                    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    logger.info(
                        "[llm_call] chain=%s provider=gemini model=%s event=invoke_success attempt=%s elapsed_ms=%s result_keys=%s",
                        chain_name,
                        LLM_MODEL,
                        attempt,
                        elapsed_ms,
                        sorted(result.keys()) if isinstance(result, dict) else [],
                    )
                    return result
                except (json.JSONDecodeError, OutputParserException) as exc:
                    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    if attempt < MAX_JSON_ATTEMPTS:
                        logger.warning(
                            "[llm_call] chain=%s provider=gemini model=%s event=json_retry attempt=%s elapsed_ms=%s error=%s",
                            chain_name,
                            LLM_MODEL,
                            attempt,
                            elapsed_ms,
                            exc,
                        )
                        continue
                    logger.exception(
                        "[llm_call] chain=%s provider=gemini model=%s event=invoke_failed attempts=%s elapsed_ms=%s fallback=true error=%s",
                        chain_name,
                        LLM_MODEL,
                        attempt,
                        elapsed_ms,
                        exc,
                    )
                    return fallback(payload)
                except Exception as exc:
                    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    logger.exception(
                        "[llm_call] chain=%s provider=gemini model=%s event=invoke_failed attempt=%s elapsed_ms=%s fallback=true error=%s",
                        chain_name,
                        LLM_MODEL,
                        attempt,
                        elapsed_ms,
                        exc,
                    )
                    return fallback(payload)

            return fallback(payload)

        return RunnableLambda(invoke_or_fallback)

    def invoke_json(self, system_prompt: str, user_prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("LLM is not configured")
        chain = self.build_json_chain(system_prompt, user_prompt, lambda _: {}, "invoke_json")
        result = chain.invoke(payload)
        return json.loads(json.dumps(result))
