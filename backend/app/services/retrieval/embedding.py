import math
import threading


def normalize(vector):
    values = [float(x) for x in vector]
    length = math.sqrt(sum(x * x for x in values))
    if not values or not math.isfinite(length) or length == 0:
        raise ValueError("Invalid embedding")
    return [x / length for x in values]


class LocalEmbedding:
    """Real multilingual ONNX embedding on CPU; no LLM or paid API calls."""

    def __init__(self, settings):
        self.model_name = settings.embedding_model
        self.cache_dir = settings.embedding_cache_dir
        self._model = None
        self._lock = threading.Lock()

    def embed(self, texts: list[str], *, query: bool = False):
        from fastembed import TextEmbedding

        with self._lock:
            if self._model is None:
                self._model = TextEmbedding(
                    model_name=self.model_name, cache_dir=self.cache_dir, threads=2, max_length=512
                )
            # E5 requires these prefixes for retrieval, including multilingual inputs.
            prefix = (
                ("query: " if query else "passage: ")
                if "/multilingual-e5-" in self.model_name
                else ""
            )
            return [
                normalize(v)
                for v in self._model.embed([prefix + text for text in texts], batch_size=16)
            ]
