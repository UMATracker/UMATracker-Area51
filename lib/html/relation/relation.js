if (String.prototype.format == undefined) {
    String.prototype.format = function(arg)
    {
        var rep_fn = undefined;
        if (typeof arg == "object") {
            rep_fn = function(m, k) { return arg[k]; }
        }
        else {
            var args = arguments;
            rep_fn = function(m, k) { return args[ parseInt(k) ]; }
        }

        return this.replace( /\{(\w+)\}/g, rep_fn );
    }
}

function plus(a, b){
    return a + b;
}

function draw_chord_diagram(matrix, color) {
    nodes_list = [];
    edges_list = [];
    selected_nodes = [];

    var max_node_weight = 0;
    for(var i=0; i<matrix.length; i++){
        var w = matrix[i].reduce(plus, 0);
        var c = color[i];
        nodes_list.push({
            data: {
                id : i,
                weight: w,
            },
            style: {
                'background-color': c,
            }
        });

        max_node_weight = Math.max(w, max_node_weight);
        selected_nodes.push(true);
    }

    var max_edge_weight = 0;
    for(var row=0; row<matrix.length; row++){
        for(var col=row+1; col<matrix.length; col++){
            var w = matrix[row][col];
            if (w!=0){
                edges_list.push({
                    data: {
                        id: "e"+row+col,
                        source: row,
                        target: col,
                        weight: w,
                    },
                });
                max_edge_weight = Math.max(w, max_edge_weight);
            }
        }

        var sum = 0;
        for(var col=0; col<matrix.length; col++){
            if(col==row){
                nodes_list[row]['data']['n'+col] = 0;
            }
            else{
                var w = matrix[row][col];
                nodes_list[row]['data']['n'+col] = w;
                sum += w;
            }
        }
        for(var col=0; col<matrix.length; col++){
            if (sum > 0) {
                nodes_list[row]['data']['n'+col] /= sum;
                nodes_list[row]['data']['n'+col] *= 100;
            }
        }
    }

    json = {
        'width': 'mapData(weight, 0, {0}, 0, 80)'.format(max_node_weight),
        'height': 'mapData(weight, 0, {0}, 0, 80)'.format(max_node_weight),
        'content': 'data(id)',
        'text-background-color': 'white',
        'text-background-opacity': '0.5',
        // 'background-color' : 'black',
        'background-opacity' : '1',
        'border-color': 'black',
        'border-width': 1,
        'pie-size': '80%',
        'pie-border-color': 'black',
        'pie-border-width': 1,
    }
    for (var i=0; i<color.length; i++){
        var color_option = 'pie-{0}-background-color'.format(i+1);
        var size_option = 'pie-{0}-background-size'.format(i+1);
        var map_function = 'data(n{0})'.format(i);

        json[color_option] = color[i];
        json[size_option] = map_function;
    }

    console.log(json);

    options = {
        style: cytoscape.stylesheet()
        .selector('node')
        .css(json)
        .selector('edge')
        .css({
            'line-color': 'black',
            // 'target-arrow-color': 'black',
            // 'source-arrow-color': 'black',
            // 'target-arrow-shape': 'triangle',
            // 'source-arrow-shape': 'triangle',
            'opacity': '1',
            'width' : 'mapData(weight, 0, {0}, 0, 20)'.format(max_edge_weight),
            'content': 'data(weight)',
            'text-background-color': 'white',
            'text-background-opacity': '0.5',
        })
        .selector(':selected')
        .css({
            // 'background-color': 'black',
            'opacity': 1
        })
        .selector('.faded')
        .css({
            'opacity': 0.25,
            'text-opacity': 0
        }),

        elements: {
            nodes: nodes_list,
            edges: edges_list
        },

        layout: {
            name: 'circle',
            padding: 10
        },

        ready: function(){
            window.cy = this;
            window.selected_nodes = selected_nodes;
        }
    };
    $('#cy').cytoscape(options);

    window.cy.on('click', 'node', function(evt){
        var target_node = evt.cyTarget;
        var i = target_node.data('id');
        window.selected_nodes[i] = !window.selected_nodes[i];

        if(window.selected_nodes[i]){
            target_node.style({'opacity' : 1});
        }
        else{
            target_node.style({'opacity' : 0.5});
        }

        window.cy.edges().forEach(function(edge){
            edge.style({'opacity' : 0.5});
        });

        window.cy.nodes().forEach(function( node ){
            var id = node.data('id');

            if(window.selected_nodes[id]){
                node.connectedEdges().forEach(function( edge ){
                    edge.style({'opacity' : 1});
                });
            }
        });
    });

    // window.cy.nodes().forEach(function(node){
    //     var c = color[parseInt(node.data('id'))];
    //     node.style({ 'background-color': c});
    // });
}

function test(){
    var matrix = [
        [    0, 5871, 8916, 2868],
        [ 5871,    0, 2060, 6171],
        [ 8916, 2060,    0, 8045],
        [ 2868, 6171, 8045,    0]
    ];
    var color = ['#80BFFF', '#E8747C', '#74CBE8', '#74E883', ];
    draw_chord_diagram(matrix, color);
}
