class ApplicationSpecificData:
    _instances: dict = {}

    def __init__(self, name, total_duration) -> None:
        self.name = name
        self.total_duration = total_duration

    def to_string(self) -> str:
        return f"The user has spent {self.total_duration:.0f} seconds on {self.name}"

    @classmethod
    def get_or_create(cls, name: str):
        if name not in cls._instances:
            cls._instances[name] = cls(name, 0)
        return cls._instances[name]
    
    @classmethod
    def clear_data(cls):
        cls._instances = {}

    @classmethod
    def get_all_instances_to_string(cls):
        tempStr = ""
        for instance in cls._instances.values():
            tempStr += f"{instance.to_string()}\n"
        return tempStr.rstrip()