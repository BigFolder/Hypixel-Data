# [Example of updating Google Spreadsheet](https://docs.google.com/spreadsheets/d/1HIuR6UwqzY7NjcOvMB4Z0gw68RZRKjDAq9ettuaQ4X4/edit?usp=sharing)

## This Repository holds a base example of how to use Machine learning models created in sklearn to help you decide which items you want to invest in on the game.


### Current Models from sklearn being used (You can see the directory "Bazaar" to view how the simple creation of each model was done. I wanted to post the full run through, but I wanted to use libraries that are in sklearn by default(no LGBM) NOTE: HistGradientBoostClassifier can used in trial and should be similar to LGBM now), parameter tweaking is not shown here sadly.

- AdaBoostingClassifier
- KNearestNeighbor
- RandomForestClassifier
- ExtraTreesClassifier
- BaggingClassifier
- GradientBoostingClassifier

## What are they predicting?

Over the last Summer I had some friends collect data from users in their discord servers, they were shown the information we used to fit each model, and the users gave it a rating from 0-9. When there was enough data to really work with, the models were then created and tweaked. The rating is called "reliability" for our purposes simply due to us having multiple uses for this prediction. 

With the use of some of the functionality from [Baritone](https://github.com/cabaletta/baritone) I believe a bot can be created to efficiently and effectively do Bazaar work for you, so far trials are showing to be successful, However with a bit more data (Perhaps some type of rolling average of each week for an entire year) it will be working signifigantly well.


###
