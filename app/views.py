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
    df = stats.schedule()
    #return json.dumps(data, default=json_util.default)
    return df.to_json(orient='records')


@app.route('/teaminfo')
def teaminfo():
    df = stats.teams_list()
    return df.to_json(orient='records')


@app.route('/game', methods=['GET'])
def game():
    gameid = request.args.get('gameid')
    return render_template('scoreboard.html',
                            gameid=gameid)


@app.route('/gamesentiment', methods=['GET'])
def gamesentiment():
    # Parse gameid from get request
    gameid = request.args.get('gameid')

    # Sentiment data frame from gameid
    sentiment = stats.Game(gameid)._sentiment()

    # Return sentiment markup
    return sentiment.to_json(orient='records')
