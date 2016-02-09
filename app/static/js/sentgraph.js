/**
 *  Draws the sentiment graph from the game JSON data
 */
function drawSentGraph(d){

    //var prestart = d3.min(data.gametime, function(d){ return d.time.$date; });
    //var postend = d3.max(data.gametime, function(d){ return d.time.$date; });

    var margin = {top: 20, right: 30, bottom: 20, left: 30}
        width = 700 - margin.left - margin.right,
        height = 300 - margin.top - margin.bottom;

    var svg = d3.select("#sentgraphcontainer")
                 .append("svg")
                 .attr("width", width + margin.left + margin.right)
                 .attr("height", height + margin.top + margin.bottom)
                 .append("g")
                 .attr("transform", 
                       "translate(" + margin.left + "," + margin.top + ")");
                 
    var x = d3.time.scale().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);

    var yAxis = d3.svg.axis().scale(y)
                  .orient("left")
                  .ticks(5)
                  .tickFormat(function(d){
        	           if(d == 1) { return '\uf118' }
        	           else if(d == 0) { return "\uf11a" }
        	           else if(d == -1) { return "\uf119"}
          	      });

    var xAxis = d3.svg.axis().scale(x).ticks(0)
        .orient("middle").outerTickSize(0);

    var homeline = d3.svg.line()
        .x(function(d) { return x(d.time.$date); })
        .y(function(d) { return y(d.homesentiment); });

    var awayline = d3.svg.line()
        .x(function(d) { return x(d.time.$date); })
        .y(function(d) { return y(d.awaysentiment); });

    // Scale the range of the data
    x.domain(d3.extent(data.gametime, function(d) { return d.time.$date; }));
    y.domain([-1, 1]);

    // x axis
    svg.append("g")
        .attr("class", "x axis")
    	.attr("transform", "translate(" + 0 + "," + eval(height/2) + ")")
        .call(xAxis);

    svg.append("g")         
            .attr("class", "grid")
            .attr("transform", "translate(0," + height + ")")

    // Home team line
    svg.append("path")
        .attr("class", "line")
        .attr("stroke", '#' + data.homecolor)
        .attr("fill", "none")
        .attr("stroke-width", "3px")
        .attr("d", homeline(data.gametime));

    // Away team line
    svg.append("path")
        .attr("class", "line")
        .attr("stroke", '#' + data.awaycolor)
        .attr("fill", "none")
        .attr("stroke-width", "3px")
        .attr("d", awayline(data.gametime));

    // y axis
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

};

