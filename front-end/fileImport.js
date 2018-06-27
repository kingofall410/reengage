var nodes;
var edges;
var network;
////////////////////////////////////////////////////////////////////////////////////////////////////
function buildGraph(importData) {
    
    console.log(importData);
    // create a network
    var container = document.getElementById('mynetwork');

    nodes = new vis.DataSet(importData.nodes);
    edges = new vis.DataSet(importData.edges);
    // provide the data in the vis format
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        "physics": {
            "enabled": true
        },
        "edges": {
            "smooth": false
        },
        "nodes": {
            "heightConstraint": 28,
            "widthConstraint": 28
        }
    };

    options["groups"] = importData.groups;
    
    console.log(options)
    
    // initialize your network!
    network = new vis.Network(container, data, options);

    network.on("afterDrawing", function(ctx) {
        updateBorders(ctx);
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////
function checkReadFile() {
    // Check for the various File API support.
    if (window.File && window.FileReader && window.FileList && window.Blob) {
        console.log("Supported browser")
    } else {
        alert('The File APIs are not fully supported in this browser.');
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function handleFileSelect(evt) {
    var file = evt.target.files[0]; // File object

    var reader = new FileReader();
    reader.onload = (function(theFile) {
        return function(e) {
            data = JSON.parse(e.target.result);
            buildGraph(data);
        };
    })(file);

    reader.readAsText(file);

  }

////////////////////////////////////////////////////////////////////////////////////////////////////
function readTextFile(file) {
    var rawFile = new XMLHttpRequest();
    rawFile.open("GET", file, false);
    rawFile.onreadystatechange = function ()
    {
        if(rawFile.readyState === 4)
        {
            if(rawFile.status === 200 || rawFile.status == 0)
            {
                var allText = rawFile.responseText;
                alert(allText);
            }
        }
    }
    rawFile.send(null);
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function updateGroupVisualization() {
    network.redraw()
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function updateBorders(ctx) {
    nodeArray = nodes.get();
    redCheckbox = document.getElementById('redgroup');
    blueCheckbox = document.getElementById('bluegroup');
    greenCheckbox = document.getElementById('greengroup');

    for (element in nodeArray) {

        node = nodeArray[element];
        var nodePosition = network.getPositions([node.id]);
        var nodeBox = network.getBoundingBox(node.id);
        offset = 0;
        isInGroup = false;

        if (redCheckbox.checked && node.inRedGroup) {
            //TODO:why is this number (22) different from the height constraints above?
            ctx.beginPath();
            ctx.strokeStyle = '#FF0000';
            ctx.lineWidth = 4;
            ctx.arc(nodePosition[node.id].x, nodePosition[node.id].y, 20, 0, 2 * Math.PI);
            ctx.stroke();
            offset += ctx.lineWidth;
            isInGroup = true;
        }

        if (greenCheckbox.checked && node.inGreenGroup) {
            //TODO:why is this number (22) different from the height constraints above?
            ctx.beginPath();
            ctx.strokeStyle = '#00FF00';
            ctx.lineWidth = 4;
            ctx.arc(nodePosition[node.id].x, nodePosition[node.id].y, 20+offset, 0, 2 * Math.PI);
            ctx.stroke();
            offset += ctx.lineWidth;
            isInGroup = true;
        }

        if (blueCheckbox.checked && node.inBlueGroup) {
            //TODO:why is this number (22) different from the height constraints above?
            ctx.beginPath();
            ctx.strokeStyle = '#0000FF';
            ctx.lineWidth = 4;
            ctx.arc(nodePosition[node.id].x, nodePosition[node.id].y, 20+offset, 0, 2 * Math.PI);
            ctx.stroke();
            offset += ctx.lineWidth;
            isInGroup = true;
        }

        /*if (blueCheckbox.checked || redCheckbox.checked || greenCheckbox.checked) {
            if (!isInGroup) {
                nodes.update({"id":node.id, "group": "inactiveGroup"});
            }
        } else {
            nodes.update({"id":node.id, "group": "defaultGroup"});

        }*/

    }
}