import sys, os
import time
import json
import random
from flask import Flask, request
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from g4f import ChatCompletion, Provider
from config import app as conf_app, request as conf_req

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
    streaming = request.json.get('stream', False)
    model = request.json.get('model', 'gpt-3.5-turbo')
    messages = request.json.get('messages')
    temperature = request.json.get('temperature', 0.5)
    provider = providers.get(request.json.get('provider'))
    os.environ['HTTPS_PROXY'] = os.environ['HTTP_PROXY'] = request.json.get('proxy', '')
    if not provider:
        provider = random.choice(list(providers.values()))
    if model not in provider.model:
        model = provider.model[0]
    
    try:
        response = ChatCompletion.create(provider=provider, model=model, stream=streaming, messages=messages, temperature=temperature, timeout=conf_req['timeout'])
    except Exception as e:
        return {'error': str(e)}
    
    if not streaming:
        # while 'curl_cffi.requests.errors.RequestsError' in response:
        #     response = ChatCompletion.create(model=model, stream=streaming,
        #                                      messages=messages)

        completion_timestamp = int(time.time())
        completion_id = ''.join(random.choices(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))

        return {
            'id': 'chatcmpl-%s' % completion_id,
            'object': 'chat.completion',
            'created': completion_timestamp,
            'model': model,
            'usage': {
                'prompt_tokens': None,
                'completion_tokens': None,
                'total_tokens': None
            },
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': response
                },
                'finish_reason': 'stop',
                'index': 0
            }]
        }

    def stream():
        for token in response:
            completion_timestamp = int(time.time())
            completion_id = ''.join(random.choices(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))

            completion_data = {
                'id': f'chatcmpl-{completion_id}',
                'object': 'chat.completion.chunk',
                'created': completion_timestamp,
                'model': 'gpt-3.5-turbo-0301',
                'choices': [
                    {
                        'delta': {
                            'content': token
                        },
                        'index': 0,
                        'finish_reason': None
                    }
                ]
            }

            yield 'data: %s\n\n' % json.dumps(completion_data, separators=(',' ':'))
            time.sleep(0.1)

    return app.response_class(stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    config = {
        'host': conf_app['host'],
        'port': conf_app['port'],
        'debug': conf_app['debug'],
    }

    app.run(**config)
