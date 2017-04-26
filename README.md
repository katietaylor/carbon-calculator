# calCO2

![alt text](/static/img/screenshots/homepage_top.png "Homepage")

Using publicly available emission factor data from the EPA, the app calculates a user’s carbon footprint based on electricity and natural gas use as well as miles driven. The app visualizes the data to show how energy use decisions affect your carbon footprint over time.

Tech Stack: Python, Flask, JavaScript, AJAX, PostgreSQL, SQLAlchemy, Chart.js, Jinja, Bootstrap

In the profile, users can set up their residence and cars. For the residence, what I care about is the zipcode, because I use that to lookup their carbon emission factor, depending on what egrid region they are in.
![alt text](/static/img/screenshots/profile.png "Profile")

They can also add their cars, so they don’t have to reselect it each time they enter a new trip. The dropdown list for adding a new car were written using javascript and AJAX.

Users can then add in their electricity, natural gas data, and trip data. The trip data uses the Google Distance API to calculate the distance. So a user can enter in their starting location and their destination and the API will determine how far they drove.
![alt text](/static/img/screenshots/trip.png "Homepage")

Once a user has some data entered, they can go back to the dashboard. At the top there is a high level carbon footprint. I have also compared that to the number of trees it takes to offset that carbon, to put your footprint into terms that everyone can relate to.

Then I have 4 different graphs breaking down the data in different ways. I show how your footprint varies month-to-month, and year-to-year. I have also compared each day of the week and how much each source contributes to your overall footprint. I am using chart.js and ajax requests to populate this data, and a lot of algorithms under the hood to aggregate and splice the data. 
![alt text](/static/img/screenshots/graphs.png "Graphs")

I also made 2 sets of graphs that see how your footprint would change if you lived in a new location or if you are contemplating buying a new car.
![alt text](/static/img/screenshots/car_comparison.png "Car Comparison")