# all the inports
from flask import Flask, flash, redirect, render_template, request, session,jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from flask_cors import CORS
import re
import base64
import sqlite3
import googlemaps 
from itertools import permutations 

#initializes api
API = 'AIzaSyBuyP447XzLPFFEpEb6PFvn9MbllrYWOqE'
Maps = googlemaps.Client(key = API)

#declaring variables  
carPerkm = 192
idleCarGrams = 1814.37/3600
busPerKm = 96
idleBusGramsPerSecond = (15/3600)/9.6
trainperKm = 15
typeTransit = "bus"

#imports the flask framework and enables CORS
app = Flask(__name__)
CORS(app)

#configure the flask appliations session settings
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#establishes connection to SQLite database 
con = sqlite3.connect("accounts.db")
cur = con.cursor()

#define route for home page
@app.route("/")
def index():
    return render_template("index.html")

#defines a route for user registration 
@app.route("/register", methods=["GET", "POST"])
def register():
    #establish a new database connection and cursor
    con = sqlite3.connect("accounts.db")
    cur = con.cursor()
    #handle registration from submission (post request)
    if request.method == "POST":
        #check if required form fields are provided 
        if not request.form.get("email"):
            return apology("must provide email", 400)
        if not request.form.get("username"):
            return apology("must provide username", 400)
        if not request.form.get("password"):
            return apology("must provide password", 400)
        if len(request.form.get("password")) < 8:
            return apology("password must be at least 8 characters", 400)
        #initialize counters for character types in the password
        letter_count = 0
        upper_count = 0
        number_count = 0
        spec_count = 0

        #interate through each characer in the password
        for char in request.form.get("password"):
            #check if the character is an alphabet letter
            if char.isalpha():
                letter_count += 1
                #if its an uppercase letter, increment the uppercase count
                if char.isupper():
                    upper_count += 1
            #check if character is a digit
            elif char.isdigit():
                number_count += 1
            #if its neither a letter nor a digit, consider it a special character
            else:
                spec_count += 1

        #check password requirements and returns and apology message if not met
        if letter_count < 4:
            return apology("there must be at least 4 letters", 400)
        if upper_count < 1:
            return apology("there must be at least one uppercase character", 400)
        if number_count < 1:
            return apology("there must be at least one number", 400)
        if spec_count < 1:
            return apology("there must be at least one special character", 400)
        #define a regular expression pattern to validate the email address
        pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        #check if the provided email matches the pattern 
        if not re.match(pattern, request.form.get("email")):
            return apology("this is not a valid email address.", 400)
        #establish a database connection and cursor 
        cur.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cur.fetchall()
        cur = con.cursor()
        #check if the username already exists in the databse 
        if len(rows) != 0:
            return apology("username already exists", 400)

        #check if the email address is already used in the database 
        rows = cur.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("email"),)
        )
        rows = cur.fetchall()
        cur = con.cursor()
        if len(rows) != 0:
            return apology("email address already used", 400)

        #check if the password and password confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        #inserts the users information into the databse 
        cur.execute(
            "INSERT INTO users (username, password, email, points, money) VALUES(?, ?, ?, ?, ?)",
            (request.form.get("username"),
            generate_password_hash(request.form.get("password")),
            request.form.get("email"),
            0,
            0.00,)
        )

        #commit the changes to the database 
        con.commit()

        # commit the changes to the database 
        flash("Registered!")

        # retrieve the users ID from the database 
        cur.execute(
            "SELECT id FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cur.fetchall()
        column_names = [description[0] for description in cur.description]
        rows = [dict(zip(column_names, row)) for row in rows]
        cur = con.cursor()

        #set the users ID in the session data 
        session["user_id"] = rows[0]["ID"]
        #close the database connection 
        con.close()
        #redirect to the homepage
        return redirect("/")
    else:
        con.close()
        return render_template("register.html")

# Define a route for user login, supporting both GET and POST requests
@app.route("/login", methods=["GET", "POST"])
def login():
    # Establish a new database connection and cursor
    con = sqlite3.connect("accounts.db")
    cur = con.cursor()
    # Clear the user's session data
    session.clear()
    # Handle POST request (form submission)
    if request.method == "POST":
        # Check if the username or email and password are provided
        if not request.form.get("username"):
            return apology("must provide username or email address", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)

         # Query the database to retrieve user information based on username or email
        cur.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cur.fetchall()
        # Extract column names for the result rows
        column_names = [description[0] for description in cur.description]
        # Convert result rows into dictionaries for easier access
        rows = [dict(zip(column_names, row)) for row in rows]
        # Reinitialize the cursor
        cur = con.cursor()

        # Check if the provided credentials are valid
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)
        # Set the user's ID in the session data
        session["user_id"] = rows[0]["ID"]
        # Display a flash message indicating successful login
        flash("Logged in!")
        # Close the database connection
        con.close()
        return redirect("/")
    else:
        con.close()
        # Render the login form template
        return render_template("login.html")

