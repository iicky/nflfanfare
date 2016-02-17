
/**
 *  Returns a nicely formatted date
 */
function parseDate(stamp){
    return moment(stamp).format("ddd, DD MMM YYYY [@] hh:mm a");
};

/**
 *  Returns a nicely formatted play descripion
 */
function prettyPlay(play){
    //return play.split('. ')[0];
    if (play === 'undefined'){
        return ' ';
    }
    else {
        return play;
    }
};

/**
 *  Initializes the scoreboard from game JSON data
 */
function initScoreboard(d){

    //------------------------------------------
    // Scoreboard definitions
    var margin = {top: 5, right: 5, bottom: 5, left: 5}
        width = 700 - margin.left - margin.right,
        height = 200 - margin.top - margin.bottom;

    // Scoreboard
    var board = d3.select("#scoreboardcontainer")
        .append("svg")
        .attr("id", "scoreboard")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")");

    //------------------------------------------
    // Team possession defintions
    var possradx = 5, possrady = 10;
    var possy = 75/2;
    var homepossx = margin.left;
    var awaypossx = width - margin.left;

    // Home team possession
    var homeposs = board.append("g")
        .attr("id", "boardhomepossgroup")
        .attr("transform",
              "translate(" + homepossx + "," + possy + ")")
        .append("ellipse")
        .attr("id", "boardhomeposs")
        .attr("class", "boardpossessionoff")
        .attr("rx", possradx)
        .attr("ry", possrady)
        .attr("cx", 0).attr("cy", 0);

    // Away team possession
    var awayposs = board.append("g")
        .attr("id", "boardhomepossgroup")
        .attr("transform",
              "translate(" + awaypossx + "," + possy + ")")
        .append("ellipse")
        .attr("id", "boardawayposs")
        .attr("class", "boardpossessionoff")
        .attr("rx", possradx)
        .attr("ry", possrady)
        .attr("cx", 0).attr("cy", 0);

    //------------------------------------------
    // Team ID defintions
    var teamidheight = 30, teamidwidth = 75;
    var teamidy = 75/2 - teamidheight/2;
    var hometeamidx = homepossx + margin.left*2;
    var awayteamidx = awaypossx - teamidwidth - margin.left*2;

    // Home team ID
    var hometeamid = board.append("g")
        .attr("id", "boardhometeamidgroup")
        .attr("transform",
              "translate(" + hometeamidx + "," + teamidy + ")")

    hometeamid.append("rect")
              .attr("id", "boardhometeamid")
              .attr("class", "boardrect")
              .attr("height", teamidheight)
              .attr("width", teamidwidth)
              .attr("x", 0).attr("y", 0);

    hometeamid.append("text")
              .text(data.hometeam)
              .attr("class", "boardteamidtext")
              .attr("x", teamidwidth/2).attr("y", teamidheight/2);

    // Away team ID
    var awayteamid = board.append("g")
        .attr("id", "boardawayteamidgroup")
        .attr("transform",
              "translate(" + awayteamidx + "," + teamidy + ")")

    awayteamid.append("rect")
              .attr("id", "boardawayteamid")
              .attr("class", "boardrect")
              .attr("height", teamidheight)
              .attr("width", teamidwidth)
              .attr("x", 0).attr("y", 0);

    awayteamid.append("text")
              .text(data.awayteam)
              .attr("class", "boardteamidtext")
              .attr("x", teamidwidth/2).attr("y", teamidheight/2);

    //------------------------------------------
    // Team time out definitions
    var timeoutrad = 5;
    var circledata = [1, 2, 3];
    var hometimeoutx = hometeamidx + timeoutrad;
    var awaytimeoutx = awayteamidx + timeoutrad;
    var timeouty = teamidy + timeoutrad + teamidheight + margin.left*2;

    var hometimeout = board.append("g")
        .attr("id", "boardhometimeoutgroup")
        .attr("transform",
              "translate(" + hometimeoutx + "," + timeouty + ")")
        .selectAll("circle")
        .data(circledata).enter()
        .append("circle")
        .attr("id", function(d){ return "boardhometimeout" + d; })
        .attr("class", "boardtimeouton")
        .attr("r", timeoutrad)
        .attr("cx", function(d, i){ return ((teamidwidth/3)/2 + (teamidwidth/3)*i) - timeoutrad; })
        .attr("cy", 0);

    var awaytimeout = board.append("g")
        .attr("id", "boardawaytimeoutgroup")
        .attr("transform",
              "translate(" + awaytimeoutx + "," + timeouty + ")")
        .selectAll("circle")
        .data(circledata).enter()
        .append("circle")
        .attr("id", function(d){ return "boardawaytimeout" + d; })
        .attr("class", "boardtimeouton")
        .attr("r", timeoutrad)
        .attr("cx", function(d, i){ return ((teamidwidth/3)/2 + (teamidwidth/3)*i) - timeoutrad; })
        .attr("cy", 0);

    //------------------------------------------
    // Team logo definitions
    var logoheight = 75, logowidth = 75;
    var homelogox = hometeamidx + teamidwidth + margin.left*2;
    var awaylogox = awayteamidx - logowidth - margin.left*2;

    // Home logo
    var homelogo = board.append("g")
        .attr("id", "boardhomelogogroup")
        .attr("transform",
              "translate(" + homelogox + ", 0)")
        .append("image")
        .attr("id", "boardhomelogo")
        .attr("height", logoheight)
        .attr("width", logowidth)
        .attr("xlink:href", "/static/images/logos/" + d.hometeam + ".png")
        .attr("x", 0).attr("y", 0);

    // Away logo
    var awaylogo = board.append("g")
        .attr("id", "boardawaylogogroup")
        .attr("transform",
              "translate(" + awaylogox + ", 0)")
        .append("image")
        .attr("id", "boardawaylogo")
        .attr("height", logoheight)
        .attr("width", logowidth)
        .attr("xlink:href", "/static/images/logos/" + d.awayteam + ".png")
        .attr("x", 0).attr("y", 0);

    //------------------------------------------
    // Team score definitions
    var scoreheight = 75, scorewidth = 75;
    var homescorex = homelogox + logowidth + margin.left*2;
    var awayscorex = awaylogox - scorewidth - margin.left*2;
    var lastplay = d.plays[d.plays.length-1];

    // Home score
    var homescore = board.append("g")
        .attr("id", "boardhomescoregroup")
        .attr("transform",
              "translate(" + homescorex + ", 0)");

    homescore.append("rect")
             .attr("class", "boardrect")
             .attr("height", scoreheight)
             .attr("width", scoreheight)
             .attr("x", 0).attr("y", 0);

    homescore.append("text")
             .text(lastplay.homescore)
             .attr("id", "boardhomescore")
             .attr("class", "boardscoretext")
             .attr("x", scorewidth/2).attr("y", scoreheight/2);

    // Away score
    var awayscore = board.append("g")
        .attr("id", "boardawayscoregroup")
        .attr("transform",
              "translate(" + awayscorex + ", 0)");

    awayscore.append("rect")
             .attr("class", "boardrect")
             .attr("height", scoreheight)
             .attr("width", scoreheight)
             .attr("x", 0).attr("y", 0);

    awayscore.append("text")
             .text(lastplay.awayscore)
             .attr("id", "boardawayscore")
             .attr("class", "boardscoretext")
             .attr("x", scorewidth/2).attr("y", scoreheight/2);

    //------------------------------------------
    // Team score definitions
    var quarterheight = 30;
    var timeheight = 30;
    var quarterwidth = awayscorex - (homescorex + scorewidth) - margin.left*4;
    var quartery = margin.left;
    var timex = homescorex + scorewidth + margin.left*2;
    var timey = quarterheight + quartery + margin.left;

    // Quarter information
    var quarter = board.append("g")
        .attr("id", "boardquartergroup")
        .attr("transform",
              "translate(" + timex + ", 0)");

    quarter.append("rect")
           .attr("class", "boardrect")
           .attr("height", quarterheight)
           .attr("width", quarterwidth)
           .attr("x", 0).attr("y", quartery);

    quarter.append("text")
           .attr("id", "boardquarter")
           .text("FINAL")
           .attr("class", "boardquartertext")
           .attr("x", quarterwidth/2).attr("y", quartery + quarterheight/2);

    // Time information
    var time = board.append("g")
        .attr("id", "boardtimegroup")
        .attr("transform",
              "translate(" + timex + "," + timey + ")");

    time.append("rect")
        .attr("class", "boardrect")
        .attr("height", timeheight)
        .attr("width", quarterwidth)
        .attr("x", 0).attr("y", 0);

    time.append("text")
        .text(parseDate(d.endtime.$date))
        .attr("id", "boardtime")
        .attr("class", "boardtimetext")
        .attr("x", quarterwidth/2).attr("y", timeheight/2);

    //------------------------------------------
    // Play description definitions
    var playatrs = {
        height: 40,
        //width: width,
        width: awaylogox + logowidth - homelogox,
        x: homelogox,
        //x: 0,
        y: logoheight + margin.left*2
    };


    //var playheight = 20;
    //var playwidth = awaylogox + logowidth - homelogox;
    //var playx = homelogox;
    //var playy = logoheight + margin.left*2;

    // Time information
    var play = board.append("g")
        .attr("id", "boardplaygroup")
        .attr("transform",
              "translate(" + playatrs.x + "," + playatrs.y + ")");

    play.append("rect")
        .attr("id", "boardplayrect")
        .attr("class", "boardrect")
        .attr("height", playatrs.height)
        .attr("width", playatrs.width)
        .attr("x", 0).attr("y", 0);

    play.append("text")
        //.text(prettyPlay(lastplay.description))
        .attr("id", "boardplay")
        .attr("class", "boardplaytext")
        //.attr("x", playatrs.width/2).attr("y", playatrs.height/2);

    d3plus.textwrap()
          .container(d3.select("#boardplay"))
          .text(prettyPlay(lastplay.description))
          .draw();

};
