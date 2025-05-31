import numpy as np  # For generating sample embeddings
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth  # If using AWS OpenSearch Service with IAM

# --- 1. Configuration ---
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 443  # or 9200 if not using HTTPS
OPENSEARCH_USER = "shankha"  # or None if no auth or using AWS IAM
OPENSEARCH_PASSWORD = "choose_password"  # or None
INDEX_NAME = "embedding_index"
VECTOR_FIELD_NAME = "my_vector"
VECTOR_DIMENSION = 768

# --- Use AWS4Auth if on Amazon OpenSearch Service with IAM ---
import boto3

region = "your-aws-region"
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token,
)
http_auth_val = awsauth  # If using AWS IAM
# http_auth_val = (OPENSEARCH_USER, OPENSEARCH_PASSWORD) if OPENSEARCH_USER else None

# --- 2. Initialize OpenSearch Client ---
client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    http_auth=http_auth_val,
    use_ssl=True if OPENSEARCH_PORT == 443 else False,
    verify_certs=True,  # Set to False for self-signed certs in dev, not recommended for prod
    connection_class=RequestsHttpConnection,
    timeout=30,  # Optional: Increase timeout for larger requests
)


# --- 3. Define Index Mapping for k-NN ---
def create_index_with_knn_mapping():
    """
    This script demonstrates how to set up and use OpenSearch for k-NN vector search.

    It covers:
    1.  **Configuration**: Setting up OpenSearch connection parameters,
        including authentication (basic or AWS IAM).
    2.  **Client Initialization**: Creating an OpenSearch client instance.
    3.  **Index Creation**: Defining and creating an OpenSearch index with a
        k-NN vector field mapping, specifying algorithm (HNSW), space type,
        and engine.
    4.  **Data Preparation**: Generating sample documents with random vector
        embeddings and associated metadata.
    5.  **Bulk Indexing**: Indexing the generated documents into OpenSearch
        in bulk.

    The main execution block orchestrates these steps, creating the index if it
    doesn't exist, generating sample data, and then indexing it.
    """
    if not client.indices.exists(index=INDEX_NAME):
        index_body = {
            "settings": {
                "index": {
                    "knn": True,  # Enable k-NN for this index
                    "knn.algo_param.ef_search": 100,  # Optional: query-time parameter
                }
            },
            "mappings": {
                "properties": {
                    VECTOR_FIELD_NAME: {
                        "type": "knn_vector",
                        "dimension": VECTOR_DIMENSION,
                        "method": {  # Specifies the k-NN algorithm and its parameters
                            "name": "hnsw",  # Hierarchical Navigable Small Worlds
                            "space_type": "l2",  # Euclidean distance. Others: cosinesimil, innerproduct
                            "engine": "lucene",  # or "nmslib", "faiss"
                            "parameters": {
                                "ef_construction": 128,  # Index-time parameter for HNSW
                                "m": 24,  # Index-time parameter for HNSW
                            },
                        },
                    },
                    "text_content": {  # Example: Other metadata you might store
                        "type": "text"
                    },
                    "document_id": {"type": "keyword"},
                }
            },
        }
        try:
            client.indices.create(index=INDEX_NAME, body=index_body)
            print(f"Index '{INDEX_NAME}' created successfully.")
        except Exception as e:
            print(f"Error creating index '{INDEX_NAME}': {e}")
            raise
    else:
        print(f"Index '{INDEX_NAME}' already exists.")


# --- 4. Prepare Sample Embeddings and Documents ---
def generate_sample_documents(num_docs: int = 100):
    documents = []
    for i in range(num_docs):
        # Replace this with your actual embedding generation
        embedding = np.random.rand(VECTOR_DIMENSION).tolist()
        doc = {
            "_index": INDEX_NAME,
            "_id": f"doc_{i+1}",  # Optional: specify your own document ID
            "_source": {
                VECTOR_FIELD_NAME: embedding,
                "text_content": f"This is sample document number {i+1}.",
                "document_id": f"doc_{i+1}",
            },
        }
        documents.append(doc)
    return documents


# --- 5. Bulk Index the Documents ---
def bulk_index_documents(docs):
    try:
        successes, errors = helpers.bulk(
            client, docs, chunk_size=500, request_timeout=60
        )
        print(f"Successfully indexed {successes} documents.")
        if errors:
            print(f"Encountered errors during bulk indexing: {errors}")
        return successes, errors
    except Exception as e:
        print(f"Error during bulk indexing: {e}")
        raise


# --- Main Execution ---
if __name__ == "__main__":
    # Create index with k-NN mapping if it doesn't exist
    create_index_with_knn_mapping()

    # Generate some sample documents with embeddings
    print(
        f"\nGenerating {10} sample documents with {VECTOR_DIMENSION}-dimensional embeddings..."
    )
    sample_docs = generate_sample_documents(
        num_docs=10
    )  # Generate 10 docs for this example

    # Print one sample document to inspect
    if sample_docs:
        print("\nSample document to be indexed:")
        import json

        print(json.dumps(sample_docs[0], indent=2))

    # Bulk index the documents
    print(f"\nAttempting to bulk index {len(sample_docs)} documents...")
    bulk_index_documents(sample_docs)

    print(
        "\nTo verify, you can query the index using the OpenSearch Dashboards Dev Tools or the client:"
    )
    print(f"GET {INDEX_NAME}/_search")
    print(f"GET {INDEX_NAME}/_count")
