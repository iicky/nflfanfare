from bson import json_util
from flask import Flask, jsonify, Markup, render_template, request
from app import app
import json
import pandas as pd

from nflfanfare import stats


@app.route('/')
def home():
    return ''


@app.route('/schedule', methods=['GET'])
def schedule():
    week = request.args.get('week')
    return render_template("tweetcount.html", week=week)


@app.route('/scroll')
def scroll():
    return render_template("scrolltest.html")


@app.route('/tweetcount', methods=['GET'])
def tweetcount():
    week = request.args.get('week')
    if week == 'None':
        week = None
    df = stats.schedule(week)
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

@app.route('/gamedata', methods=['GET'])
def gamedata():
    # Parse gameid from get request
    gameid = request.args.get('gameid')

    # Sentiment data frame from gameid
    data = stats.Game(gameid).data()

    # Return sentiment markup
    return json.dumps(data, default=json_util.default)
