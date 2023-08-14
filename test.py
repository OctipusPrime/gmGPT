from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import json

qdrant_client = QdrantClient(
    url="https://fdd4a708-5232-433e-a5f0-830c4eb7e177.eu-central-1-0.aws.cloud.qdrant.io:6333", 
    api_key="lr9JcrGVAJA3udCtchE21Byj4_vog4h_X0Xl1utfDa2Ut3g4k_e8Rw",
)

qdrant_client.recreate_collection(collection_name="full_conversation", vectors_config=VectorParams(size=1536, distance=Distance.COSINE))

qdrant_client.recreate_collection(collection_name="summaries", vectors_config=VectorParams(size=384, distance=Distance.COSINE))

print(qdrant_client.get_collections())

print(qdrant_client.get_collection(collection_name = "summaries"))