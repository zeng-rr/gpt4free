
import io
import os
import random
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import g4f

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# os.environ['HTTPS_PROXY'] = os.environ['HTTP_PROXY'] = ''

# Set with provider
stream = False
total = i = 1
s = 0
t = time.time()
while i:
    try:
        i -= 1
        response = g4f.ChatCompletion.create(model='gpt-3.5-turbo', provider=g4f.Provider.Yqcloud, messages=[
                                     {"role": "user", "content": "hello"}], stream=stream, timeout=(3, 55))

        if stream:
            for message in response:
                print(message)
        else:
            print(response)
        s += 1 if response else 0
    except Exception as e:
        print(str(e))
    sys.stdout.flush()
print('total: ', total, ', success: ', s, ', time: ', int(time.time() - t))