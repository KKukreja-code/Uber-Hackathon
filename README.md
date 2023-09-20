# Hackstreet boys

## Table of contents
* [General info](#general-info)
* [Introduction](#introduction)
* [Code](#code)
* [Setup](#setup)
* [Troubleshooting](#troubleshooting)

## general info

built using:  
* python 3.11.5
  * Flask 2.3.3
  * google maps API 3.54
  * jinja 3.1.2
  * SQLite 3.41.1
* CSS 4.15
* java script ES13
* HTML 5
  
## Introduction 

(website name) is a multipurposed website designed to promote environmental friendliness and improve traffic congestion. It does this by allowing users to ear points through the use of public transport and ridesharing. These points would be used to provide discounts for certain services as an incentive for environmentally friendly behaviour. We prodive the shortest route, the route that releases the least amount of CO2 along with routes with less walking and transfers for disabled people.

## Code Overview

One purpose of the website is to find use the google maps API to find the distance and carbon footprint of trips that users input for different modes of transport. It then returns the number of points they gain for doing actions like ridesharing and taking public transport based on the amount of CO2 they have saved compared to riding solo. The code uses a carbon footprint calculator, taking into account fuel burning rates and current traffic to generate a trip's carbon footprint. 

The code also uses the google maps API to tailor to the disabled/elderly by providing less walking routes. 

The code is also able to take multiple inputs for people who want to share rides and use an optimisation algorithm to pair the rides up to cover the minimal distance. These ridesharing requests can be made in advance as the requests are stored on a permanent database, allowing shared rides to be more organised and easier to use for customers. 

The code utilises this database to store all user login details, their points and money in their account, which is constantly being updated as their points balance updates. 

## Setup 

* Download accounts.db
* pip install previously listed modules

## Troubleshooting

If you put boundary data in the code (put the starting point in the wrong country or in the middle of the ocean) the code handles it properly and throws up an error message to prevent misuse and misleading information.  

### Important:

if the github database does not work try to run our code on this replit link:

https://replit.com/@KrishivKukreja/Hackstreet-Boys
