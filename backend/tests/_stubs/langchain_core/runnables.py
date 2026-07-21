from typing import Any, Callable, Dict


class Runnable:
    def __class_getitem__(cls, item):
        return cls

    def invoke(self, payload: Any) -> Any:
        raise NotImplementedError

    def __or__(self, other):
        return _ComposedRunnable(self, other)

    def __ror__(self, other):
        if isinstance(other, Runnable):
            return _ComposedRunnable(other, self)
        return _ComposedRunnable(RunnableLambda(lambda _: other), self)


class _ComposedRunnable(Runnable):
    def __init__(self, left: Runnable, right) -> None:
        self.left = left
        self.right = right if isinstance(right, Runnable) else RunnableLambda(lambda _: right)

    def invoke(self, payload: Any) -> Any:
        return self.right.invoke(self.left.invoke(payload))


class RunnableLambda(Runnable):
    def __init__(self, func: Callable[[Any], Any]) -> None:
        self.func = func

    def invoke(self, payload: Any) -> Any:
        return self.func(payload)


class RunnablePassthrough(Runnable):
    def invoke(self, payload: Any) -> Any:
        return payload

    @classmethod
    def assign(cls, **assignments):
        def _assign(payload: Dict[str, Any]) -> Dict[str, Any]:
            result = dict(payload)
            for key, runnable in assignments.items():
                if isinstance(runnable, Runnable):
                    result[key] = runnable.invoke(payload)
                elif callable(runnable):
                    result[key] = runnable(payload)
                else:
                    result[key] = runnable
            return result

        return RunnableLambda(_assign)
