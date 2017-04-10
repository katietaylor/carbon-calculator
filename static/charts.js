


var options = {
  responsive: true
};

// Make Donut Chart of percent of different CO2 source types
var ctx_donut = $("#donutChart").get(0).getContext("2d");

$.get("/co2-per-datatype.json", function (response) {

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

    var myDonutChart = new Chart(ctx_donut, {
        type: 'doughnut',
        data: data,
        options: options
    });
    
});