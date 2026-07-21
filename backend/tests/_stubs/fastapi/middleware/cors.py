class CORSMiddleware:
    def __init__(self, app=None, **kwargs) -> None:
        self.app = app
        self.kwargs = kwargs
