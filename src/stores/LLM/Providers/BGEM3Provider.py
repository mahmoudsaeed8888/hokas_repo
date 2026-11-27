from ..LLMInterface import LLMInterface
from ..LLMEnums import DocumentTypeEnum , BGEM3Enums
import logging


class BGEM3Provider(LLMInterface):

    def __init__(self, default_input_max_characters: int = 1000,
                       default_generation_max_output_tokens: int = 1000,
                       default_generation_temperature: float = 0.1,
                       batch_size: int = 32,
                       device: str = None):

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.batch_size = batch_size
        self.device = device  # None = auto (cuda if available, else cpu)

        self.enums = BGEM3Enums

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.model = None

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

        # Load the model once at startup
        self.model = SentenceTransformer(model_id, device=self.device)

        real_size = self.model.get_sentence_embedding_dimension()
        if real_size != embedding_size:
            self.logger.warning(
                f"EMBEDDING_MODEL_SIZE={embedding_size} but the model outputs {real_size}. "
                f"Using the real size."
            )
            self.embedding_size = real_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def embed_text(self, text: str, document_type: str = None):
        if self.model is None:
            self.logger.error("Embedding model for BGE-M3 was not set")
            return None

        try:
            vector = self.model.encode(
                self.process_text(text),
                normalize_embeddings=True,
            )
        except Exception as e:
            self.logger.error(f"Error while embedding text with BGE-M3: {e}")
            return None

        return vector.tolist()

    def embed_texts(self, text, document_type: str = None, batch_size: int = None):
        if self.model is None:
            self.logger.error("Embedding model for BGE-M3 was not set")
            return None

        if isinstance(text, str):
            text = [text]

        try:
            vectors = self.model.encode(
                [self.process_text(t) for t in text],
                batch_size=batch_size or self.batch_size,
                normalize_embeddings=True,
            )
        except Exception as e:
            self.logger.error(f"Error while embedding texts with BGE-M3: {e}")
            return None

        return vectors.tolist()

    # Generation is not supported by this provider
    def generate_text(self, prompt: str, chat_history: list = [],
                      max_output_tokens: int = None, temperature: float = None):
        self.logger.error("BGEM3Provider does not support generation")
        return None

    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "text": prompt}