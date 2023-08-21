import json
import random
import string
import time
from typing import Any

from flask import Flask, request
from flask_cors import CORS

import sys, os
from config import app as conf_app, request as conf_req
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from g4f import ChatCompletion, Provider

app = Flask(__name__)
CORS(app)

# working providers
providers = {
    'Acytoo': Provider.Acytoo,
    'DeepAi': Provider.DeepAi,
    'opchatgpts': Provider.opchatgpts,
    'ChatgptAi': Provider.ChatgptAi,
    'GetGpt': Provider.GetGpt,
    'EasyChat': Provider.EasyChat,
    'Ails': Provider.Ails,
    'Aichat': Provider.Aichat,
    'Yqcloud': Provider.Yqcloud,
}

@app.route("/chat/completions", methods=['POST'])
def chat_completions():
    stream = request.json.get('stream', False)
    model = request.json.get('model', 'gpt-3.5-turbo')
    messages = request.json.get('messages')
    temperature = request.json.get('temperature', 0.5)
    top_p = request.json.get('top_p', 0.5)
    provider = providers.get(request.json.get('provider'))
    timeout = request.json.get('timeout', conf_req['timeout'])
    os.environ['HTTPS_PROXY'] = os.environ['HTTP_PROXY'] = request.json.get('proxy', '')
    if not provider:
        provider = random.choice(list(providers.values()))
    if model not in provider.model:
        model = provider.model[0]
    
    try:
        response = ChatCompletion.create(provider=provider, model=model, stream=stream, messages=messages, temperature=temperature, timeout=timeout, top_p=top_p)
    except Exception as e:
        return {'error': str(e)}

    completion_id = "".join(random.choices(string.ascii_letters + string.digits, k=28))
    completion_timestamp = int(time.time())

    if not stream:
        return {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion",
            "created": completion_timestamp,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

    def streaming():
        for chunk in response:
            completion_data = {
                "id": f"chatcmpl-{completion_id}",
                "object": "chat.completion.chunk",
                "created": completion_timestamp,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": chunk,
                        },
                        "finish_reason": None,
                    }
                ],
            }

            content = json.dumps(completion_data, separators=(",", ":"))
            yield f"data: {content}\n\n"
            time.sleep(0.1)

        end_completion_data: dict[str, Any] = {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion.chunk",
            "created": completion_timestamp,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        content = json.dumps(end_completion_data, separators=(",", ":"))
        yield f"data: {content}\n\n"

    return app.response_class(streaming(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host=conf_app['host'], port=conf_app['port'], debug=conf_app['debug'])
