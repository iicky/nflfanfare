from flask import Flask, jsonify, render_template, Markup
from app import app
import json
import pandas as pd
import sqlalchemy as sql

from nflfanfare import stats

@app.route('/')
def home():
    return render_template("tweetcount.html")

@app.route('/scroll')
def scroll():
    return render_template("scrolltest.html")

@app.route('/tweetcount')
def tweetcount():
    df = stats.game_tweet_counts()
    return df.to_json(orient='records')

@app.route('/teaminfo')
def teaminfo():
    df = stats.teams_list()
    return df.to_json(orient='records')