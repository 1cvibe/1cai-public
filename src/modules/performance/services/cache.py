import logging
import numpy as np
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class SemanticCacheANN:
    """Семантический кэш с Approximate Nearest Neighbor (ANN) поиском."""

    def __init__(
        self, index_type: str = "linear", dimension: int = 384, max_size: int = 10000
    ):
        self.index_type = index_type
        self.dimension = dimension
        self.max_size = max_size
        self.index = None
        self.embeddings = []
        self.texts = []
        self._rebuild_threshold = 0.8  # Перестроить индекс при 80% заполнения
        self._build_index()

    def _build_index(self):
        """Построить ANN индекс."""
        if self.index_type == "linear":
            # Линейный поиск (fallback)
            self.index = None
        elif self.index_type == "faiss":
            try:
                import faiss

                # HNSW индекс для быстрого поиска
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                self.index.hnsw.efConstruction = 200
                logger.info("FAISS HNSW index initialized")
            except ImportError:
                logger.warning("FAISS not available, falling back to linear search")
                self.index = None
        elif self.index_type == "hnswlib":
            try:
                import hnswlib

                self.index = hnswlib.Index(space="cosine", dim=self.dimension)
                self.index.init_index(max_elements=10000, ef_construction=200, M=16)
                logger.info("HNSWlib index initialized")
            except ImportError:
                logger.warning("HNSWlib not available, falling back to linear search")
                self.index = None
        else:
            self.index = None

    def add(self, embedding: List[float], text: str):
        """Добавить embedding в индекс.
        
        Args:
            embedding: Векторное представление.
            text: Исходный текст.
        """
        try:
            if not embedding:
                logger.warning("Empty embedding provided to ANN cache")
                return

            if not isinstance(embedding, list):
                logger.warning(f"Invalid embedding type: {type(embedding)}")
                return

            if len(embedding) != self.dimension:
                logger.warning(
                    f"Embedding dimension mismatch: {len(embedding)} != {self.dimension}"
                )
                return

            if not isinstance(text, str):
                logger.warning(f"Invalid text type: {type(text)}")
                return

            # Проверяем размер и удаляем старые записи если нужно
            if len(self.embeddings) >= self.max_size:
                # Удаляем самые старые (FIFO)
                self.embeddings.pop(0)
                self.texts.pop(0)
                # Перестраиваем индекс если используется
                if self.index is not None and len(self.embeddings) > 0:
                    self._rebuild_index()

            self.embeddings.append(embedding)
            self.texts.append(text)

            # Инкрементальное обновление индекса
            if self.index is not None:
                try:
                    if self.index_type == "faiss":
                        pass

                        # Проверяем, нужно ли перестроить индекс
                        if len(self.embeddings) % 100 == 0:  # Каждые 100 записей
                            self._rebuild_index()
                        else:
                            embedding_array = np.array([embedding], dtype=np.float32)
                            self.index.add(embedding_array)
                    elif self.index_type == "hnswlib":
                        # HNSWlib поддерживает инкрементальное добавление
                        self.index.add_items(
                            np.array([embedding], dtype=np.float32),
                            [len(self.embeddings) - 1],
                        )
                except Exception as e:
                    logger.warning(
                        f"Error adding to ANN index: {e}, rebuilding index",
                        exc_info=True,
                    )
                    self._rebuild_index()
        except Exception as e:
            logger.error(f"Error adding embedding to ANN cache: {e}", exc_info=True)

    def _rebuild_index(self):
        """Перестроить индекс с нуля."""
        try:
            if not self.embeddings:
                return

            self._build_index()

            # Добавляем все embeddings заново
            if self.index is not None:
                if self.index_type == "faiss":
                    pass

                    embeddings_array = np.array(self.embeddings, dtype=np.float32)
                    self.index.add(embeddings_array)
                elif self.index_type == "hnswlib":
                    embeddings_array = np.array(self.embeddings, dtype=np.float32)
                    labels = list(range(len(self.embeddings)))
                    self.index.add_items(embeddings_array, labels)

            logger.debug(f"Rebuilt ANN index with {len(self.embeddings)} embeddings")
        except Exception as e:
            logger.warning(f"Error rebuilding ANN index: {e}", exc_info=True)

    def search(
        self, query_embedding: List[float], k: int = 1, threshold: float = 0.95
    ) -> Optional[Tuple[List[float], float, str]]:
        """Поиск похожих embeddings.
        
        Args:
            query_embedding: Вектор запроса.
            k: Количество соседей.
            threshold: Порог схожести.
            
        Returns:
            Кортеж (найденный эмбеддинг, схожесть, текст) или None.
        """
        if not self.embeddings:
            return None

        if self.index is None:
            return self._linear_search(query_embedding, threshold)

        try:
            if self.index_type == "faiss":
                pass

                query_array = np.array([query_embedding], dtype=np.float32)
                self.index.hnsw.efSearch = 64
                distances, indices = self.index.search(
                    query_array, min(k, len(self.embeddings))
                )

                if len(indices[0]) > 0 and distances[0][0] < (1 - threshold):
                    idx = indices[0][0]
                    similarity = 1.0 - distances[0][0]
                    return self.embeddings[idx], similarity, self.texts[idx]

            elif self.index_type == "hnswlib":
                self.index.set_ef(64)
                labels, distances = self.index.knn_query(
                    np.array([query_embedding], dtype=np.float32),
                    k=min(k, len(self.embeddings)),
                )

                if len(labels[0]) > 0:
                    idx = labels[0][0]
                    similarity = 1.0 - distances[0][0]
                    if similarity >= threshold:
                        return self.embeddings[idx], similarity, self.texts[idx]

        except Exception as e:
            logger.warning("Error in ANN search: %s, falling back to linear", e)
            return self._linear_search(query_embedding, threshold)

        return None

    def _linear_search(
        self, query: List[float], threshold: float
    ) -> Optional[Tuple[List[float], float, str]]:
        """Fallback: линейный поиск."""
        best_similarity = 0.0
        best_embedding = None
        best_text = None

        query_np = np.array(query, dtype=np.float32)
        query_norm = np.linalg.norm(query_np)

        if query_norm == 0:
            return None

        for i, emb in enumerate(self.embeddings):
            emb_np = np.array(emb, dtype=np.float32)
            emb_norm = np.linalg.norm(emb_np)

            if emb_norm == 0:
                continue

            similarity = np.dot(query_np, emb_np) / (query_norm * emb_norm)

            if similarity > best_similarity:
                best_similarity = similarity
                best_embedding = emb
                best_text = self.texts[i]

        if best_similarity >= threshold:
            return best_embedding, best_similarity, best_text

        return None

    def clear(self):
        """Очистить индекс."""
        self.embeddings = []
        self.texts = []
        if self.index is not None:
            self._build_index()
