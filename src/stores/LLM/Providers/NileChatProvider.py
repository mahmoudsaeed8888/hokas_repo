from ..LLMInterface import LLMInterface
from ..LLMEnums import DocumentTypeEnum , NileChatEnums
from openai import OpenAI
import logging


class NileChatProvider(LLMInterface):

    ROLE_MAP = {
        "USER": "user", "CHATBOT": "assistant", "SYSTEM": "system",
        "user": "user", "assistant": "assistant", "system": "system",
    }

    def __init__(self, base_url: str = "http://localhost:8000/v1",
                       api_key: str = "EMPTY",
                       default_input_max_characters: int = 1000,
                       default_generation_max_output_tokens: int = 1000,
                       default_generation_temperature: float = 0.1):

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.enums = NileChatEnums

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def _build_messages(self, prompt: str, chat_history: list):
        system_parts, messages = [], []

        for m in chat_history or []:
            role = self.ROLE_MAP.get(m.get("role"), "user")
            content = m.get("content") or m.get("text") or ""
            if role == "system":
                system_parts.append(content)
            else:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": self.process_text(prompt)})

        # Some chat templates don't support a system role,
        # so merge the system text into the first user message.
        if system_parts:
            first_user = next(m for m in messages if m["role"] == "user")
            first_user["content"] = "\n".join(system_parts) + "\n\n" + first_user["content"]

        return messages

    def generate_text(self, prompt: str, chat_history: list = [],
                      max_output_tokens: int = None, temperature: float = None):

        if not self.generation_model_id:
            self.logger.error("Generation model for NileChat was not set")
            return None

        max_output_tokens = (max_output_tokens if max_output_tokens is not None
                             else self.default_generation_max_output_tokens)
        temperature = (temperature if temperature is not None
                       else self.default_generation_temperature)

        try:
            response = self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=self._build_messages(prompt, chat_history),
                temperature=temperature,
                max_tokens=max_output_tokens,
            )
        except Exception as e:
            self.logger.error(f"Error while generating text with NileChat: {e}")
            return None

        if not response or not response.choices or not response.choices[0].message.content:
            self.logger.error("Empty response from NileChat")
            return None

        return response.choices[0].message.content

    # Embeddings stay on your multilingual embedding provider
    def embed_text(self, text: str, document_type: str = None):
        self.logger.error("NileChatProvider does not support embeddings")
        return None

    def embed_texts(self, text, document_type: str = None, batch_size: int = 32):
        self.logger.error("NileChatProvider does not support embeddings")
        return None

    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "text": prompt}