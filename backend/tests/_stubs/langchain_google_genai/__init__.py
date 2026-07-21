class ChatGoogleGenerativeAI:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def invoke(self, payload):
        return payload
