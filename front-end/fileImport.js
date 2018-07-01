var nodes;
var edges;
var network;
////////////////////////////////////////////////////////////////////////////////////////////////////
function buildGraph(importData) {
    
    console.log(importData);
    // create a network
    var container = document.getElementById('network');

    nodes = new vis.DataSet(importData.nodes);
    edges = new vis.DataSet(importData.edges);
    // provide the data in the vis format
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        "physics": {
            "enabled": true,
            "timestep": 0.2,
            "adaptiveTimestep": true
        },
        "edges": {
            "smooth": false
        },
        "nodes": {
            "heightConstraint": 28,
            "widthConstraint": 28
        },
        "layout": {
            improvedLayout:false
        },
        
    };
    
    options["groups"] = importData.groups;
    
    console.log(options)

    buildCheckboxes(importData.cliqueDefinitions);
    
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
    network.redraw();
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function checkAllCliques() {
    let selectall = document.getElementById("selectall");
    let checkboxDiv = document.getElementById("filters");
    for (i = 0; i < checkboxDiv.children.length; i++) {
        if (checkboxDiv.children[i] && checkboxDiv.children[i].id.startsWith("_")) {
            checkboxDiv.children[i].checked = selectall.checked;
        }
    }
    updateGroupVisualization();
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function buildCheckboxes(cd) {
    
    let checkboxDiv = document.getElementById("filters");
    let selectall = document.createElement("input");
    selectall.type = "checkbox";
    selectall.id = "selectall";
    selectall.addEventListener("click", checkAllCliques);

    let label = document.createElement('label')
    label.htmlFor = selectall.id;
    label.appendChild(document.createTextNode("Select All"));

    checkboxDiv.appendChild(selectall);
    checkboxDiv.appendChild(label);
    checkboxDiv.appendChild(document.createElement("br"));

    for (clique_id in cd) {

        clique = cd[clique_id];
        let groupName = clique["name"].slice(1);
        let checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = clique["name"];
        color = '#'+(Math.random()*0xFFFFFF<<0).toString(16);
        while (tinycolor(color).isLight()) {
            color = '#'+(Math.random()*0xFFFFFF<<0).toString(16);
        }
        checkbox.value = color;
        checkbox.addEventListener("click", updateGroupVisualization);
        label = document.createElement('label')
        label.htmlFor = checkbox.id;
        label.appendChild(document.createTextNode(groupName));

        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        checkboxDiv.appendChild(document.createElement("br"));
        checkboxDiv.appendChild(document.createTextNode(clique["description"]));
        checkboxDiv.appendChild(document.createElement("br"));
    }
    
}

////////////////////////////////////////////////////////////////////////////////////////////////////
function updateBorders(ctx) {
    let nodeArray = nodes.get();
    console.log("updateBorders")
    let isSegmented = document.getElementById('segmented').checked;
    
    for (element in nodeArray) {

        let node = nodeArray[element];
        let nodePosition = network.getPositions([node.id]);
        //let isInGroup = false;

        let activeGroups = 0;
        for (key in node) {
            if (key.startsWith("_")) {
                //console.log(key)
                activeGroups += (node[key]*document.getElementById(key).checked);
            }
        }

        //console.log(node.label, activeGroups)
        let step = 0;
        if (activeGroups > 1) {
            step = 0.1;
        } 
        let arcLength = 2*Math.PI;
        let drawLength = arcLength;
        let arcStart = 0;
        let radius = 18;

        if (isSegmented) {
            arcLength = arcLength/activeGroups;
            drawLength = arcLength-step;
        } 

        for (key in node) {
            if (key.startsWith("_")) {
                let checkbox = document.getElementById(key);
                if (node[key] && checkbox.checked) {
                    ctx.beginPath();
                    ctx.strokeStyle = checkbox.value;
                    console.log(checkbox.value)
                    ctx.lineWidth = 4;
                    ctx.arc(nodePosition[node.id].x, nodePosition[node.id].y, radius, arcStart, arcStart+drawLength);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.strokeStyle = "#FFFFFF"
                    ctx.arc(nodePosition[node.id].x, nodePosition[node.id].y, radius, arcStart+drawLength, arcStart+arcLength);
                    ctx.stroke();
                    if (isSegmented) {   
                        arcStart += arcLength;
                    } else {                
                        radius += ctx.lineWidth;
                    }
                }
            }
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