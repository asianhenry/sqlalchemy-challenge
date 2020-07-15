import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt

from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station=Base.classes.station

# Flask Setup
app = Flask(__name__)
#disable automatick key sort 
app.config['JSON_SORT_KEYS'] = False


# Flask Routes

@app.route("/")
def welcome():
    """List all available api routes."""
    
    return (
        f"Welcome to the Hawaii Climate API<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start> and /api/v1.0/<start>/<end>"
    )

# Convert the query results to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all passengers
    sel = [Measurement.date, Measurement.prcp]
    precip_data = session.query(*sel).order_by(Measurement.date).all()

    session.close()
    new_dict={}
    data_list=[]
    new_dict['precipitation data']=data_list
   
    precip_dict = {}
    for date, precip in precip_data:
        
        precip_dict[date] = precip
       
    data_list.append(precip_dict)
    return jsonify(new_dict)

# Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def stations():
    """Returns list of station data"""
    
    session = Session(engine)

    # Query
    sel=[Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation]
    station_data = session.query(*sel).all()

    session.close()
    
    #convert to dict
    #station_data = []
    new_dict={}
    station_list=[]
    station_dict={}
    
    for id, name, lat, long ,elevation in station_data:
        
        station_dict['id'] = id
        station_dict['name'] = name
        station_dict['lat'] = lat 
        station_dict['long'] = long
        station_dict['elevation'] = elevation     
        station_list.append(station_dict)
        station_dict={}

    new_dict['stations']=station_list
    return jsonify(new_dict)


@app.route("/api/v1.0/tobs")
def tobs():
    """Returns id of most active station in last year of data.
       Returns list of date and tobs of the last year of data for the station"""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    #last date and year ago
    last_date=session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_datetime=dt.datetime.strptime(last_date[0],'%Y-%m-%d')
    year_ago = (last_datetime - dt.timedelta(days=365)).strftime('%Y-%m-%d')

    #get the most active station in the last year of data
    active_stations= session.query(Measurement.station).filter(Measurement.date >= year_ago).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.id).desc()).all()

    #query date and prcp of the last year of the most active station in the last year
    sel = [Measurement.date, Measurement.prcp]
    station_precip_data = session.query(*sel).filter(Measurement.station==active_stations[0][0]).\
        filter(Measurement.date >= year_ago).order_by(Measurement.date).all()
        

    session.close()
    
    new_dict={}
    new_list=[]
    new_dict['station']=new_list
    station_precip_dict={}
    data_dict={}

    
    station_precip_dict['id']=active_stations[0][0]
    station_precip_dict['data']=data_dict
    for date, precip in station_precip_data:
        data_dict[date] = precip        
        #station_data.append(station_dict)
    station_precip_dict['data']=data_dict
    new_list.append(station_precip_dict)

    return jsonify(station_precip_dict)


@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """When given only the start date, returns data_points, TMIN, TAVG, and TMAX 
       for all dates greater than or equal to the start date"""
    
    # Query
    sel=[func.count(Measurement.tobs),func.min(Measurement.tobs), func.max(Measurement.tobs),func.avg(Measurement.tobs)]
    temp_start = session.query(*sel).filter(Measurement.date >= start).all()

    session.close()
    
    #convert to dict
    temp_dict= {}
    for points, min, max, avg in temp_start:
        temp_dict['data_points']=points
        temp_dict["TMIN"] = min
        temp_dict["TMAX"] = max
        temp_dict["TAVG"] = avg

    #return an error message if the date exceeds the latest date in the data
    if temp_dict["data_points"] ==0 or start < '2010-01-01':
        return jsonify({"error": "Invalid date. Please select a dates between 2010-01-01 and 2017-08-23. Make sure date entered matches format yyyy-mm-dd"}),404
    else:
        return jsonify(temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def end(start,end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """When given start and end date, returns data_points, TMIN, TAVG, and TMAX 
       for all dates in the start-end range"""
    
    # Query
    sel=[func.count(Measurement.tobs),func.min(Measurement.tobs), func.max(Measurement.tobs),func.avg(Measurement.tobs)]
    temp_end = session.query(*sel).filter(Measurement.date >= start,Measurement.date <= end).all()

    session.close()
    
    #convert to dict
    temp_dict= {}
    for points, min, max, avg in temp_end:
        temp_dict['data_points']=points
        temp_dict["TMIN"] = min
        temp_dict["TMAX"] = max
        temp_dict["TAVG"] = avg

    #return an error message if the date exceeds the latest date in the data
    if temp_dict["data_points"] ==0 or start < '2010-01-01' or end > '2017-08-23':
        return jsonify({"error": "Invalid date. Please select a dates between 2010-01-01 and 2017-08-23. Make sure date entered matches format yyyy-mm-dd"}),404
    else:
        return jsonify(temp_dict)
        
if __name__ == '__main__':
    app.run(debug=True)

# Hints
# You will need to join the station and measurement tables for some of the queries.

# Use Flask jsonify to convert your API data into a valid JSON response object.