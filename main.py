from flask import Flask, redirect, render_template, request
from flask_socketio import SocketIO, emit
import random
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, async_mode='threading')

n = 0
d = 0

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        gcd, x, y = extended_gcd(b % a, a)
        return gcd, y - (b // a) * x, x

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True

def generate_keypair():
    global n 
    p = random.randint(1000, 9999)
    q = random.randint(1000, 9999)

    while not (is_prime(p) and is_prime(q)):
        p = random.randint(1000, 9999)
        q = random.randint(1000, 9999)

    n = p * q
    phi = (p - 1) * (q - 1)

    e = random.randint(2, phi - 1)
    while gcd(e, phi) != 1:
        e = random.randint(2, phi - 1)

    _, d, _ = extended_gcd(e, phi)
    d = d % phi
    if d < 0:
        d += phi

    return (e, n), (d, n)

def encrypt(public_key, message):
    e, n = public_key
    encrypted_message = []
    for char in message:
        encrypted_char = pow(ord(char), e, n)
        encrypted_message.append(str(encrypted_char).zfill(4))
    return " ".join(encrypted_message)

def decrypt(private_key, ciphertext):
    d, n = private_key
    decrypted_message = ""
    ciphertext = ciphertext.split()
    for num in ciphertext:
        decrypted_char = pow(int(num), d, n)
        decrypted_message += chr(decrypted_char)
    return decrypted_message

API_URL = 'https://db.andypoquis.site/api/collections/menssage/records'

@app.route('/')
def index():
    response = requests.get(API_URL)
    if response.status_code == 200 or response.status_code == 201:
        messages = response.json()
        messages = messages['items']
    else:
        messages = []
    return render_template('index.html', messages=messages)



@socketio.on('message')
def handle_message(data):
    global n
    global d
    message = data['message']
    user = data['user']
    n_key = data['n_key']
    d_key = data['d_key']    
    # Generar llaves
    public_key, private_key = generate_keypair()
    n = public_key[1]
    d = private_key[0]
    
    print("n: ", str(n))
    print("d: ", str(d))

    # Cifrar mensaje
    ciphertext = encrypt(public_key, message)
    
    payload = {
        "menssage_crypt": ciphertext,
        "user": user
    }
    response = requests.post(API_URL, json=payload)
    if response.status_code == 200:
        emit('message', {'message': ciphertext, 'user': user, 'n_key': str(n),'d_key': str(d)}, broadcast=True)

socketio.on('keys')
def n_keyd_key():
    global n
    global d
    emit('keys', {'n': n, 'd': d}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app)
