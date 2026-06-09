from dataclasses import dataclass, field


@dataclass
class Model:
    id: str
    display_name: str
    litellm_string: str
    is_recommended: bool = False


@dataclass
class Provider:
    id: str
    display_name: str
    auth_label: str
    models: list[Model] = field(default_factory=list)


@dataclass
class AppConfig:
    provider: str
    model: str
    api_key: str
    litellm_model_string: str

    @property
    def masked_key(self) -> str:
        if len(self.api_key) > 8:
            return self.api_key[:8] + "[REDACTED]"
        return "[REDACTED]"
