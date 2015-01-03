from flask import Flask, render_template, request, jsonify, make_response

# DB imports
import psycopg2

# Required for generating secret keys
import random
import hashlib
import urlparse

# for urlparse
import os

# Setup url parse to read DB login data as environment string
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

app = Flask(__name__, static_url_path = "")

# simple map to store authenticated users sessionKeys.
auth_verified_users = {}


def connect_to_db():
    print "Creating connection object."
    db_connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return db_connection

@app.route("/registerDevice",methods=['POST'])
def register_device():
    device_code = request.form['DEVICE_ID']
    api_code = hashlib.sha224(str(random.random())).hexdigest()
    client_id = request.form['CLIENT_ID']
    username = request.form['F_NAME'] + request.form['L_NAME']
    phone_number = request.form['PHONE_NUMBER']


    response = None

    STATUS = "REGISTRATION_SUCCEEDED"
    try:
        # Get database connection
        connection = connect_to_db()

        # Create cursor
        cursor = connection.cursor()

        # Build query
        get_id_query = """SELECT userid FROM user_reg WHERE userphonenumber =\'%s\' AND clientid = \'%s\'"""%(phone_number, client_id)

        # Execute query, get the userid from the reg table
        cursor.execute(get_id_query)

        user_id = cursor.fetchall()
        user_id = user_id[0][0]

        # Now register the user
        register_query = """INSERT INTO users VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\')"""%(client_id, user_id, username, api_code, device_code)
        cursor.execute(register_query)

        # Commit query
        connection.commit()

        response = {'STATUS' : STATUS, 'API_SECRET' : api_code}

        # Close the connection and cursor
        cursor.close()
        connection.close()

    except Exception as e:
        print "DB connection failed!"
        print e

        STATUS = "REGISTRATION_FAILED"
        response = {'STATUS' : STATUS}

    return jsonify(response)

@app.route("/getSession", methods=['GET','POST'])
def get_session():

    # Get app secret from device
    app_secret = request.form['secret_key']

    print "\n"
    print app_secret
    print "\n"

    response = None

    try:
        # Get connection object
        connection = connect_to_db()

        # Ge ta cursor
        cursor = connection.cursor()

        query = """SELECT * FROM api_secret_keys WHERE secret_key = \'%s\' ;"""%(app_secret)

        print query

        cursor.execute(query)

        data = cursor.fetchall()


        cursor.close()
        connection.close()

        if len(data) == 1:

            STATUS = "SESSION_SUCCESS"
            SESSION_KEY = hashlib.md5(str(random.random())).hexdigest()
            response = {'STATUS' : STATUS, 'SESSION_KEY' : SESSION_KEY}

        else:
            STATUS = "SESSION_FAILED"
            response = {'STATUS' : STATUS}

    except Exception as e:

        print "DB Insert failed."
        STATUS = "FAILED_TO_AUTH"

        print e

        response = {'STATUS' : STATUS}

    return jsonify(response)

