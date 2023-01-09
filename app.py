import datetime
import json

from flask import Flask, request, Response

import mysql.connector
import hashlib

import carrier_sdk

app = Flask(__name__)


"""Schema:
mysql> CREATE TABLE users (
    -> user_id int,
    -> password varchar(255))
    -> ;

mysql> CREATE TABLE labels (
    -> label_id int,
    -> user_id int,
    -> rate int,
    -> created_at datetime,
    -> image_url varchar(255));
"""


@app.route('/get_rates')
def get_rates():
    return carrier_sdk.get_rates()


@app.route('/buy_label', methods=['PUT'])
def buy_label():
    data = request.get_json()
    username = data['user_id']
    password = data['password']
    encrypted_pass = hashlib.sha1(password.encode(encoding = 'UTF-8', errors = 'strict'))
    cnx = mysql.connector.connect(user='root', password='', host='localhost', database='stuff')
    query = ("SELECT * FROM users WHERE user_id = " + str(username) + " AND password = '" + encrypted_pass.hexdigest() + "'")
    with cnx.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            return Response("Unable to purchase label", status=200, mimetype='application/json')

    label = carrier_sdk.buy_label(data['service_level'])
    with cnx.cursor() as cursor:
        query = "INSERT INTO LABELS(user_id, rate, created_at, image_url) VALUES('" + str(username) + "', '" + str(label['rate']) + "', '" + str(datetime.datetime.utcnow()) + "', '" + str(label['image_url']) + "')"
        cursor.execute(query)
    cnx.commit()

    return label


@app.route('/get_purchased_labels')
def get_purchased_labels():
    data = request.get_json()
    username = data['user_id']
    password = data['password']
    print("Logging in user: " + str(username))
    encrypted_pass = hashlib.sha1(password.encode(encoding = 'UTF-8', errors = 'strict'))
    cnx = mysql.connector.connect(user='root', password='', host='localhost', database='stuff')
    query = ("SELECT * FROM users WHERE user_id = " + str(username) + " AND password = '" + encrypted_pass.hexdigest() + "'")
    with cnx.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            return Response("Unable to view labels", status=200, mimetype='application/json')

    with cnx.cursor() as cursor:
        label_query = ("SELECT * FROM labels WHERE user_id = " + str(username))
        cursor.execute(label_query)
        result = cursor.fetchall()
        labels = []
        for row in result:
            label = {
                'label_id': row['label_id'],
                'image_url': row['image_url'],
                'created_at': row['created_at']
            }
            labels.append(label)
        return Response(json.dumps(labels), status=200, mimetype='application/json')


@app.route('/register', methods=['PUT'])
def register():
    data = request.get_json()
    username = data['user_id']
    password = data['password']
    print("Registering user: " + str(username))
    encrypted_pass = hashlib.sha1(password.encode(encoding='UTF-8', errors='strict'))
    cnx = mysql.connector.connect(user='root', password='', host='localhost', database='stuff')
    query = ("INSERT INTO users(user_id, password) values (" + str(username) + ", '" + encrypted_pass.hexdigest() + "')")
    with cnx.cursor() as cursor:
        cursor.execute(query)
    cnx.commit()


if __name__ == '__main__':
    app.run()
