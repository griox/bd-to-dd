"""Phase 3 replacement tests: Gemini Dense Embedding Adapter.

Unit tests mock the Gemini client; no real API key or network call is required.
"""

import unittest
from typing import List
from unittest.mock import MagicMock, patch

from app.infrastructure.embedding.gemini_embedder import (
    GeminiEmbeddingService,
    InfrastructureError,
)


def _make_service(api_key: str = "test-key") -> GeminiEmbeddingService:
    return GeminiEmbeddingService(
        api_key=api_key,
        model="gemini-embedding-001",
        dimensions=1536,
    )


def _mock_gemini_response(vectors: List[List[float]]) -> MagicMock:
    response = MagicMock()
    response.embeddings = [MagicMock(values=vec) for vec in vectors]
    return response


class DescribeTest(unittest.TestCase):
    def test_describe_returns_gemini_metadata_without_network(self):
        service = _make_service()

        info = service.describe()

        self.assertEqual(info["provider"], "gemini")
        self.assertEqual(info["model"], "gemini-embedding-001")
        self.assertEqual(info["dimensions"], 1536)
        self.assertTrue(info["configured"])

    def test_describe_handles_missing_api_key(self):
        service = _make_service(api_key="")

        info = service.describe()

        self.assertFalse(info["configured"])


class EmbedDocumentsTest(unittest.TestCase):
    @patch("app.infrastructure.embedding.gemini_embedder.GeminiEmbeddingService._get_client")
    def test_embed_documents_calls_gemini_once_for_batch(self, mock_get_client):
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _mock_gemini_response(vectors)
        mock_get_client.return_value = mock_client

        result = _make_service().embed_documents(["doc A", "doc B"])

        self.assertEqual(result, vectors)
        mock_client.models.embed_content.assert_called_once()
        call_kwargs = mock_client.models.embed_content.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "gemini-embedding-001")
        self.assertEqual(call_kwargs["contents"], ["doc A", "doc B"])

    def test_empty_input_returns_empty_without_client_call(self):
        service = _make_service()

        result = service.embed_documents([])

        self.assertEqual(result, [])

    @patch("app.infrastructure.embedding.gemini_embedder.GeminiEmbeddingService._get_client")
    def test_embed_query_returns_single_vector(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _mock_gemini_response([[0.7, 0.8]])
        mock_get_client.return_value = mock_client

        result = _make_service().embed_query("search term")

        self.assertEqual(result, [0.7, 0.8])

    @patch("app.infrastructure.embedding.gemini_embedder.GeminiEmbeddingService._get_client")
    def test_embed_documents_splits_large_batches(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = [
            _mock_gemini_response([[0.1, 0.2] for _ in range(100)]),
            _mock_gemini_response([[0.3, 0.4] for _ in range(20)]),
        ]
        mock_get_client.return_value = mock_client
        service = GeminiEmbeddingService(
            api_key="test-key",
            model="gemini-embedding-001",
            dimensions=1536,
            batch_size=100,
        )

        result = service.embed_documents([f"doc-{index}" for index in range(120)])

        self.assertEqual(len(result), 120)
        self.assertEqual(mock_client.models.embed_content.call_count, 2)
        first_call = mock_client.models.embed_content.call_args_list[0].kwargs
        second_call = mock_client.models.embed_content.call_args_list[1].kwargs
        self.assertEqual(len(first_call["contents"]), 100)
        self.assertEqual(len(second_call["contents"]), 20)

    @patch("time.sleep")
    @patch("app.infrastructure.embedding.gemini_embedder.GeminiEmbeddingService._get_client")
    def test_retries_rate_limited_batch_after_provider_delay(
        self,
        mock_get_client,
        mock_sleep,
    ):
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = [
            _mock_gemini_response([[0.1, 0.2] for _ in range(100)]),
            RuntimeError("429 RESOURCE_EXHAUSTED. Please retry in 0s."),
            _mock_gemini_response([[0.3, 0.4] for _ in range(20)]),
        ]
        mock_get_client.return_value = mock_client
        service = GeminiEmbeddingService(
            api_key="test-key",
            model="gemini-embedding-001",
            dimensions=1536,
            batch_size=100,
        )

        result = service.embed_documents([f"doc-{index}" for index in range(120)])

        self.assertEqual(len(result), 120)
        self.assertEqual(mock_client.models.embed_content.call_count, 3)
        mock_sleep.assert_called_once_with(1)


class ErrorHandlingTest(unittest.TestCase):
    def test_missing_api_key_raises_infrastructure_error(self):
        service = _make_service(api_key="")

        with self.assertRaises(InfrastructureError) as ctx:
            service._get_client()

        self.assertIn("GEMINI_EMBEDDING_API_KEY", str(ctx.exception))

    @patch("app.infrastructure.embedding.gemini_embedder.GeminiEmbeddingService._get_client")
    def test_api_error_raises_infrastructure_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = RuntimeError("timeout")
        mock_get_client.return_value = mock_client

        with self.assertRaises(InfrastructureError) as ctx:
            _make_service().embed_documents(["doc"])

        self.assertIn("Gemini embed_documents failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
