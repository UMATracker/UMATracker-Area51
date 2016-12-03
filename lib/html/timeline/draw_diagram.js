function draw_chord_diagram(matrix, color) {
    // From http://mkweb.bcgsc.ca/circos/guide/tables/
    // var matrix = [
    //     [11975,  5871, 8916, 2868],
    //     [ 1951, 10048, 2060, 6171],
    //     [ 8010, 16145, 8090, 8045],
    //     [ 1013,   990,  940, 6907]
    // ];

    var chord = d3.layout.chord()
        .padding(.05)
        .sortSubgroups(d3.descending)
        .matrix(matrix);

    var width = 600;
    var height = 600;
    var innerRadius = Math.min(width, height) * .41;
    var outerRadius = innerRadius * 1.1;

    var fill = d3.scale.ordinal()
        .domain(d3.range(4))
        .range(color);

    var svg = d3.select("body").append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    svg.append("g").selectAll("path")
        .data(chord.groups)
        .enter().append("path")
        .style("fill", function(d) { return fill(d.index); })
        .style("stroke", function(d) { return fill(d.index); })
        .attr("d", d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius))
        .on("mouseover", fade(.1))
        .on("mouseout", fade(1));

    var ticks = svg.append("g").selectAll("g")
        .data(chord.groups)
        .enter().append("g").selectAll("g")
        .data(groupTicks)
        .enter().append("g")
        .attr("transform", function(d) {
            return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
                + "translate(" + outerRadius + ",0)";
        });

    ticks.append("line")
        .attr("x1", 1)
        .attr("y1", 0)
        .attr("x2", 5)
        .attr("y2", 0)
        .style("stroke", "#000");

    ticks.append("text")
        .attr("x", 8)
        .attr("dy", ".35em")
        .attr("transform", function(d) { return d.angle > Math.PI ? "rotate(180)translate(-16)" : null; })
        .style("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })
        .text(function(d) { return d.label; });

    svg.append("g")
        .attr("class", "chord")
        .selectAll("path")
        .data(chord.chords)
        .enter().append("path")
        .attr("d", d3.svg.chord().radius(innerRadius))
        .style("fill", function(d) { return fill(d.target.index); })
        .style("opacity", 1);

    // Returns an array of tick angles and labels, given a group.
    function groupTicks(d) {
        var k = (d.endAngle - d.startAngle) / d.value;
        return d3.range(0, d.value, 1000).map(function(v, i) {
            return {
                angle: v * k + d.startAngle,
                label: i % 5 ? null : v / 1000 + "k"
            };
        });
    }

    // Returns an event handler for fading a given chord group.
    function fade(opacity) {
        return function(g, i) {
            svg.selectAll(".chord path")
                .filter(function(d) { return d.source.index != i && d.target.index != i; })
                .transition()
                .style("opacity", opacity);
        };
    }
}



function draw_timeline_diagram(tasks, taskNames, statusNames, colors) {
    var width = 350;
    var height = 580;

    // var tasks = [
    //
    // {
    //     "startDate": 10,
    //     "endDate": 20,
    //     "taskName": "E Job",
    //     "status": "FAILED"
    // },
    //
    // {
    //     "startDate": 30,
    //     "endDate": 40,
    //     "taskName": "A Job",
    //     "status": "RUNNING"
    // }];

    var taskStatus = {};
    for (var i=0; i<statusNames.length; i++){
        name = statusNames[i];
        taskStatus[name] = name;
    }

    // var taskNames = [ "D Job", "P Job", "E Job", "A Job", "N Job" ];
    var gantt = d3.gantt().taskTypes(taskNames).taskStatus(taskStatus);
    gantt.width(width);
    gantt.height(height);
    gantt(tasks);

    for (var i=0; i<statusNames.length; i++){
        attr = '.'+statusNames[i];
        $(attr).css({fill: colors[i]});
    }

    var svg = d3.select(".chart");
    svg.append("text")
        .attr("class", "x label")
        .attr("text-anchor", "end")
        .attr("x", width + 20)
        .attr("y", height+20)
        .text("Video frame number");

    svg.append("text")
        .attr("class", "y label")
        .attr("text-anchor", "end")
        .attr("y", width/3)
        .attr("x", -height/2.5)
        .attr("transform", "rotate(-90)")
        .text("Individual ID number");
}
