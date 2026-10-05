"""Vectorización dispersa de las descripciones de poderes."""

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


def vectorizar_tfidf(
    textos: list[str], min_df: int = 2, max_features: int | None = 5000
) -> tuple[TfidfVectorizer, csr_matrix]:
    """Ajusta TF-IDF en inglés y conserva una fila por texto."""
    vectorizador = TfidfVectorizer(
        stop_words="english", min_df=min_df, max_features=max_features
    )
    return vectorizador, vectorizador.fit_transform(textos).tocsr()


def vectorizar_bolsa(
    textos: list[str], min_df: int = 2, max_features: int | None = 5000
) -> tuple[CountVectorizer, csr_matrix]:
    """Cuenta tokens sin stop words, con el mismo vocabulario base que TF-IDF."""
    vectorizador = CountVectorizer(
        stop_words="english", min_df=min_df, max_features=max_features
    )
    return vectorizador, vectorizador.fit_transform(textos).tocsr()
