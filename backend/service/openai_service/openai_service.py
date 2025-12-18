import logging
import os
from openai import AzureOpenAI
from pydantic import BaseModel

class AzureOpenAIService:
    def __init__(self, client: AzureOpenAI) -> None:
        self.client = client
        # Read deployment names from environment and validate
        self.chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        missing = []
        if not self.chat_deployment:
            missing.append("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        if not self.embedding_deployment:
            missing.append("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        if missing:
            logging.error(f"Missing OpenAI deployment environment variables: {', '.join(missing)}")
            raise ValueError(f"Missing OpenAI deployment environment variables: {', '.join(missing)}")

    def getChatCompletion(self, messages, temperature, top_p):
        try:
            response = self.client.chat.completions.create(
                model = self.chat_deployment,
                messages = messages,
                temperature = float(temperature),
                top_p = float(top_p)
            )
            return response
        except Exception as e:
            logging.error(f"Error getting chat completion: {e}")
            raise e
        
    def getChatCompletionJsonStructureMode(self, messages, temperature, top_p, structure):
        try:
            response = self.client.chat.completions.parse(
                model = self.chat_deployment,
                messages = messages,
                response_format = structure,
                temperature = float(temperature),
                top_p = float(top_p),
            )
            return response
        except Exception as e:
            # Log more details for 404 NotFound errors from the service
            logging.error(f"Error getting chat completion with JSON structure: {e}")
            try:
                # openai client errors often have 'response' with status and data
                resp = getattr(e, 'response', None)
                if resp is not None:
                    logging.error(f"OpenAI response status: {getattr(resp, 'status_code', None)}, body: {getattr(resp, 'text', None)}")
            except Exception:
                pass
            return None
        
    def getEmbedding(self, input):
        try:
            response = self.client.embeddings.create(
                model = self.embedding_deployment,
                input = input
            )
            return response
        except Exception as e:
            logging.error(f"Error getting embedding: {e}")
            raise e