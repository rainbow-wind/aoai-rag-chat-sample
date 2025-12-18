import azure.functions as func
import pymupdf
from openai import AzureOpenAI

import os
from io import BytesIO
import logging
import tempfile
import base64
import json
from urllib.parse import urlparse
from PIL import Image

from azure.storage.blob import BlobServiceClient

from service.openai_service.openai_service import AzureOpenAIService
from service.cosmos_service.cosmos_service import CosmosService
from domain.obj_cosmos_page import CosmosPageObj
from domain.document_structure import DocumentStructure

logging.basicConfig(level=logging.INFO)
app = func.FunctionApp()

STR_AI_SYSTEMMESSAGE = """
##制約条件
- 画像内の情報を、Markdown形式に整理しなさい。
- 図や表が含まれる場合、図や表の内容を理解できるように説明する文章にしなさい。
- 回答形式 以外の内容は記載しないでください。
- 回答の最初に「```json」を含めないこと。

##回答形式##
{
    "content":"画像をテキストに変換した文字列",
    "keywords": "カンマ区切りのキーワード群",
    "is_contain_image": "図や表などの画像で保存しておくべき情報が含まれている場合はtrue、それ以外はfalse"
}

##記載情報##
- content: 画像内の情報はcontentに記載してください。画像内の情報を漏れなく記載してください。
- keywords: 画像内の情報で重要なキーワードをkeywordsに記載してください。カンマ区切りで複数記載可能です。
- is_contain_image: 図や表などの画像で保存しておくべき情報が含まれている場合はtrue、それ以外はfalseを記載してください。
"""
STR_AI_USERMESSAGE = """画像の内容を用いて回答しなさい。Json形式でのみ回答してください。"""
STR_SAMPLE_USERMESSAGE = """画像の内容を用いて回答しなさい。Json形式でのみ回答してください。"""
STR_SAMPLE_AIRESPONSE = """{
    "content":"画像をテキストに変換した文字列",
    "keywords": "word1, word2, word3"
}"""

BLOB_TRIGGER_PATH = "rag-docs"
BLOB_CONTAINER_NAME_IMAGE = "rag-images"
BLOB_CONNECTION = os.getenv("BLOB_CONNECTION")

