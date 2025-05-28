import pytest

from enigma_engines.infrastructure.opensearch_setup import generate_sample_documents, VECTOR_DIMENSION, INDEX_NAME, VECTOR_FIELD_NAME

def test_generate_sample_documents():
    num_docs = 5
    docs = generate_sample_documents(num_docs=num_docs)
    assert len(docs) == num_docs
    for i, doc in enumerate(docs):
        assert doc["_index"] == INDEX_NAME
        assert doc["_id"] == f"doc_{i+1}"
        source = doc["_source"]
        assert VECTOR_FIELD_NAME in source
        assert isinstance(source[VECTOR_FIELD_NAME], list)
        assert len(source[VECTOR_FIELD_NAME]) == VECTOR_DIMENSION
        assert "text_content" in source
        assert source["text_content"] == f"This is sample document number {i+1}."
        assert "document_id" in source
        assert source["document_id"] == f"doc_{i+1}"
