
# Usage

I havent packaged this up yet so its just some plain old python code you can run from the directory / command line (assumign you have python tooling)

Location as a field is a pain to extract. Orienteering event creators using Eventor often the event location them in a special Evenot message area (a blue box on the web site).
The location is found by looking for a key word e.g. "Location: The Park"

Example below takes the Newcastle organisation (29) and sepcifies the prefix "Location:" and sets a date start and date end
```
Python
MultiICS.py' '--organisationIds' '29' '--location' 'Location: ' '2019-10-01' '2020-03-31'
```

Example below looks for the prefix "Bay Orienteering Series" or a synonym "River Orienteering Series" and specifies the prefix "Venue:" and sets a date start and date end
```
Python
MultiICS.py' 'Bay Orienteering Series' '--synonym' 'River Orienteering Series' '--location' 'Venue: ' '2019-10-13' '2019-12-15'
```

Example below looks for the prefix "Sydney Summer" or a synonym "SSS" sets a date start and date end
```
Python
MultiICS.py' 'Sydney Summer' '-s' 'SSS' '2019-10-01' '2020-04-01' 
```
See results of these queries in this [directory](./docs/examples)


# Comments
This was originally designed as a web app - where you put in the search on a form....
If I were building this for an enteprrise  I would make it an API for people to use  but this is probably just ok for its occasional usage