@app.event_grid_trigger(arg_name="azeventgrid")
def EventGridTrigger(azeventgrid: func.EventGridEvent):
    try:
        event = json.dumps({
            'id': azeventgrid.id,
            'data': azeventgrid.get_json(),
            'topic': azeventgrid.topic,
            'subject': azeventgrid.subject,
            'event_type': azeventgrid.event_type,
        })
        event_dict = json.loads(event)
    except Exception as ex:
        logging.error(f"Failed to parse Event Grid payload: {ex}")
        logging.error(f"Raw event data: {azeventgrid.get_body().decode('utf-8', errors='replace')}" )
        raise
    blob_url = event_dict.get('data').get('url')

    logging.info(f"azeventgrid.get_json(): {azeventgrid.get_json()}")
    
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not azure_endpoint or not azure_api_key:
        logging.error("Missing Azure OpenAI credentials. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in environment or local.settings.json")
        return

    aoai_client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=azure_api_key,
        api_version="2024-12-01-preview"
    )
    azure_openai_service = AzureOpenAIService(client=aoai_client)
    cosmos_service = CosmosService()
    if not BLOB_CONNECTION:
        logging.error("Missing BLOB_CONNECTION environment variable. Set BLOB_CONNECTION in local.settings.json or environment.")
        return

    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION)

    try:
        if event_dict.get('event_type') == "Microsoft.Storage.BlobCreated":
            logging.info(f"Event Type: {event_dict.get('event_type')}, Blob URL: {blob_url}")

            blob_file_path = blob_url.split(f"/{BLOB_TRIGGER_PATH}/")[1]
            blob_client = blob_service_client.get_blob_client(container=BLOB_TRIGGER_PATH, blob=blob_file_path)
            blob_data = blob_client.download_blob()
            logging.info(f"Blob data downloadeded")

            file_name = blob_data.name
            file_extension = os.path.splitext(file_name)[1].lower()
            logging.info(f"Processing file: {file_name}, extension: {file_extension}")

            ragdocs = blob_data.content_as_bytes()
            data_as_file = BytesIO(ragdocs)

            query = f'SELECT * FROM c WHERE c.file_name = \"{file_name}\"'
            items = cosmos_service.get_data(query=query)

            for item in items:
                cosmos_service.delete_data(item['id'])
                logging.info(f"Deleted existing document with id: {item['id']}")

            if file_extension == ".pdf":
                logging.info(f"Processing PDF file: {file_name}")

                temp_path = ""
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                    temp.write(data_as_file.read())
                    temp_path = temp.name

                doc = pymupdf.open(temp_path)
                logging.info(f"PDF opened, number of pages: {doc.page_count}")

                for page in doc:
                    logging.info(f"Processing page number: {page.number}")
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    binary_data = BytesIO()
                    img.save(binary_data, format="PNG")
                    binary_data.seek(0)
                    base64_data = base64.b64encode(binary_data.getvalue()).decode()
                    
                    image_content = []
                    image_content.append({
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_data}"
                        }
                    })
                    messages = []
                    messages.append({"role": "system", "content": STR_AI_SYSTEMMESSAGE})
                    messages.append({"role": "user", "content": STR_SAMPLE_USERMESSAGE})
                    messages.append({"role": "user", "content": STR_SAMPLE_AIRESPONSE})
                    messages.append({"role": "user", "content": STR_AI_USERMESSAGE})
                    messages.append({"role": "user", "content": image_content})

                    response = azure_openai_service.getChatCompletionJsonStructureMode(
                        messages, 0, 0, DocumentStructure
                    )
                    if response is None:
                        logging.error("OpenAI returned no response (likely 404 Resource not found). Check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_DEPLOYMENT_NAME in settings.")
                        return
                    doc_structured = response.choices[0].message.parsed
                    logging.info(f"AI response for page {page.number}: {doc_structured}")

                    # Fetch embedding and normalize to JSON-serializable structure (list of floats)
                    raw_embedding = azure_openai_service.getEmbedding(doc_structured.content)
                    content_vector = None
                    if raw_embedding is not None:
                        try:
                            # SDKs often return an object with .data -> list of items with .embedding
                            if hasattr(raw_embedding, "data"):
                                vectors = []
                                for item in raw_embedding.data:
                                    if hasattr(item, "embedding"):
                                        vectors.append(list(item.embedding))
                                    elif isinstance(item, (list, tuple)):
                                        vectors.append(list(item))
                                # If single vector, use that vector directly; otherwise keep list of vectors
                                if len(vectors) == 1:
                                    content_vector = vectors[0]
                                elif len(vectors) > 1:
                                    content_vector = vectors
                                else:
                                    content_vector = None
                            elif isinstance(raw_embedding, (list, tuple)):
                                content_vector = list(raw_embedding)
                            else:
                                # Try to coerce to list (may raise)
                                content_vector = list(raw_embedding)
                        except Exception as ex:
                            logging.warning("Could not normalize embedding response: %s", ex)
                            content_vector = None

                    if doc_structured.is_contain_image:
                        parse_url = urlparse(blob_url)
                        path_parts = parse_url.path.split('/')
                        index = path_parts.index('rag-docs')
                        stored_image_path = file_name + \
                            "_page" + str(page.number) + ".png"
                        blob_client = blob_service_client.get_blob_client(
                            container=BLOB_CONTAINER_NAME_IMAGE,
                            blob=stored_image_path
                        )
                        # base64_data is a str (base64-encoded). Decode to bytes before uploading.
                        blob_client.upload_blob(base64.b64decode(base64_data), overwrite=True)
                        logging.info(f"Uploaded image blob to: {stored_image_path}")

                        cosmos_page_obj = CosmosPageObj(
                            page_number=page.number,
                            content=doc_structured.content,
                            content_vector=content_vector,
                            keywords=doc_structured.keywords,
                            file_name=file_name,
                            file_path=blob_url,
                            detele_flag=False,
                            is_contain_image=doc_structured.is_contain_image,
                            image_blob_path=stored_image_path if doc_structured.is_contain_image else None
                        )
                        cosmos_service.insert_data(cosmos_page_obj.to_dict())
            else:
                logging.info(f"Unsupported file type: {file_extension} for file: {file_name}")
            
        elif event_dict.get('event_type') == "Microsoft.Storage.BlobDeleted":
            logging.info(f"Event Type: {event_dict.get('event_type')}, Blob URL: {blob_url}")

            query = f'SELECT * FROM c WHERE c.file_path = \"{blob_url}\"'
            items = cosmos_service.get_data(query=query)

            for item in items:
                cosmos_service.delete_data(item['id'])
                logging.info(f"Deleted document with id: {item['id']} due to blob deletion")

                if item["is_contain_image"]:
                    blob_client = blob_service_client.get_blob_client(
                        container=BLOB_CONTAINER_NAME_IMAGE,
                        blob=item["image_blob_path"]
                    )
                    blob_client.delete_blob()
                    logging.info(f"Deleted associated image blob: {item['image_blob_path']}")
        
        else:
            logging.info(f"Ignored event type: {event_dict.get('event_type')}")

    except Exception as e:
        logging.error(f"Error processing Event Grid event: {e}")
        raise e