# Define a route for user logout, accessible only to logged-in users
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out!")
    return redirect("/")

# Define a route for a trip, accessible only to logged-in users
@app.route("/trip", methods=["GET", "POST"])
@login_required
def trip():
  con = sqlite3.connect("accounts.db")
  cur = con.cursor()
  def validate_address(address):
    geocode_result = Maps.geocode(address)
    if geocode_result:
        return True
    else:
        return False
    
  def carCarbonFootprint():
      kmDistance = (distance[0]['legs'][0]['distance']['value'])
      kmDistance = kmDistance/1000
      carbonFootprint = kmDistance * carPerkm
      
  
      # calculating traffic coefficient 
  
      actualDuration = (distance[0]['legs'][0]['duration']['value'])
  
      oDuration = actualDuration *0.8
  
      trafficCoefficient = actualDuration - oDuration
      return (carbonFootprint + trafficCoefficient*(idleCarGrams))
  
  def transitCarbonFootprint():
      if typeTransit == "bus":
          # calculating bus carbon footprint 
  
          kmDistance = (distance[0]['legs'][0]['distance']['value'])
          kmDistance = kmDistance/1000
          carbonFootprint = kmDistance * busPerKm  
  
          # calculating traffic coefficient for buses
  
          actualDuration = (distance[0]['legs'][0]['duration']['value'])
  
          oDuration = actualDuration * 0.8
  
          trafficCoefficient = actualDuration - oDuration
          return(carbonFootprint + trafficCoefficient*(idleBusGramsPerSecond))
      else: 
          kmDistance = (distance[0]['legs'][0]['distance']['value'])
          kmDistance = kmDistance/1000
          return(kmDistance * trainperKm)
  
  def greenPtsCalc():
      if modeOfTravel == 'c':
          # inefficent, carrying out the calculation twice. 
          basePts = int(carCarbonFootprint()) - int(transitCarbonFootprint())   
          return((basePts/ (1/(carCarbonFootprint()) + (1/transitCarbonFootprint())) ) * 1/carCarbonFootprint())
      else:
          basePts = int(carCarbonFootprint()) - int(transitCarbonFootprint())   
          return((basePts/ (1/(carCarbonFootprint()) + (1/transitCarbonFootprint())) ) * 1/transitCarbonFootprint())
  
  startDestination = None
  endDestination = None
  
  # validating the addresses entered 
  
  
  
  #selecting mode of travel 

  if request.method == "POST":

      while True:
          startDestination = request.form.get('start')
          if validate_address(startDestination):
              break
          else:
              return apology("Invalid start address", 400)
  
      while True:
          endDestination = request.form.get('end')
          if validate_address(endDestination):
              break
          else:
              return apology("Invalid destination.")
      modeOfTravel = request.form.get('mode')
      
      # validating mode of travel 
      
      if modeOfTravel !=  't' and modeOfTravel != 'c':
          return apology("Your mode of travel must be either transit or car", 400)      
      # calculating distance and time for car 
      
      if modeOfTravel == 'c':
          try: 
              distance  = Maps.directions(startDestination, endDestination, mode = 'driving', units = 'metric')
          
          except len(distance) == 0:
              return apology("Error extracting data from Maps. Please try with a more specific address", 400)      
          else:  
              kmDistance = (distance[0]['legs'][0]['distance']['text'])
      
              durationText = (distance[0]['legs'][0]['duration']['text'])

              display = ""
              display += "Distance = " + kmDistance + " Time = " + durationText + "<br>"
      
      
              # calls carbon footprint calculation function for cars 
      
              numpax = request.form.get('numpax')
                  
              carbonFootprint = carCarbonFootprint()
              saved = carbonFootprint - (carbonFootprint/int(numpax))
              
              # outputting carbon footprint

              print(carbonFootprint)
              display += "You will emit around " + str(int(carbonFootprint)) + " grams of CO2 in your journey" + "<br>"
      
              # calculating green points 
      
              greenPts = saved
              display += "By choosing rideshare, you will " + str(saved) + " fewer grams of CO2 that if you were to drive alone." + "<br>"
              cur.execute(
                  "SELECT points FROM users WHERE ID = ?", (session['user_id'],)
              )
              currentPts = cur.fetchall()
              column_names = [description[0] for description in cur.description]
              currentPts = [dict(zip(column_names, row)) for row in currentPts]
              cur = con.cursor()
              greenPts = int((0.1)*greenPts)
              currentPts[0]['points'] += greenPts
              flash(f"Green Points increased by {greenPts}")
              display += "Your new pts balance = " + str(currentPts[0]['points']) + "<br>" 
              cur.execute("UPDATE users SET points = ? WHERE ID = ?;", (currentPts[0]['points'], session['user_id'],))
              con.commit()
              con.close()
      else:
          con = sqlite3.connect("accounts.db")
          cur = con.cursor()
          #calculating bus distance
          typeTransit = request.form.get("transittype")
          while typeTransit != "train" and typeTransit != "bus":
              return apology("Please enter a valid transit type", 400)
      
          disabled = request.form.get('disabled')
          while disabled != 'y' and disabled != 'n':
              return apology("Please enter a valid response", 400)
          
          try:
              if disabled == 'y':
                  distance  = Maps.directions(startDestination, endDestination, mode = 'transit', transit_mode= typeTransit, transit_routing_preference = 'less_walking')
      
              else:
                  distance  = Maps.directions(startDestination, endDestination, mode = 'transit', transit_mode= typeTransit)
      
          except len(distance) == 0:
              return apology("Error extracting data from Maps, please try with a more specific address.", 400)          
          else:

              display = ''
              kmDistance = (distance[0]['legs'][0]['distance']['text'])
      
              durationText = (distance[0]['legs'][0]['duration']['text'])
      
              display += "Distance = " + kmDistance + " Time = " + durationText + '<br>'
      
              carbonFootprint = transitCarbonFootprint()
              # outputting carbon footprint
      
              display += "You will emit around " + str(int(carbonFootprint)) + "grams of CO2 in your journey" + '<br>'
      
              # calculating green points 
      
              greenPts = greenPtsCalc()
              greenPts = int(0.1*(greenPts))
              print("By choosing transit, you will prevent the emission of " + str(greenPts*10) + " grams of CO2")
              cur.execute(
                  "SELECT points FROM users WHERE ID = ?", (session['user_id'],)
              )
              currentPts = cur.fetchall()
              column_names = [description[0] for description in cur.description]
              currentPts = [dict(zip(column_names, row)) for row in currentPts]
              cur = con.cursor()
              currentPts[0]['points'] += greenPts
              flash(f"Green Points increased by {greenPts}")
              display += "Your new pts balance = " + str(currentPts[0]['points']) + '<br>'
              cur.execute("UPDATE users SET points = ? WHERE ID = ?;", (currentPts[0]['points'], session['user_id'],))
              con.commit()
              con.close()
      return render_template("result.html", display=display)
  else:
    return render_template("trip.html")

