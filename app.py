# Dependencies
import os
import csv
import psycopg2
import pandas as pd
import numpy as np
#from config import username, password
from flask import Flask, render_template, jsonify, request, redirect
from flask import json
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

import sqlite3

app = Flask(__name__)

# Create an instance of Flask
app = Flask(__name__)


# DATABASE SETUP
# Configure our Flask instance to sqllite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Resources/gdp_olympic.sqlite'

# Create database object using SQLAlchemy
db = SQLAlchemy(app)

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(db.engine, reflect=True)


# ROUTE SETUP
# Route to render index.html template
@app.route("/")
def home():
    #engine = create_engine(f'postgresql://{username}:{password}@localhost/olympic_data')
    #conn = engine.connect()
    #conn = psycopg2.connect(database="olympic_data", user='postgres', password='FlynnsArcade#19707', host='127.0.0.1', port= '5432')
    #cursor = conn.cursor()
    conn = sqlite3.connect("./Resources/gdp_olympic.sqlite")
    cursor = conn.cursor()

    return render_template("index.html")


#Route for Maggie - Female bar graph and scatter plaots
#@app.route("/maggie.html")
#def maggie():
 

#@app.route("/maggieData")
#def maggieData():
#   return render_template("maggie.html")

# Route for Maggie Male bar graph and scatter plots
#@app.route("/maggiemale.html")
#def maggiemale():
   #return render_template("maggiemale.html")


#@app.route("/maggieData")
#def maggieData2():
#    return render_template("maggiemale.html")

# Route for gdp
@app.route('/observations')
def method():
    return render_template("observations.html")
    

#Route for female page 
#@app.route('/female')
#def female():
#   return render_template('maggie.html')
   
#@app.route('/female')
#def female():
#    return render_template('maggie.html')
   
#@app.route('/female')
#def athletes_data_json():
   # filename = os.path.join(app.static_folder, 'athletes_data.json')
   # with open(filename) as test_file:
       # data = json.load(test_file)
   # return render_template('maggie.html', data = data)



# Route for male page of project
#@app.route('/male')
#def male():
#    return render_template("maggiemale.html")

# Route to get data for choropleth map and scatter plot
@app.route("/gdp_medals")
def gdp_medals():
    
    #Connect to PostgreSQL database
    conn = sqlite3.connect("./Resources/gdp_olympic.sqlite")
    #engine = create_engine(f'postgresql://{username}:{password}@localhost/olympic_data')
    #conn = engine.connect()
    #conn = psycopg2.connect(database="olympic_data", user='postgres', password='password', host='127.0.0.1', port= '5432')
    cursor = conn.cursor()
    # Selected needed values from winter table
    winter_df = pd.read_sql('SELECT year, country_code, medal FROM winter', conn)

    # Selected needed values from wdi table
    wdi_df = pd.read_sql('SELECT country_name, country_code, year, gdp_per_cap FROM wdi', conn)

    # Merge with 'games' with 'wdi_df'
    df = pd.merge(winter_df, wdi_df, left_on=['country_code', 'year'], right_on=['country_code', 'year'])

    # Extract count of medals per country per year
    df2 = df.groupby(['year', 'country_name', 'medal']).count() # Group data and count medals by type
    df2 = df2.reset_index()
    df2 = df2.iloc[:, 0:4] # Selected needed columns and drop excess
    df2 = df2.rename(columns={'country_code':'medal_count'})

    # Pivot data frame so that each medal type is a column
    medals_df = pd.pivot_table(df2, values='medal_count', index=['year', 'country_name'], columns='medal', fill_value=0)
    medals_df = medals_df.reset_index()
    
    # Extract each country's gdp per year
    df3 = df.groupby(['year', 'country_code']).max()
    df3 = df3.reset_index()
    df3 = df3.drop(columns=['medal'])

    # Combine all information: gdp and medal count
    final_df = pd.merge(medals_df, df3, left_on=['country_name', 'year'], right_on=['country_name', 'year'])

    # Reorder columns
    final_df = final_df[['year', 'country_name', 'country_code', 'gdp_per_cap', 'Gold', 'Silver', 'Bronze']]

    # Rename columns
    final_df = final_df.rename(columns={'country_name':'country',
                            'gdp_per_cap':'gdp',
                            'Gold':'gold',
                            'Silver':'silver',
                            'Bronze':'bronze'
                            })
    
    # Save data to dictionary
    gdp_medals = final_df.to_dict(orient='records')

    return jsonify(gdp_medals)


# Route to get data for line graph 
@app.route("/line_graph")
def line_graph():
    #conn = psycopg2.connect(database="olympic_data", user='postgres', password='', host='127.0.0.1', port= '5432')
    #cursor = conn.cursor()
    # Load in data frame
    df = pd.read_csv('./Resources/line_graph.csv', dtype=str)
  

    # Create dictionary with key == country_code and values == dictionaries of pop_percentage and medal_percentage
    data = {}

    for i in range(len(df)):
        # Define row variable to describe the row we are on in current iteration
        row = df.iloc[i, :]
        
        # Define an empty list variable so we can append such an empty list when adding a new country
        empty_list = []
        
        # Conditional to check if country_code not already in the dictionary (add it if it's not)
        if row.country_code not in data.keys():
            data.update({
                row.country_code: empty_list
            })
            
        # Get the list corresponding to the current row's country code
        country_list = data.get(row.country_code)
        
        # Create a new element of that list which is a dictionary. JSON does not recognize
        # numpy data types, so casting as python ints and floats using the item() method.
        country_list.append({
            'year': int(row.year),
            'pop_percentage': float(row.pop_percentage),
            'medal_percentage': float(row.medal_percentage)
        })
        
    return jsonify(data)

# End Flask
if __name__ == "__main__":
    app.run(debug=False)

