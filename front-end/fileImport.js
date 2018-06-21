////////////////////////////////////////////////////////////////////////////////////////////////////
function buildGraph(importData) {
    // create a network
    var container = document.getElementById('mynetwork');

    // provide the data in the vis format
    var data = {
        nodes: importData.nodes,
        edges: importData.edges
    };
    var options = {
        physics:{
        enabled: false
        }
    };

    // initialize your network!
    var network = new vis.Network(container, data, options);
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