#define route for "/points" that requires login
@app.route("/points")
@login_required
def points():
  con = sqlite3.connect("accounts.db")
  cur = con.cursor()
  #Retrieve the points for the currently logged-in user
  cur.execute(
        "SELECT points FROM users WHERE ID = ?", (session['user_id'],)
  )
  currentPts = cur.fetchall()
  # Extract column names from the database cursor description
  column_names = [description[0] for description in cur.description]
  # Convert the database result into a dictionary
  currentPts = [dict(zip(column_names, row)) for row in currentPts]
  # Render the "points.html" template with the user's points
  return render_template("points.html", points=currentPts[0]['points'])

@app.route("/prep_trips", methods=["GET", "POST"])
@login_required
def prep():
    con = sqlite3.connect("accounts.db")
    cur = con.cursor()
    
    if request.method == "POST":
        cur.execute(
                "INSERT INTO trips (username, start, end, time) VALUES(?, ?, ?, ?)",
                (request.form.get('username'), request.form.get("start"), request.form.get("end"), request.form.get("time"),)
        )
        con.commit()
        con = sqlite3.connect("accounts.db")
        cur = con.cursor()
        # Retrieve the count of trips in the database
        cur.execute("SELECT COUNT(*) FROM trips")
        result = cur.fetchone()
        count = result[0]
        # Check if the count of trips is equal to 4
        if count == 4: 
            cur = con.cursor()
            # Retrieve the start and end points of all trips
            cur.execute(
                "SELECT start, end FROM trips")
            dests = cur.fetchall()
            # Extract column names from the database cursor description
            column_names = [description[0] for description in cur.description]
            dests = [dict(zip(column_names, row)) for row in dests]
            def process(places):
                a_start = places[0]
                a_end = places[1]
                b_start = places[2]
                b_end = places[3]
                c_start = places[4]
                c_end = places[5]
                d_start = places[6]
                d_end = places[7]
              
                
                API = 'AIzaSyBuyP447XzLPFFEpEb6PFvn9MbllrYWOqE'
                Maps = googlemaps.Client(key = API)
                
                
                def minway(waypoints):
            
                    big_array = []
                    carPerkm = 192
                    idleCarGrams = 1814.37/3600
                
                    API = 'AIzaSyBuyP447XzLPFFEpEb6PFvn9MbllrYWOqE'
                    Maps = googlemaps.Client(key = API)
                
                    def carCarbonFootprint():
                        carbonFootprint = mini * carPerkm
                
                        oDuration = actualDuration * 0.8
                
                        trafficCoefficient = actualDuration - oDuration
                        return (carbonFootprint + trafficCoefficient(idleCarGrams))
                    
                    comb = permutations(waypoints)
                
                    count = 0
                
                    for combos in list(comb):
                        big_array.append(combos)
                        count += 1
                
                    mini = 100000000000000
                
                    a_start = waypoints[0]
                    a_end = waypoints[1]
                    b_start = waypoints[2]
                    b_end = waypoints[3]
                
                    for i in range(count):
                        smallList = big_array[i]
                        if smallList.index(a_start) < smallList.index(a_end) and smallList.index(b_start) < smallList.index(b_end):
                            total = 0
                            actualDuration = 0 
                            for i in range(3):
                                distance = Maps.directions(smallList[i], smallList[i+1], mode = "driving")
                                kmDistance = ((distance[0]['legs'][0]['distance']['value']) / 1000)
                                total += int(kmDistance)
                                timeSmall = (distance[0]['legs'][0]['duration']['value'])
                                actualDuration = int(actualDuration + timeSmall)
                            if  int(total) < mini:
                                mini = total
                                index = smallList
                                displayTime = actualDuration
                    
                    return [mini, index]
                
            
                def validate_address(address):
                    geocode_result = Maps.geocode(address)
                    if geocode_result:
                        return True
                    else:
                        return False
                
                for i in [a_start, a_end, b_start, b_end, c_start, c_end, d_start, d_end]:
                    if not(validate_address(i)):
                        exit()
                    
                
                inputs = [a_start, a_end, b_start, b_end, c_start, c_end, d_start, d_end] 
                combs = []
                for i in range(0, len(inputs), 2):
                    for j in range(i+2, len(inputs), 2):
                        lst = []
                        lst = minway([inputs[i], inputs[i+1], inputs[j], inputs[j+1]])
                        lst.append(inputs[i]) 
                        lst.append(inputs[j])
                        combs.append(lst)
                
                minimum = 100000000000000000
                print(combs)    
                for i in combs:
                    if i[0] < minimum:
                        minimum = i[0]
                        best = i 
                
                print("the optimal route is: ")
                print_array = []
                print_array.append(best)
                  
                print(print_array)
                
                startCheck = print_array[0][2]
                otherStartCheck = print_array[0][3]
                namedList = [a_start, b_start,c_start,d_start]
                if startCheck in namedList:
                    namedList.remove(startCheck)
                if otherStartCheck in namedList:
                    namedList.remove(otherStartCheck)
                otherStart = namedList[0]
                otherOtherStart = namedList[1]
                otherEnd = inputs[inputs.index(otherStart) + 1]
                otherOtherEnd = inputs[inputs.index(otherOtherStart) + 1]
                otherBest = minway([otherStart,otherEnd,otherOtherStart, otherOtherEnd])
                print("the other path is ")
                print(otherBest)
                display = []
                display = [print_array, otherBest]
                return display

            formatted_pts = []
        
            for pt in dests:
                formatted_pts.append(pt['start'])
                formatted_pts.append(pt['end'])
            
            lst = process(formatted_pts)
            cur.execute(
              "DROP TABLE trips"
            )
            con.commit()
            con = sqlite3.connect("accounts.db")
            cur = con.cursor()
            cur.execute(
              "CREATE TABLE trips (username TEXT NOT NULL PRIMARY KEY, start TEXT NOT NULL, end TEXT NOT NULL, time TEXT NOT NULL)"
            )
            con.commit()
            return render_template("display.html", display=lst[0], display2 = lst[1])
        else:
            return render_template("result.html", display="OK")
    else:
        return render_template("prep_trips.html")


app.run(host='0.0.0.0', port=81)
