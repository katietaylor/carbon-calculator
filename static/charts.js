
var options = {
  responsive: true
};


// DONUT CHART ################################################################

var myDonutChart;
function updateCo2Donut() {

    // Make Donut Chart of percent of different CO2 source types
    var ctx_donut = $("#donutChart");
    var yearData = {};
    yearData.year = $("#donut-year").val();

    if (myDonutChart) {
        myDonutChart.destroy();
    }
    $.get("/co2-per-datatype.json", yearData, function (response) {
        var data = {
            labels: [
                "Trip",
                "Electricity",
                "Natural Gas"
            ],
            datasets: [
                {
                    data: response,
                    backgroundColor: [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56"
                    ],
                    hoverBackgroundColor: [
                        "#FF6384",
                        "#36A2EB",
                        "#FFCE56"
                    ]
                }]
            };
        myDonutChart = new Chart(ctx_donut, {
            type: 'doughnut',
            data: data,
            options: options
        });
        
    });
}
updateCo2Donut();
$("#donut-year").on("change", updateCo2Donut);


// LINE GRAPH ################################################################

var myLineGraph;
function updateCo2LineGraph() {

    // Make Donut Chart of percent of different CO2 source types
    var ctx_line = $("#lineChart");
    var yearData = {};
    yearData.year = $("#line-year").val();

    if (myLineGraph) {
        myLineGraph.destroy();
    }
    $.get("/co2-trend.json", yearData, function (response) {
        var data = {
            
            };
        myLineGraph = new Chart(ctx_line, {
            type: 'line',
            data: data,
            options: options
        });
        
    });
}
updateCo2LineGraph();
$("#donut-year").on("change", updateCo2LineGraph);
