"""
Phase 3 — Merkezi araç kayıt ve çalıştırma sistemi.

Yeni bir özellik eklemek için sadece:
    1. Yeni tool fonksiyonunu yaz.
    2. tm.register() ile sisteme ekle.
    3. Komut parser'ında yönlendir.

Phase 4'te LLM, schema() çıktısını okuyarak hangi tool'u
çağıracağına karar verecek (function calling).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: Dict[str, str] = field(default_factory=dict)


class ToolManager:
    def __init__(self) -> None:
        self._registry: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, str]] = None,
    ) -> None:
        """Bir aracı sisteme kayıt eder."""
        self._registry[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {},
        )

    def execute(self, tool_name: str, **kwargs: Any) -> Any:
        """Kayıtlı bir aracı çalıştırır."""
        if tool_name not in self._registry:
            raise KeyError(
                f"'{tool_name}' aracı bulunamadı. "
                f"Mevcut araçlar: {self.list_tools()}"
            )
        return self._registry[tool_name].func(**kwargs)

    def list_tools(self) -> List[str]:
        """Kayıtlı araç isimlerini döndürür."""
        return list(self._registry.keys())

    def schema(self) -> List[Dict[str, Any]]:
        """
        Phase 4 LLM entegrasyonu için araç tanım şemasını döndürür.
        OpenAI / Ollama function calling formatına benzer yapı.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._registry.values()
        ]
