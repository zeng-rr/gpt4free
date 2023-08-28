import json
import random
import string
import time
from typing import Any

from flask import Flask, request
from flask_cors import CORS

import threading
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from config import app as conf_app, request as conf_req
from testing import test_providers
from g4f import ChatCompletion, Provider, BaseProvider, models

app = Flask(__name__)
CORS(app)

@app.route("/chat/completions", methods=['POST'])
def chat_completions():
    stream = request.json.get('stream', False)
    model = request.json.get('model', models.gpt_35_turbo.name)
    messages = request.json.get('messages')
    temperature = request.json.get('temperature', 0.5)
    top_p = request.json.get('top_p', 0.5)
    provider = request.json.get('provider')
    timeout = request.json.get('timeout', conf_req['timeout'])
    os.environ['HTTPS_PROXY'] = os.environ['HTTP_PROXY'] = request.json.get('proxy', '')
    
    try:
        provider = getattr(Provider, provider) if provider else random.choice([
            provider for provider in test_providers.get_providers() if provider.working
        ])
        provider.working = True
        response = ChatCompletion.create(provider=provider, model=model, stream=stream, messages=messages, temperature=temperature, timeout=timeout, top_p=top_p, system_prompt="")
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
                        "content": response.encode().decode(),
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
                            "content": chunk.encode().decode(),
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

@app.route("/providers/check", methods=['POST'])
def check_providers():
    proxies = request.json.get('proxies', [])
    times = request.json.get('times', 10)
    timeout = request.json.get('timeout', 10) * times
    providers = test_providers.get_providers()
    results: list[str] = []
    failResults: list[str] = []

    try:
        def check_provider(_provider: BaseProvider):
            if _provider.needs_auth:
                return
            print("start check ", _provider.__name__)
            for _ in range(times):
                os.environ['HTTPS_PROXY'] = os.environ['HTTP_PROXY'] = random.choice(proxies) if proxies else ""
                if test_providers.test(_provider):
                    results.append(_provider.__name__)
                    break
    
        for _provider in providers:
            _t = threading.Thread(target=check_provider, args=(_provider,), daemon=True)
            _t.start()
        threading.Event().wait(timeout)
    except Exception as e:
        return {'error': str(e)}

    failResults = [_provider.__name__ for _provider in providers if _provider.__name__ not in results]
    print("working provider list: " + str(results))
    print("not work provider list: " + str(failResults))
    return {"working_list": results, "not_work_list": failResults}

if __name__ == "__main__":
    app.run(host=conf_app['host'], port=conf_app['port'], debug=conf_app['debug'])
