class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class BackgroundTasks:
    def __init__(self) -> None:
        self.tasks = []

    def add_task(self, func, *args, **kwargs) -> None:
        self.tasks.append((func, args, kwargs))


class UploadFile:
    def __init__(self, file=None, filename: str = "", headers=None) -> None:
        self.file = file
        self.filename = filename
        self.headers = headers or {}
        self.content_type = self.headers.get("content-type")


def File(*args, **kwargs):
    return None


def Form(*args, **kwargs):
    return None


class APIRouter:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def get(self, *args, **kwargs):
        def _decorator(func):
            return func
        return _decorator

    def post(self, *args, **kwargs):
        def _decorator(func):
            return func
        return _decorator


class FastAPI:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def include_router(self, router):
        return None

    def add_middleware(self, *args, **kwargs):
        return None
