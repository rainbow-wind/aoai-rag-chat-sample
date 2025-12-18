import os 
import logging
import azure.cosmos.cosmos_client as CosmosClient

COSMOSDB_URI = os.getenv("COSMOSDB_URI")
COSMOSDB_KEY = os.getenv("COSMOSDB_KEY")
DATABASE_NAME = os.getenv("COSMOSDB_DATABASE_NAME")
CONTAINER_NAME = os.getenv("COSMOSDB_CONTAINER_NAME")

class CosmosService:
    def __init__(self):
        missing = []
        if not COSMOSDB_URI:
            missing.append('COSMOSDB_URI')
        if not COSMOSDB_KEY:
            missing.append('COSMOSDB_KEY')
        if not DATABASE_NAME:
            missing.append('COSMOSDB_DATABASE_NAME')
        if not CONTAINER_NAME:
            missing.append('COSMOSDB_CONTAINER_NAME')

        if missing:
            logging.error(f"Missing required Cosmos DB environment variables: {', '.join(missing)}")
            raise ValueError(f"Missing required Cosmos DB environment variables: {', '.join(missing)}")

        self.client = CosmosClient.CosmosClient(COSMOSDB_URI, {'masterKey': COSMOSDB_KEY})
        self.database = self.client.get_database_client(DATABASE_NAME)
        self.container = self.database.get_container_client(CONTAINER_NAME)
        logging.info(f"COSMOS_URI: {COSMOSDB_URI}, Connected to Cosmos DB: {DATABASE_NAME}, Container: {CONTAINER_NAME}")

    def insert_data(self, data):
        # Sanitize data to ensure JSON serializable before sending to Cosmos
        try:
            # Attempt a quick json.dumps to detect non-serializable fields
            import json as _json
            _json.dumps(data)
            sanitized = data
        except Exception:
            # Walk the dict and coerce known problematic types (e.g., SDK response objects)
            def _sanitize(o):
                if isinstance(o, dict):
                    return {k: _sanitize(v) for k, v in o.items()}
                if isinstance(o, (list, tuple)):
                    return [_sanitize(v) for v in o]
                # If object has 'embedding' attribute that's list-like, extract it
                if hasattr(o, 'embedding'):
                    try:
                        return list(o.embedding)
                    except Exception:
                        return None
                # If object has 'data' attribute, try to extract embeddings
                if hasattr(o, 'data'):
                    try:
                        out = []
                        for item in o.data:
                            if hasattr(item, 'embedding'):
                                out.append(list(item.embedding))
                            else:
                                out.append(_sanitize(item))
                        return out
                    except Exception:
                        return None
                # Fallback: try to convert to primitive
                try:
                    return str(o)
                except Exception:
                    return None

            sanitized = _sanitize(data)

        response = self.container.upsert_item(sanitized)
        logging.info(f"Document upserted: {sanitized}")

    def get_data(self, query):
        try:
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            logging.info(f"Query returned {len(items)} items.")
            return items
        except Exception as e:
            logging.error(f"Error querying documents: {e}")
            raise

    def delete_data(self, item_id):
        return self.container.delete_item(item=item_id, partition_key=item_id)
    
    def update_data(self, query, data):
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        for item in items:
            self.container.replace_item(item, data)
        logging.info(f"Updated {len(items)} items matching query: {query}")
        return items