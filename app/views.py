from bson import json_util
from flask import Flask, jsonify, Markup, render_template, request
from app import app
import json
import pandas as pd

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
    #return json.dumps(data, default=json_util.default)
    return df.to_json(orient='records')

@app.route('/teaminfo')
def teaminfo():
    df = stats.teams_list()
    return df.to_json(orient='records')

@app.route('/game', methods=['GET'])
def game():
    
    gameid = request.args.get('gameid')
    return render_template("charttest.html",
                            gameid=gameid)

@app.route('/gamesentiment', methods=['GET'])
def gamesentiment():
    gameid = request.args.get('gameid')

    sent = stats.gametime_info(gameid)

    return Markup(json.dumps(sent, default=json_util.default))