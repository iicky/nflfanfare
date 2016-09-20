/**
 *  Draws the sentiment graph from the game JSON data
 */
function drawSentGraph(d){

    //var prestart = d3.min(data.gametime, function(d){ return d.time.$date; });
    //var postend = d3.max(data.gametime, function(d){ return d.time.$date; });

    //------------------------------------------
    // Sentiment graph definitions
    var margin = {top: 20, right: 75, bottom: 20, left: 75}
        width = 700 - margin.left - margin.right,
        height = 300 - margin.top - margin.bottom;

    var svg = d3.select("#sentgraphcontainer")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")");

    //------------------------------------------
    // Axis definitions
    var x = d3.time.scale().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);

    // Scale data
    x.domain(d3.extent(data.sentiment,
                       function(d) { return d.gametime.$date; }));
    y.domain([-1, 1]);

    var xAxis = d3.svg.axis().scale(x).ticks(0)
                  .orient("middle")
                  .outerTickSize(0);

    // Draw x-axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + 0 + "," + eval(height/2) + ")")
        .call(xAxis);

    var yAxis = d3.svg.axis().scale(y)
                  .orient("left")
                  .ticks(5)
                  .tickFormat(function(d){
                       if(d == 1) { return '\uf118' }
                       else if(d == 0) { return "\uf11a" }
                       else if(d == -1) { return "\uf119"}
                  });

    // Draw y-axis
    svg.append("g")
       .attr("class", "y axis")
       .attr("transform", "translate(0, 0)")
       .call(yAxis)

    svg.select(".y.axis")
       .selectAll("text")
       .attr("id", function(d){
                if(d == 1) { return 'yaxishappy' }
                else if(d == 0) { return "yaxismeh" }
                else if(d == -1) { return "yaxissad"}
            });

    //------------------------------------------
    // Team sentiment line definitions
    var homeline = d3.svg.line()
        .x(function(d) { return x(d.gametime.$date); })
        .y(function(d) { return y(d.homesentiment); });

    var awayline = d3.svg.line()
        .x(function(d) { return x(d.gametime.$date); })
        .y(function(d) { return y(d.awaysentiment); });

    // Home team lines
    svg.append("path")
       .attr("class", "boardteamlinepri")
       .attr("stroke", '#' + data.colors.home_pri)
       .attr("d", homeline(data.sentiment));

    svg.append("path")
       .attr("class", "boardteamlinesec")
       .attr("stroke", '#' + data.colors.home_sec)
       .attr("d", homeline(data.sentiment));

    // Away team line
    svg.append("path")
       .attr("class", "boardteamlinepri")
       .attr("stroke", '#' + data.colors.away_pri)
       .attr("d", awayline(data.sentiment));

    svg.append("path")
       .attr("class", "boardteamlinesec")
       .attr("stroke", '#' + data.colors.away_sec)
       .attr("d", awayline(data.sentiment));

    //------------------------------------------
    // Focus definitions

    var focus = svg.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("line")
         .attr("stroke", "gray")
         .attr("stroke-width", ".5px")
         .attr("opacity", .5)
         .attr("x1", 0)
         .attr("y1", 0)
         .attr("x2", 0)
         .attr("y2", height);

    var focuspad = 5;
    var focuslogoheight = 30;
    var focushomex = -1 * focuspad - focuslogoheight;
    var focusawayx = focuspad;

    // Home team focus definitions
    var focushome = focus.append("g")
        .append("g")
        .attr("transform",
              "translate(" + focushomex + ", 0)")

    focushome.append("image")
        .attr("id", "focushomelogo")
        .attr("height", focuslogoheight)
        .attr("width", focuslogoheight)
        .attr("xlink:href", "/static/images/logos/" + d.hometeam + ".png")

    focushome.append("text")
             .attr("id", "focushomesent")
             .attr("class", "focustext")
             .attr("x", -1 * focuspad)
             .attr("y", focuslogoheight/2)
             .style("text-anchor", "end")

    // Away team focus definitions
    var focusaway = focus.append("g")
        .append("g")
        .attr("transform",
              "translate(" + focusawayx + ", 0)")

    focusaway.append("image")
        .attr("id", "focusawaylogo")
        .attr("height", focuslogoheight)
        .attr("width", focuslogoheight)
        .attr("xlink:href", "/static/images/logos/" + d.awayteam + ".png")

    focusaway.append("text")
             .attr("id", "focusawaysent")
             .attr("class", "focustext")
             .attr("x", focuslogoheight + focuspad)
             .attr("y", focuslogoheight/2)
             .style("text-anchor", "start")

    // Focus overlay
    svg.append("rect")
       .attr("class", "overlay")
       .attr("width", width)
       .attr("height", height)
       .on("mouseover", function() { focus.style("display", null); })
       .on("mouseout", function() { focus.style("display", "none"); })
       .on("mousemove", mousemove);

    var boardtime = d3.select("#boardtime");
    var boardhomescore = d3.select("#boardhomescore");
    var boardawayscore = d3.select("#boardawayscore");
    var boardplay = d3.select("#boardplay");

    var playindex = d3.bisector(function(d){ return d.collected_time.$date }).right;
    var sentindex = d3.bisector(function(d){ return d.gametime.$date }).right;

    // Mouse move function
    function mousemove() {
        var x0 = d3.mouse(this)[0];
        var xtime = x.invert(x0);

        var playi = playitem(xtime);
        var senti = sentindex(data.sentiment, Date.parse(xtime));

        // Move focus line
        focus.attr("transform",
                   "translate(" + x0 + ",0)");

        // Board updates
        boardtime.text(parseDate(xtime));
        boardhomescore.text(data.plays[playi].homescore);
        boardawayscore.text(data.plays[playi].awayscore);

        d3plus.textwrap()
              .container(d3.select("#boardplay"))
              .text(prettyPlay(data.plays[playi].desc))
              .draw();

        possession(playi);
        timeouts(playi);
        quarter(playi);
        sentiment(senti);
    };

};

