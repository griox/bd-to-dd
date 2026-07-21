import unittest


class DependencyWiringTest(unittest.TestCase):
    def test_knowledge_base_uses_gemini_embedding_adapter(self):
        from app.presentation import deps

        info = deps.knowledge_base.dense_embedding_service.describe()

        self.assertEqual(info["provider"], "gemini")
        self.assertEqual(info["model"], "gemini-embedding-001")


if __name__ == "__main__":
    unittest.main()