@app.route("/getNextItemInPath", methods=['POST'])
def get_next_item_in_path():
    device_id = request.form["DEVICE_ID"]

    data = {
        "TYPE" : "NONE"
    }


    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # query to get the user id
        query_get_uid = """SELECT userid FROM users WHERE device_key = \'%s\'"""%(device_id)

        # Execute query
        cursor.execute(query_get_uid)

        # get user_id
        user_id = cursor.fetchall()
        user_id = user_id[0][0]


        # now we get the next action to be taken
        query_get_next_action = """SELECT sequence FROM user_action WHERE userid=\'%s\' order by action_seq desc limit 1"""%(user_id)

        # execute query
        cursor.execute(query_get_next_action)

        # get the next action
        sequence = cursor.fetchall()

        if len(sequence) == 0:
            query_get_first_action = """SELECT sequence, questionid, unitid FROM learning_path WHERE previoussequence = \'NULL\' AND userid = \'%s\'"""%(user_id)

            # execute query to get next action
            cursor.execute(query_get_first_action)

            #get the next action
            sequence = cursor.fetchall()[0]

            # get the data
            sequence, question_id, unit_id = sequence

        else:
            query_get_sequence_action = """SELECT nextsequence FROM learning_path WHERE sequence = \'%s\' AND userid = \'%s\'"""%(sequence[0][0], user_id)

            # execute query to get next action
            cursor.execute(query_get_sequence_action)

            #get the next action
            nextsequence = cursor.fetchall()[0][0]

            query_get_next_action =  """SELECT sequence, questionid, unitid FROM learning_path WHERE sequence = \'%s\' AND userid = \'%s\'"""%(nextsequence, user_id)

            #execute fetch
            cursor.execute(query_get_next_action)

            # get the data
            sequence = cursor.fetchall()[0]

            sequence, question_id, unit_id = sequence

        print sequence, question_id, unit_id
        if question_id != 'NULL':
            query_get_question= """SELECT questionname, questiontext, option1Text, option2Text, option3Text, questionmultimedia FROM question WHERE questionid = \'%s\'"""%(question_id)

            cursor.execute(query_get_question)

            dat = cursor.fetchall()[0]
            name, statement, option_a, option_b, option_c, image_url = dat

            print dat

            data = {
                'TYPE' : 'KNOWLEDGE_TYPE_QUESTION',
                'STATEMENT' : statement,
                'SEQUENCE'  : sequence,
                'OPTION_A'  : option_a,
                'OPTION_B'  : option_b,
                'OPTION_C'  : option_c,
                'ID' : hashlib.sha224(str(random.random())).hexdigest(),
                'PATH_PROGRESS' : str(random.randint(30,99)),
                'IMAGE_URL' : image_url
            }

        if unit_id != 'NULL':
            query_get_unit = """SELECT unitname, unittext FROM unit WHERE unitid=\'%s\'"""%(unit_id)

            cursor.execute(query_get_unit)

            name, text = cursor.fetchall()[0]

            print name, text
            data = {
                'TYPE' : 'KNOWLEDGE_TYPE_UNIT',
                'SEQUENCE' : sequence,
                'TITLE' : name,
                'CONTENT' : text,
                'ID' : hashlib.sha224(str(random.random())).hexdigest(),
                'PATH_PROGRESS' : str(random.randint(30,99))
            }

        # now we update the user_action with current user's data
    except Exception as e:
        print e

    return jsonify(data)

@app.route("/recordResponse", methods=['POST'])
def record_response():
    response_for = request.form["RESPONSE_FOR"]
    device_id = request.form["DEVICE_ID"]
    course_id = request.form["COURSE_ID"]
    response = request.form["RESPONSE"]
    current_seq = request.form["SEQUENCE"]

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # query to get the user id
        query_get_uid = """SELECT userid, clientid FROM users WHERE device_key = \'%s\'"""%(device_id)
        # Execute query
        cursor.execute(query_get_uid)

        # get user_id
        user_id, client_id = cursor.fetchall()[0]

        if response_for == "KNOWLEDGE_TYPE_UNIT":
            query_update_user_action =\
                """INSERT INTO user_action VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\')"""\
                %(client_id, user_id, course_id, current_seq, response, "NULL")
        if response_for == "KNOWLEDGE_TYPE_QUESTION":
            query_update_user_action =\
                """INSERT INTO user_action VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\')"""\
                %(client_id, user_id, course_id, current_seq, "NULL", response)

        cursor.execute(query_update_user_action)
        connection.commit()

        cursor.close()
        connection.close()
    except Exception as e:
        print e

    return "lol"
@app.route('/getAllOrg')
def getAllOrganizations():
    query = "SELECT * FROM client"

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        cursor.execute(query)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

    except Exception as e:
        print e

    return jsonify(data)

if __name__ == "__main__":
	app.run(debug=True)
