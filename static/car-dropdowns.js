
var make = $("#make");
var model = $("#model");
var year = $("#car-year");
var cylinders = $("#cylinders");
var transmission = $("#transmission");

make.on("change", onMakeChange);
model.on("change", onModelChange);
year.on("change", onYearChange);
cylinders.on("change", onCylindersChange);
transmission.on("change", onTransmissionChange);

function onMakeChange(evt) {
    var data = {};
    data.make = make.val();

    model.prop("disabled", false);
    year.prop("disabled", false);
    cylinders.prop("disabled", true);
    transmission.prop("disabled", true);

    $.ajax({
        url: "/car-data",
        data: data,
        success: function(response) {

            cylinders.empty();
            transmission.empty();
            model.empty();
            year.empty();

            populateModels(response);
            populateYears(response);

        },
        error: function(response) {
        }
    });
}

function onModelChange(evt) {
    var data = {};
    data.make = make.val();
    data.model = model.val();

    cylinders.empty();
    transmission.empty();

    $.ajax({
        url: "/car-data",
        data: data,
        success: function(response) {
            populateYears(response);
        },
        error: function(response) {
        }
    });

    if (year.val()) {
        data.year = year.val();

        cylinders.prop("disabled", false);
        transmission.prop("disabled", false);

        $.ajax({
            url: "/car-data",
            data: data,
            success: function(response) {
                populateCylinders(response);
                populateTransmissions(response);
            },
            error: function(response) {
            }
        });
    }
}

function onYearChange(evt) {
    var data = {};
    data.make = make.val();
    data.year = year.val();

    cylinders.empty();
    transmission.empty();

    $.ajax({
        url: "/car-data",
        data: data,
        success: function(response) {
            populateModels(response);
        },
        error: function(response) {
        }
    });

    if (model.val()) {
        data.model = model.val();

        cylinders.prop("disabled", false);
        transmission.prop("disabled", false);

        $.ajax({
            url: "/car-data",
            data: data,
            success: function(response) {
                populateCylinders(response);
                populateTransmissions(response);
            },
            error: function(response) {
            }
        });
    }
}

function onCylindersChange(evt) {
    var data = {};
    data.make = make.val();
    data.model = model.val();
    data.year = year.val();
    data.cylinders = cylinders.val();

    $.ajax({
        url: "/car-data",
        data: data,
        success: function(response) {
            populateTransmissions(response);
        },
        error: function(response) {
        }
    });
}

function onTransmissionChange(evt) {
    var data = {};
    data.make = make.val();
    data.model = model.val();
    data.year = year.val();
    data.transmission = transmission.val();

    $.ajax({
        url: "/car-data",
        data: data,
        success: function(response) {
            populateCylinders(response);
        },
        error: function(response) {
        }
    });
}

function populateModels(response) {
    var selectedModel = model.val();
    model.empty();
    model.append("<option value=''>SELECT MODEL</option>");
    var modelsFound = [];

    // create a list of unique models
    $.each(response, function(i, car) {
        if ($.inArray(car.model, modelsFound) == -1) {
            modelsFound.push(car.model);
        }
    });
    // sort the list and append it to the Model dropdown list
    $.each(modelsFound.sort(), function(i, carModel) {
        var optionSelected = "";
        // if model has already been selected, keep current model as selected value
        if (carModel == selectedModel) {
                optionSelected = "selected='selected'";
            }
        model.append("<option " + optionSelected + " value='"+carModel+"'>"+carModel+"</option>");
    });
}

function populateYears(response) {
    var selectedYear = year.val();
    year.empty();
    year.append("<option value=''>SELECT YEAR</option>");
    var yearsFound = [];

    // create a list of unique years
    $.each(response, function(i, car) {
        if ($.inArray(car.year, yearsFound) == -1) {
            yearsFound.push(car.year);
        }
    });
    // sort the list and append it to the Year dropdown list
    $.each(yearsFound.sort(), function(i, carYear) {
        var optionSelected = "";
        // if year has already been selected, keep current year as selected value
        if (carYear.toString() == selectedYear) {
                optionSelected = "selected='selected'";
            }
        year.append("<option " + optionSelected + " value='"+carYear+"'>"+carYear+"</option>");
    });
}

function populateCylinders(response) {
    var selectedCylinders = cylinders.val();
    cylinders.empty();
    cylinders.append("<option value=''>SELECT CYLINDERS</option>");
    var cylindersFound = [];

    // create a list of unique cylinders
    $.each(response, function(i, car) {
        if ($.inArray(car.cylinders, cylindersFound) == -1) {
            cylindersFound.push(car.cylinders);
        }
    });
    // sort the list and append it to the Cylinders dropdown list
    $.each(cylindersFound.sort(), function(i, carCylinders) {
        var optionSelected = "";
        // if cylinders has already been selected, keep current cylinders as selected value
        if (carCylinders.toString() == selectedCylinders) {
                optionSelected = "selected='selected'";
            }

        cylinders.append("<option " + optionSelected + "value='"+carCylinders+"'>"+carCylinders+"</option>");
    });
}

function populateTransmissions(response) {
    var selectedTransmission = transmission.val();
    transmission.empty();
    transmission.append("<option value=''>SELECT TRANSMISSION</option>");
    var transmissionsFound = [];

    // create a list of unique transmission
    $.each(response, function(i, car) {
        if ($.inArray(car.transmission, transmissionsFound) == -1) {
            transmissionsFound.push(car.transmission);
        }
    });
    // sort the list and append it to the Year dropdown list
    $.each(transmissionsFound.sort(), function(i, carTransmission) {
        var optionSelected = "";
        // if transmission has already been selected, keep current transmission as selected value
        if (carTransmission.toString() == selectedTransmission) {
                optionSelected = "selected='selected'";
            }
        transmission.append("<option " + optionSelected + "value='" + carTransmission + "'>" + carTransmission + "</option>");
    });
}