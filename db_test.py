from flask import Flask
import sqlite3

connection = sqlite3.connect('data.db')

user = (1, 'gorkem', 'acar')

users = [
    (2, 'rolf', 'qwert'),
    (3, 'jose', 'abcd')
]

cursor = connection.cursor()

# create_table = "CREATE TABLE users (id int, username text, password text)"

insert_query = "INSERT INTO users VALUES (?, ?, ?)"

cursor.execute(insert_query, user)

cursor.executemany(insert_query, users)

select_query = "SELECT * FROM users"

for row in cursor.execute(select_query):
    print(row)


connection.commit()

connection.close()