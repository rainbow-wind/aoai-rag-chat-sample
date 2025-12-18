import json
import logging

from service.openai_service.openai_service import AzureOpenAIService

STR_AI_SYSTEMMESSAGE = """
##制約条件
- 与えられた文章だけを用いて回答しなさい。
- 回答はMarkdown形式のみで回答しなさい。
- 回答形式以外の内容は記載しないでください。
- 回答の最初に「```json」を含めないこと。

##回答形式##
{
    "keywords": "カンマ区切りのキーワード群"
}

##記載情報##
画像内の情報で重要なキーワードをkeywordsに記載してください。カンマ区切りで複数記載可能です。
"""

def get_keywords(aoai_service: AzureOpenAIService, file_content: str) -> str:
    messages = []
    messages.append({"role": "system", "content": STR_AI_SYSTEMMESSAGE})
    messages.append({"role": "user", "content": file_content})

    response_format = {"type": "json_object"}

    response = aoai_service.getChatCompletion(messages, 0, 0, response_format)
    response_message = response.choices[0].message['content']
    logging.info(f"get_keywords response_message: {response_message}")

    output = json.loads(response_message)
    return output['keywords']