import flask
import urlparse,os

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

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

@app.before_request
def set_db_connection():
	flask.g.db = connect_to_db()

@app.teardown_request
def 