/**
 *  Fixes playtime index for postgame
 */
function playitem(xtime) {

    var len = data.plays.length;
    var playindex = d3.bisector(function(d){
        return d.collected_time.$date }).right;

    if (Date.parse(xtime) < data.scheduled.$date) {
        return 0;
    }
    else if (Date.parse(xtime) > data.plays[len-1].collected_time.$date) {
        return len-1;
    }
    else if (playindex(data.plays, Date.parse(xtime)) === 'undefined') {
        return len-1;
    }
    else {
        return playindex(data.plays, Date.parse(xtime));
    }
};

/**
 *  Changes team possession
 */
function possession(p) {
    var boardhomeposs = d3.select("#boardhomeposs");
    var boardawayposs = d3.select("#boardawayposs");

    if (data.plays[p].posteam == data.hometeam){
        boardhomeposs.attr("class", "boardpossessionon");
        boardawayposs.attr("class", "boardpossessionoff");
    }
    else if (data.plays[p].posteam == data.awayteam){
        boardawayposs.attr("class", "boardpossessionon");
        boardhomeposs.attr("class", "boardpossessionoff");
    }
    else {
        boardawayposs.attr("class", "boardpossessionoff");
        boardhomeposs.attr("class", "boardpossessionoff");
    }
};

/**
 *  Changes board quarter
 */
function quarter(p) {
    var boardquarter = d3.select("#boardquarter");
    var qtr = data.plays[p].qtr;

    if(typeof qtr === 'number'){
        var q = "Q" + qtr.toString();
        var t = data.plays[p].time;
        boardquarter.text(q + " " + t);
    }
    else {
        boardquarter.text(qtr);
    }
}

/**
 *  Changes team timeouts
 */
function timeouts(p) {
    var boardhometimeout1 = d3.select("#boardhometimeout1");
    var boardhometimeout2 = d3.select("#boardhometimeout2");
    var boardhometimeout3 = d3.select("#boardhometimeout3");

    if (data.plays[p].hometimeouts == 3){
        boardhometimeout1.attr("class", "boardtimeouton");
        boardhometimeout2.attr("class", "boardtimeouton");
        boardhometimeout3.attr("class", "boardtimeouton");
    }
    else if (data.plays[p].hometimeouts == 2){
        boardhometimeout1.attr("class", "boardtimeouton");
        boardhometimeout2.attr("class", "boardtimeouton");
        boardhometimeout3.attr("class", "boardtimeoutoff");
    }
    else if (data.plays[p].hometimeouts == 1){
        boardhometimeout1.attr("class", "boardtimeouton");
        boardhometimeout2.attr("class", "boardtimeoutoff");
        boardhometimeout3.attr("class", "boardtimeoutoff");
    }
    else if (data.plays[p].hometimeouts == 0){
        boardhometimeout1.attr("class", "boardtimeoutoff");
        boardhometimeout2.attr("class", "boardtimeoutoff");
        boardhometimeout3.attr("class", "boardtimeoutoff");
    }

    var boardawaytimeout1 = d3.select("#boardawaytimeout1");
    var boardawaytimeout2 = d3.select("#boardawaytimeout2");
    var boardawaytimeout3 = d3.select("#boardawaytimeout3");

    if (data.plays[p].awaytimeouts == 3){
        boardawaytimeout1.attr("class", "boardtimeouton");
        boardawaytimeout2.attr("class", "boardtimeouton");
        boardawaytimeout3.attr("class", "boardtimeouton");
    }
    else if (data.plays[p].awaytimeouts == 2){
        boardawaytimeout1.attr("class", "boardtimeouton");
        boardawaytimeout2.attr("class", "boardtimeouton");
        boardawaytimeout3.attr("class", "boardtimeoutoff");
    }
    else if (data.plays[p].awaytimeouts == 1){
        boardawaytimeout1.attr("class", "boardtimeouton");
        boardawaytimeout2.attr("class", "boardtimeoutoff");
        boardawaytimeout3.attr("class", "boardtimeoutoff");
    }
    else if (data.plays[p].awaytimeouts == 0){
        boardawaytimeout1.attr("class", "boardtimeoutoff");
        boardawaytimeout2.attr("class", "boardtimeoutoff");
        boardawaytimeout3.attr("class", "boardtimeoutoff");
    }
};

/**
 *  Changes focus bar sentiment
 */
function sentiment(s) {

    var focushomesent = d3.select("#focushomesent");
    var focusawaysent = d3.select("#focusawaysent");

    var hsent = data.sentiment[s].homesentiment.toFixed(2);
    var asent = data.sentiment[s].awaysentiment.toFixed(2);
    focushomesent.text(hsent);
    focusawaysent.text(asent);

}
