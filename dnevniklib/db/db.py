import sqlite3

db_connection = sqlite3.connect("bot_data.db")
cursor = db_connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

def create():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Users(
        user_id INTEGER PRIMARY KEY,
        token VARCHAR,
        UNIQUE(user_id)
    )
    """
    cursor.execute(create_table_query)
    db_connection.commit()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS Tasks(
        title VARCHAR NOT NULL,
        description VARCHAR NOT NULL,
        deadline DATETIME NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_table_query)
    db_connection.commit()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS Activities(
        title VARCHAR NOT NULL,
        description VARCHAR NOT NULL,
        date_start_time DATETIME NOT NULL,
        date_end_time DATETIME NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_table_query)
    db_connection.commit()

def addUser(user_id):
    try:
        insert_query = "INSERT INTO Users (user_id, token) VALUES (?, ?)"
        data = (user_id, "")
        cursor.execute(insert_query, data)
        db_connection.commit()
    except sqlite3.IntegrityError as e:
        pass

def addToken(user_id, token):
    insert_query = "UPDATE Users SET user_id = ?, token = ? WHERE user_id = ?"
    data = (user_id, token, user_id)
    cursor.execute(insert_query, data)
    db_connection.commit()

def getToken(user_id):
    insert_query = "SELECT * FROM USERS WHERE user_id=?"
    cursor.execute(insert_query, (user_id,))
    result = cursor.fetchall()
    return result[0][1]

def addTask(data, user_id):
    insert_query = "INSERT INTO Tasks (title, description, deadline, user_id) VALUES (?, ?, ?, ?)"
    data = (data["title"], data["description"], data["deadline"], user_id)
    cursor.execute(insert_query, data)
    db_connection.commit()

def getTasks(user_id):
    insert_query = "SELECT * FROM Tasks WHERE user_id=?"
    cursor.execute(insert_query, (user_id,))
    result = cursor.fetchall()
    return result

def addActivity(data, user_id):
    insert_query = "INSERT INTO Activities (title, description, date_start_time, date_end_time, user_id) VALUES (?, ?, ?, ?, ?)"
    data = (data["title"], data["description"], data["date_start_time"], data["date_end_time"],  user_id)
    cursor.execute(insert_query, data)
    db_connection.commit()

def viewActivities(user_id, inp):
    insert_query = "SELECT * FROM Activities WHERE user_id=? AND date_start_time LIKE ? ORDER BY date_start_time"
    cursor.execute(insert_query, (user_id, inp+"%"))
    result = cursor.fetchall()
    return result

def clearData():
    clearTasks()
    insert_query = "DELETE FROM Activities WHERE DATE(date_end_time)<=DATE('now')"
    cursor.execute(insert_query)
    db_connection.commit()

def clearTasks():
    insert_query = "DELETE FROM Tasks WHERE DATE(deadline)<=DATE('now')"
    cursor.execute(insert_query)    
    db_connection.commit()

create()