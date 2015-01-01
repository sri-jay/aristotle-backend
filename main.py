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

        user_id = cursor.fetchall()[0]

        # Now register the user
        register_query = """INSERT INTO users VALUES(\'%s\', \'%s\', \'%s\', \'%s\, \'%s\'')"""%(client_id, user_id, username, api_code, device_code)
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

@app.route("/get_request", methods=['POST'])
def hello_dammit():

	for req in request.form:
		print req," ",request.form[req]

	return "lol"

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


@app.route('/initialAssessment', methods=['POST'])
def initialAssessment():
	data = [get_data, get_question]
	ind = random.randint(0,20)%2

	return jsonify(data[ind]())

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

def get_data():
	data = {
		'TYPE' : 'KNOWLEDGE_TYPE_UNIT',
		'TITLE' : 'On the entropy of gases in motion.',
		'CONTENT' : 'The motion of gases in space are governed by the prescence of strog and weak pseudpo hydrogen bonding.commonly understood as a measure of disorder. According to the second law of thermodynamics the entropy of an isolated system never decreases; such a system will spontaneously evolve toward thermodynamic equilibrium, the configuration with maximum entropy. Systems that are not isolated may decrease in entropy, provided they increase the entropy of their environment by at least that same amount. Since entropy is a state function, the change in the entropy of a system is the same for any process that goes from a given initial state to a given final state, whether the process is reversible or irreversible. However, irreversible processes increase the combined entropy of the system and its environment.The motion of gases in space are governed by the prescence of strog and weak pseudpo hydrogen bonding.commonly understood as a measure of disorder. According to the second law of thermodynamics the entropy of an isolated system never decreases; such a system will spontaneously evolve toward thermodynamic equilibrium, the configuration with maximum entropy. Systems that are not isolated may decrease in entropy, provided they increase the entropy of their environment by at least that same amount. Since entropy is a state function, the change in the entropy of a system is the same for any process that goes from a given initial state to a given final state, whether the process is reversible or irreversible. However, irreversible processes increase the combined entropy of the system and its environment.',
		'ID' : hashlib.sha224(str(random.random())).hexdigest(),
		'PATH_PROGRESS' : str(random.randint(30,99))
	}

	return data

def get_question():
	data = {
		'TYPE' : 'KNOWLEDGE_TYPE_QUESTION',
		'STATEMENT' : "What are kepler's laws?",
		'OPTION_A' : "Laws that describe the motion of all planets.",
		'OPTION_B' : "Theories of mechanics.",
		'OPTION_C' : "Trajectory of elliptical motion of stellar objects.",
		'ID' : hashlib.sha224(str(random.random())).hexdigest(),
		'PATH_PROGRESS' : str(random.randint(30,99))
	}
	return data

if __name__ == "__main__":
	app.run(debug=True)
