from .runnables import RunnableLambda


class ChatPromptTemplate:
    @classmethod
    def from_messages(cls, messages):
        return RunnableLambda(lambda payload: payload)
