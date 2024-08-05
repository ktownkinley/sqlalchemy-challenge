# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import numpy as np
import datetime as dt
import os

# Use a raw string for the path or replace backslashes with forward slashes.
database_path = os.path.abspath(r"C:\\Users\\mckin\\Documents\\sqlalchemy-challenge\\Resources\\hawaii.sqlite")
print("Database path:", database_path)


#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine(f"sqlite:///{database_path}")
# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

@app.route("/")
def home():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt; (start=YYYY-MM-DD)<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;(start, end=YYYY-MM-DD)<br/>"
    )



#################################################
# Flask Routes
#################################################
@app.route("/api/v1.0/precipitation")
def precipitation():

    # calculate date one year ago from last date in db
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year_ago = last_date - dt.timedelta(days=365)

    # make query to retrieve the data and precipitation scores
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    precipitation = {date: prcp for date, prcp in results}

    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def stations():

    results = session.query(Station.station).all()

    stations = [station[0] for station in results]

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():

    most_active_station = session.query(Measurement.station, func.count(Measurement.station))\
                                 .group_by(Measurement.station)\
                                 .order_by(func.count(Measurement.station).desc()).first()[0]

    # get the last year of temperature observations
    last_date = session.query(func.max(Measurement.date)).\
        filter(Measurement.station == most_active_station).scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year_ago = last_date - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()

    tobs_data = {date: tobs for date, tobs in results}

    return jsonify(tobs_data)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def range_stats(start, end=None):

    # convert start and end to datetime objects
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")
        if end:
            end_date = dt.datetime.strptime(end, "%Y-%m-%d")
    # return 400 with error message if date is not in proper format
    except ValueError:
        session.close()
        return jsonify({"error": "Date format must be YYYY-MM-DD"}), 400

    if end:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start, Measurement.date <= end).all()
    else:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    # make dictionary to hold the results
    temps = list(np.ravel(results))
    return jsonify({"TMIN": temps[0], "TAVG": temps[1], "TMAX": temps[2]})

if __name__ == '__main__':
    app.run(debug=True)