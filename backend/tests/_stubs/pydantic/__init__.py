class BaseModel:
    def __init__(self, **data) -> None:
        for key, value in data.items():
            setattr(self, key, value)
