from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os
import hmac
import json
import hashlib
import base64


with open('env.json', 'r') as f:
    env_file = f.read()
    config = json.loads(env_file)

app = Flask(__name__)


access_token = config.get('ACCESS_TOKEN')
channel_secret = config.get('CHANNEL_SECRET')
push_url = 'https://api.line.me/v2/bot/message/push'

if access_token is None or channel_secret is None:
    raise ValueError('Please configure both access token and channel secret in env.json file.')


@app.route('/', methods=['GET', 'POST'])
def receive():
    if request.method == 'POST':
        body = request.data
        hash = hmac.new(channel_secret.encode('utf-8'),
                        body, hashlib.sha256).digest()
        gen_signature = base64.b64encode(hash).decode()
        req_signature = request.headers.get('X-Line-Signature')
        if gen_signature != req_signature:
            return jsonify({'success': False, 'error': 'Invalid signature'})
        event = request.json.get('events')[0] # returns list so we access first element
        source = event.get('source')
        if source is None:
            abort(400)
        user_id = source.get('userId')

        try:
            response = requests.post(push_url, json={
                'to': user_id,
                'messages': [{'type': 'text', 'text': user_id}]
            }, headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })
            response.raise_for_status()
        except Exception as e:
            return jsonify({'success': False, 'error': e})
        else:
            return jsonify(dict(success=successful))


@app.route('/push', methods=['POST'])
def push():
    data = request.json
    msg = data.get('message')
    recipient = data.get('to')
    if data is None or recipient is None:
        return jsonify({'error': '"message" or "to" is not in request json', 'success': False})
    try:
        requests.post(push_url, json={
            'to': recipient,
            'messages': [{'type': 'text', 'text': msg}]
        }, headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })
    except Exception as e:
        return jsonify({'error': e, 'success': False})
    else:
        return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
