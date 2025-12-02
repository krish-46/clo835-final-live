from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3

app = Flask(__name__)

# --- Database Configuration (From Env Vars) ---
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "password"
DATABASE = os.environ.get("DATABASE") or "employees"
DBPORT = int(os.environ.get("DBPORT") or 3306)

# --- New Configuration for Final Project ---
# 1. Get Student/Group Name
GROUP_NAME = os.environ.get("GROUP_NAME") or "Group 8"

# 2. S3 Configuration
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_IMAGE_KEY = os.environ.get("S3_IMAGE_KEY") # e.g., background.jpg
AWS_REGION = os.environ.get("AWS_REGION") or "us-east-1"

# --- Function to Download Image from S3 ---
def download_background_image():
    # Only try to download if the bucket env vars are set
    if S3_BUCKET and S3_IMAGE_KEY:
        print(f"Attempting to download background image from: s3://{S3_BUCKET}/{S3_IMAGE_KEY}")
        try:
            s3 = boto3.client('s3', region_name=AWS_REGION)
            # Flask serves static files from the 'static' folder
            if not os.path.exists('static'):
                os.makedirs('static')
            
            path = os.path.join('static', 'background.jpg')
            s3.download_file(S3_BUCKET, S3_IMAGE_KEY, path)
            print("Successfully downloaded background image to static/background.jpg")
        except Exception as e:
            print(f"Error downloading image from S3: {e}")
    else:
        print("S3_BUCKET or S3_IMAGE_KEY not set. Using default or missing background.")

# Download the image immediately when app starts
download_background_image()

# --- Database Connection ---
db_conn = None
try:
    db_conn = connections.Connection(
        host=DBHOST,
        port=DBPORT,
        user=DBUSER,
        password=DBPWD, 
        db=DATABASE
    )
    print("Connected to MySQL Database")
except Exception as e:
    print(f"Warning: Could not connect to Database: {e}")

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('addemp.html', name=GROUP_NAME)

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('about.html', name=GROUP_NAME)
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    emp_name = ""
    if db_conn:
        cursor = db_conn.cursor()
        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
        try:
            cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
            db_conn.commit()
            emp_name = "" + first_name + " " + last_name
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            cursor.close()

    print("all modification done...")
    return render_template('addempoutput.html', emp_name=emp_name, name=GROUP_NAME)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", name=GROUP_NAME)

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']
    output = {}
    
    if db_conn:
        select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
        cursor = db_conn.cursor()
        try:
            cursor.execute(select_sql,(emp_id))
            result = cursor.fetchone()
            if result:
                output["emp_id"] = result[0]
                output["first_name"] = result[1]
                output["last_name"] = result[2]
                output["primary_skills"] = result[3]
                output["location"] = result[4]
        except Exception as e:
            print(e)
        finally:
            cursor.close()

    return render_template("getempoutput.html", 
                           id=output.get("emp_id"), 
                           fname=output.get("first_name"),
                           lname=output.get("last_name"), 
                           interest=output.get("primary_skills"), 
                           location=output.get("location"), 
                           name=GROUP_NAME)

if __name__ == '__main__':
    # PDF Requirement: App must listen on Port 81
    app.run(host='0.0.0.0', port=81, debug=True)