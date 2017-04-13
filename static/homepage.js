
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

var myLineChart;
function updateCo2LineGraph() {

    // Make Donut Chart of percent of different CO2 source types
    var ctx_line = $("#lineGraph");
    var yearData = {};
    yearData.year = $("#trend-year").val();

    if (myLineChart) {
        myLineChart.destroy();
    }
    $.get("/co2-trend.json", yearData, function (response) {

        var data = {
            labels: ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November",
                     "December"],
            datasets: [
                {
                    label: "Trips",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: "rgba(75,192,192,0.4)",
                    borderColor: "rgba(75,192,192,1)",
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: "rgba(75,192,192,1)",
                    pointBackgroundColor: "#fff",
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: "rgba(75,192,192,1)",
                    pointHoverBorderColor: "rgba(220,220,220,1)",
                    pointHoverBorderWidth: 2,
                    pointRadius: 1,
                    pointHitRadius: 10,
                    data: response.trip,
                    spanGaps: false,
                },
                {
                    label: "Electricity",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: "#36A2EB",
                    borderColor: "#36A2EB",
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: "#36A2EB",
                    pointBackgroundColor: "#fff",
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: "#36A2EB",
                    pointHoverBorderColor: "rgba(220,220,220,1)",
                    pointHoverBorderWidth: 2,
                    pointRadius: 1,
                    pointHitRadius: 10,
                    data: response.kwh,
                    spanGaps: false,
                },
                {
                    label: "Natural Gas",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: "#FFCE56",
                    borderColor: "#FFCE56",
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: "#FFCE56",
                    pointBackgroundColor: "#fff",
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: "#FFCE56",
                    pointHoverBorderColor: "rgba(220,220,220,1)",
                    pointHoverBorderWidth: 2,
                    pointRadius: 1,
                    pointHitRadius: 10,
                    data: response.ng,
                    spanGaps: false,
                }
            ]
        };
        
        myLineChart = new Chart(ctx_line, {
            type: 'line',
            data: data,
            options: options
        });
        
    });
}
updateCo2LineGraph();
$("#trend-year").on("change", updateCo2LineGraph);


// Get Zipcode ################################################################

$("#new-location-button").on("click", getZipcode);
    
function getZipcode(evt) {
    evt.preventDefault();

    var city = $("#city");
    var state = $("#state");

    var data = {};
        data.city = city.val();
        data.state = state.val();

    $.ajax({
        url: "/get-zipcode",
        data: data,
        success: function(response) {
            // change the distance in the dom to the response
            $("#zipcode").val(response);
            compareLocations();
        }
    });
}

// Compare Locations ##########################################################

$("#zipcode").on("change", compareLocations);

 
$("location-year").on("change", function () {
    if ($("#zipcode").val()) {
        compareLocations();
    console.log($("#zipcode").val());
    console.log("hello world");
    }
});

function compareLocations(evt) {
    var year = $("#location-year");
    var zipcode = $("#zipcode");

    var data = {};
        data.year= year.val();
        data.zipcode = zipcode.val();

    $.ajax({
        url: "/co2-other-location.json",
        data: data,
        success: function(response) {
            $("#location-comparison").show();
            
            $("#current-yr-total").html(response.current_yearly_co2);
            $("#new-yr-total").html(response.new_yearly_co2);
            $("#current-dly-rate").html(response.current_daily_rate);
            $("#new-dly-rate").html(response.new_daily_rate);
            $("#comparison-statement").html(response.comparison_statement);

            updateLocationBarChart(response);
        }
    });
}

// Location Bar Graph #########################################################

var locationBarChart;
function updateLocationBarChart(response) {

    // Make bar of percent of different CO2 source types
    var ctx_bar = $("#locationBarChart");

    if (locationBarChart) {
        locationBarChart.destroy();
    }
    
    var data = {
        labels: ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November",
                 "December"],
        datasets: [
            {
                label: "Current Location",
                backgroundColor: [
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(75, 192, 192, 0.2)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1,
                data: response.current_monthly_co2,
            },

            {
                label: "New Location",
                backgroundColor: [
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(255, 206, 86, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1,
                data: response.new_monthly_co2,
            }
        ]
    };
    
    locationBarChart = new Chart(ctx_bar, {
        type: 'bar',
        data: data,
        options: options
    });
        
}
