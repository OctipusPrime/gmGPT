from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import json

qdrant_client = QdrantClient(
    url="https://fdd4a708-5232-433e-a5f0-830c4eb7e177.eu-central-1-0.aws.cloud.qdrant.io:6333", 
    api_key="lr9JcrGVAJA3udCtchE21Byj4_vog4h_X0Xl1utfDa2Ut3g4k_e8Rw",
)

print(qdrant_client.retrieve(
    collection_name="summaries",
    ids=[1,2,3]
))