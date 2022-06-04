import datetime
import json
import sys
import os
import requests
import selenium

from pprint import PrettyPrinter
from bs4 import BeautifulSoup, Comment
# from sympy import O

from env import load_environment_variables

pp = PrettyPrinter(indent=4)

CHROMEDRIVER_PATH = "./chromedriver"
ENV_PATH = "../../.env"

class Scraper:
    ''' Implements methods that allow for the web-scraping of data from various Durham University websites. '''

    def __init__(self, username:str, password:str) -> None:
        '''
        `username` and `password` are needed to authorize the requests to the various pages.
        
        ---

        ### Parameters:
        - `username` (required) --> a valid CIS username.
        - `password` (required) --> the password corresponding to `username`.
        '''

        self.BASE_URLS = [    
            "https://timetable.dur.ac.uk",                   # TEACHING_TIMETABLE_BASE_URL
            "https://timetable.dur.ac.uk/week_patterns.htm", # WEEK_PATTERNS_URL
            "https://timetable.dur.ac.uk/module.htm"         # MODULE_TIMETABLES_URL
        ]

        self.username = username
        self.password = password
    
    # ----------

    @staticmethod
    def add_auth_to_url(base_url:str, username:str, password:str) -> str:
        '''
        Adds authentication to `base_url`.

        ---

        ### Parameters:
        - `base_url` (required) --> the URL for which autorisation is needed.
        - `username` (required) --> a valid CIS username.
        - `password` (required) --> the password corresponding to `username`.

        ---

        ### Example return value:
        ```python
        "https://abcd12:Abcd1234*@www.dur.ac.uk/directory/password/"
        ```

        ---

        ### Notes:
        - In the browser, sometimes when you visit a website, before the page loads a popup will appear
        saying something like "This site wants you to log in" and you are prompted to enter a username
        and password.
        - To get round this you can add the username and password to the url
        - You add a string like so: `'{username}:{password}@'` between the `https://` and the rest of the url.
        '''
        return base_url[:8] + username + ":" + password + "@" + base_url[8:]

    # ----------

    def scrape_raw_week_pattern_data(self) -> list[list[str]]:
        '''
        Helper function for `self.get_week_patterns`. Returns a 2D list.

        ---

        ### Notes:

        This method uses Selenium in order to emulate a browser in order to scrape the week patterns page.
        This solves the problem that I was having before; BeautifulSoup was scraping the page SOURCE which contained a <script> tag which dynamically (?) generates the <tr>s.
        As such, they weren't present in the table source, so BeautifulSoup couldn't actually extract the week patterns data.
        Using Selenium avoids this issue.
        
        ---

        ### Useful references:

        - ChromeDriver - https://chromedriver.chromium.org/getting-started (includes example code)
        - Selenium Python bindings - https://selenium-python.readthedocs.io/getting-started.html
        - Helpful StackOverflow answer on how to open the browser window "silently" - https://stackoverflow.com/a/48775203
        '''

        # a class containing class variable constants used in the `find_element` method
        from selenium.webdriver.common.by import By

        # ----------

        # not really sure what this Service thingy does, but apparently it's necessary.
        # `selenium.webdriver.Chrome()`` allows you to pass the path to the `chromedriver` file, but this is deprecated.
        # using this `service` thing circumvents this.
        service = selenium.webdriver.chrome.service.Service(CHROMEDRIVER_PATH)
        service.start()

        # telling the driver to not open an actual Chrome window
        options = selenium.webdriver.chrome.options.Options()
        options.add_argument("headless")

        # this is like the equivalent of the BeautifulSoup class (as far as I have understood)
        driver = selenium.webdriver.Chrome(service=service, options=options)

        url = Scraper.add_auth_to_url("https://timetable.dur.ac.uk/week_patterns.htm", self.username, self.password)
        driver.get(url)

        table = driver.find_element(by=By.TAG_NAME,value="table")

        trs = table.find_elements(by=By.TAG_NAME, value="tr")

        # the first two <tr>'s are the headers of the table.
        # they look like this:
        #   +–––––––––––––––––––––––––––––+––––––––––––––––––––––+
        #   |       Syllabus Weeks        |   Durham Weeks       |
        #   +–––––––––––––+–––––––––––––––+––––––+–––––––––––––––+
        #   | Week Number | Calendar Date | Term | Teaching Week |
        #   +–––––––––––––+–––––––––––––––+––––––+–––––––––––––––+

        data = list()

        for tr in trs[2:]: # skipping the two rows in the mini-diagram above

            # the <td> elements in the current <tr>
            # each element in the list is of type `<selenium.webdriver.remote.webelement.WebElement`
            tds = tr.find_elements(by=By.TAG_NAME, value="td")

            row = [web_element.text.strip() for web_element in tds]
            
            data.append(row)
        
        # ----------------------------------------------------------------- #
        # --- Find academic year and add it to the table contents list. --- #
        # ----------------------------------------------------------------- #

        # (this info isn't actually in the <table> element in the webpage, but it's necessary to work out the year for each date in the table)

        # the textContent of the element that contains the academic year.
        # the raw value will be something like "2022-23 Teaching Timetable"
        academic_year_raw = driver.find_element(by=By.CLASS_NAME, value="l2sitename").text.strip()
        
        academic_year_lower = academic_year_raw.split()[0].split("-")[0]
        academic_year_upper = academic_year_lower[:2] + academic_year_raw.split()[0].split("-")[1]

        data.append([academic_year_lower, academic_year_upper])

        # -----

        driver.quit()

        return data

    # ----------

    def get_week_patterns(self, list_or_dict:str = "dict", _print:bool = False) -> 'list|dict':
        '''
        Returns a 2D `list` of the week patterns in the current academic year.

        ---

        ### Parameters:
        - `list_or_dict` (optional) --> either `'dict'` or `'list'` depending on whether you want the return value to be of type `dict` or `list`.
        - `_print` (optional) --> `True` if you want the output to be printed, `False` if not. The output is printed using the `pprint.PrettyPrinter` class' `pprint` method.
        '''
        
        week_patterns = self.scrape_raw_week_pattern_data()

        year_span = week_patterns[-1]
        del week_patterns[-1]
        
        week_patterns.sort(key=lambda x: int(x[0].split()[1])) # sorts by the week number

        # ---------

        # used in 'get_year' below
        all_dates = [date for sub_list in week_patterns for date in sub_list[1].split(" - ")]

        def get_year(s:str) -> str:
            '''
            Given `s` (a date, e.g. 'Fri 30 Jul'), returns the year of the date.
            
            The way to determine which year the date is in is by using the `all_dates` `list`.
            `first_jan_date` is the index of the first occurence of `"Jan"` in `all_dates`.
            If `s`'s index in `all_dates` is less than `first_jan_date`, its year is `year_span[0]`.
            Else, it's `year_span[0]`.
            '''
            # the index of the first date in 'all_dates' that's in January
            first_jan_date = [date.split()[-1] for date in all_dates].index("Jan")
            if all_dates.index(s) < first_jan_date:
                return year_span[0]
            else:
                return year_span[1]
        
        def convert_string_to_date(s:str) -> 'datetime.date':
            ''' Accepts a string representing a 5-day week (e.g. `"Mon 19 Jul - Fri 23 Jul"`), and returns two python `datetime.date` objects representing the Monday and Friday. '''
            # 'None' so that I can simply use MONTHS.index("Jan") to get January's month number in the year
            MONTHS = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            date1, date2 = s.split(" - ")

            # the _ is the name of the day (e.g. "Mon") - this isn't needed so just ignore it
            _, date1_day, date1_month = date1.split()
            _, date2_day, date2_month = date2.split()

            date1_year = get_year(date1)
            date2_year = get_year(date2)

            date1 = datetime.date(int(date1_year), MONTHS.index(date1_month), int(date1_day))
            date2 = datetime.date(int(date2_year), MONTHS.index(date2_month), int(date2_day))

            return [date1, date2]

        # ---------

        # mapping each "Calendar Date" to a python datetime.date object instead of just a string
        for subarray in week_patterns:
            # `subarray[0]` --> "Week Number", i.e. a `str` saying "Week" and then a number. Goes from 1 to 52
            # `subarray[1]` --> "Calendar Date", e.g. 'Mon 09 Aug - Fri 13 Aug'.
            # `subarray[2]` --> "Term", i.e. if the week is part of a Durham term ("Michaelmas", "Epiphany" or "Easter")
            # `subarray[3]` --> "Teaching Week". If the week is during term time, it'll be either "Induction", "Teaching week [number]" or "Exam period". Else, it's empty.
            subarray[1] = convert_string_to_date(subarray[1])

        # ---------

        if list_or_dict == "list":

            if _print:
                pp.pprint(week_patterns)

            return week_patterns

        else: # list_or_dict == "dict"

            week_patterns_dict = dict()

            # turns each subarray into an object and adds it to 'week_patterns_dict'
            for sub_list in week_patterns:
                week_number = sub_list[0].split()[1]
                week_patterns_dict[week_number] = {
                    "Calendar Date": sub_list[1],
                    "Term": sub_list[2],
                    "Teaching Week": sub_list[3],
                }

            if _print:
                pp.pprint(week_patterns_dict)

            return week_patterns_dict

    # ----------

    @staticmethod
    def get_datetime_date_from_week_number_and_dotw(week_number:str, day_of_the_week:str) -> 'datetime.date':
        '''
        Given a `week_number` and `day_of_the_week`, returns a `datetime.date` object.

        ---

        ### Parameters:
        - `week_number` (required) --> a valid week number (a number somewhere in the range 1-52, in string form).
        - `day_of_the_week` (required) --> one of `['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']`

        ---

        ### Notes
        - `Scraper.get_week_patterns()[<<week_number>>]["Calendar Date"][0]` gets you the `datetime.date` of the Monday of `week_number`.
        - `day_of_the_week` dictates how many days you need to add onto the Monday date to get the specific day of the week.
        - e.g. If `day_of_the_week` is `"Wednesday"`, you add a `datetime.timedelta(days=2)` to the Monday date to get the Wednesday date.

        '''

        DAYS_OF_THE_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        week_patterns = Scraper.get_week_patterns()

        week_monday_date = week_patterns[week_number]["Calendar Date"][0]
        number_of_added_days = DAYS_OF_THE_WEEK.index(day_of_the_week)

        new_date = week_monday_date + datetime.timedelta(days = number_of_added_days)
        
        return new_date

    # ----------

    def handle_request(self, base_url:str) -> str:
        '''
        Handles the request to the url at `self.BASE_URLS[url_index]`.
        
        ---

        ### Parameters:
        - `base_url` (required) --> the `str` url from which to request data.
        '''

        # adding the username and password into base_url.
        # this won't circumnavigate 2FA but does permit access to certain uni sites that only require your CIS username and password
        # e.g. "https:// + abdc12 + : + 1Abcd* + @ + timetable.dur.ac.uk"
        # url_with_auth = base_url[:8] + self.username + ":" + self.password + "@" + base_url[8:]
        url_with_auth = Scraper.add_auth_to_url(base_url, self.username, self.password)

        try:
            response = requests.get(url_with_auth)

            # if the response status code is 400 or above
            if not response.ok:
                # print(response.text)
                print("Error in connecting to server.")
                print("Response status code:", response.status_code)
                print("Reason:", response.reason)
                sys.exit(1)
            else:
                return response.text

        except:
            sys.exit(1)

    # ----------

    def user_credentials_are_valid(self, cis_username:str, password:str) -> bool:
        '''
        Validates that the person is actually a member of the university.

        Does this by making a request to a server endpoint requiring authentication, using the user's CIS email and password.
        If the request is successful, the person is a valid user, so returns `True`. Else, returns `False`.
        '''

        BASE_URL = "https://www.dur.ac.uk/directory/password/"

        url_with_auth = Scraper.add_auth_to_url(BASE_URL, cis_username, password)

        response = requests.get(url_with_auth)

        print("response.reason", response.reason, response.status_code)

        # if response.ok:
        if response.reason == "OK":
            return True

        # the request didn't work (NOT NECESSARILY BECAUSE THE USER ISN'T A MEMBER OF DURHAM UNIVERSITY)

        elif response.reason == "Unauthorized":
            print("response.reason -->", response.reason)
            return False
        
        else:
            print(response.status_code, response.reason)
            return False

    # ----------
    
    def get_module_timetable_url_parameters(self) -> dict:
        '''
        Scrapes the page at `https://timetable.dur.ac.uk/module.htm` to get the URL parameters needed to scrape the module timetable information.

        - The data I'm looking for is in the `<tr>`s (i.e. rows) of a <table>
        - Each `<tr>` has two `<td>` tags:
            - the first contains details of the type of options (e.g. `'Select Module(s) to View:'`)
            - the second contains the `<select>` tag which contains the `<option>`s which are the parameters I'm looking for
        - So I must extract the data from the `<option>` tags
        '''

        response_text = self.handle_request(base_url = self.BASE_URLS[2])
        soup = BeautifulSoup(response_text, "html.parser")

        # stores the overall data from the table
        params = {}

        # [:-1] because the last row in the table is essentially empty - it's just a button saying "View Timetable"
        for tr in soup.find_all("tr"):
            # print(tr)
            # print("*"*30)
            tds = tr.find_all("td")

            # e.g. "Select Start and End Time:"
            option_type = tds[0].contents[0]

            # stores the values for all the individual options in this row's <select>
            # there are multiple <option>s
            options = list()

            select = tds[1]
            for option in select.find_all("option"):
                
                option_text_content = option.contents[0]

                # idk what this is, but there's a random <option> tag with no value and this as the text content...
                if option_text_content == "...........................................":
                    continue

                options.append([option_text_content, option["value"]])
                  
            params[option_type] = options
        
        return params

    # ----------

    def get_module_timetable(self, module_codes:list[str], print_activities:bool = False) -> list[dict]:
        '''
        Given a `list` of module codes, scrapes the module's timetable across the whole year.
        
        ---

        The return value is a `list` of `dict`s. Each `dict` will look something like the below example:

        ```python
        {
            "Day Of The Week": str, # e.g. "Monday".
            "Activity":        str, # the code for the specific lecture/tutorial/practical etc. E.g. "COMP2181/PRAC/001".
            "Description":     str, # this is basically just the name of the module. E.g. "Programming Paradigms".
            "Module":          str, # the module code. E.g. "COMP2181".
            "Start":           str, # 24h time, e.g. "09:00".
            "End":             str, # 24h time, e.g. "17:00".
            "Duration":        str, # hours and minutes, e.g. "2:00".
            "Room":            str|"", # either a room code or empty string. Room code example: "D/RH025"
            "Staff":           str|list|"", # either a single string or a list of strings or an empty string
            "Weeks":           list[list[str,str]], # a list of single numbers, or lists of pairs of numbers.
            "Planned Size":    str|"" # either a numeric string denoting the capacity of the room, or an empty string.
        }
        ```

        ---

        In the Chrome developer panel, under `Sources`, there's a file called `/js/form.js` which contains the below code; it redirects you to the url constructed from the below variables.
        `window.location = "//" + host + "/reporting/" + printstyle + ";" + object + ";name;" + objectstr + "?days=" + days + "&weeks=" + weekstr + "&periods=" + periods + "&template=" + template + "&height=100&week=100";`

        - `host`       --> `'timetable.dur.ac.uk'`
        - `printstyle` --> value from `"Select Report Style:"` sub-object in `moduleTimetableURLParameters.json`.
        - `object`     --> one of the options from the base `https://timetable.dur.ac.uk/` page. These are:
            - Durham = `room_dur`
            - Staff = `staff`
            - Modules = `module`
            - Weeks = `week_patterns`
        - `objectstr`  --> not entirely sure yet for all of the `object` possibilities above, but I know for modules this is all the module names joined by `%0D%0A`
            - e.g. `ACCT1031%0D%0ACOMP2261%0D%0ACOMP2271%0D%0ACOMP2281%0D%0ACOMP3012%0D%0A`
        - `days`       --> value from `"Select Day(s):"` sub-object in `moduleTimetableURLParameters.json`.
        - `weekstr`    --> value from `"Select Week(s):"` sub-object in `moduleTimetableURLParameters.json`.
        - `periods`    --> value from `"Select Start and End Time:"` sub-object in `moduleTimetableURLParameters.json`.
        - `template`   --> this is equal to `object + '+' + printstyle`.
            - In this case, we only care when `object = 'module'` and `printstyle` will likely be `Master`

        example url = https://timetable.dur.ac.uk/reporting/Master;module;name;COMP2261%0D%0ACOMP2271%0D%0ACOMP2281%0D%0ACOMP3012%0D%0A?days=1-5&weeks=12-21&periods=5-41&template=module+Master&height=100&week=100
        '''

        WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # -------------------------------------
        # Establishing the URL query parameters

        host = "timetable.dur.ac.uk"
        printstyle = "textspreadsheet"                        # "List"
        _object = "module"
        objectstr = "%0D%0A".join(module_codes) + "%0D%0A"
        days = "1-7"                                          # "All Week"
        weekstr = ";".join([str(num) for num in range(1,53)]) # weeks 1 through 52 i.e. every week of the whole year
        periods = "1-56"                                      # "08:00 - 22:00 (All Day)"
        template = _object + "+" + printstyle                 # "module+Master" 

        # -------------------------------------------
        # retrieving the HTML from the Durham website

        # url = "https://" + host + "/reporting/" + printstyle + ";" + _object + ";name;" + objectstr + "?days=" + days + "&weeks=" + weekstr + "&periods=" + periods + "&template=" + template + "&height=100&week=100"
        url = "".join([
            "https://",host,"/reporting/",printstyle,";",_object,";name;",objectstr,
            "?days=",days,
            "&weeks=",weekstr,
            "&periods=",periods,
            "&template=",template,
            "&height=100&week=100",
        ])
        response_text = self.handle_request(url)
        soup = BeautifulSoup(response_text, "html.parser")

        # the formatting is weird - loads of <table>'s are used.

        # there's a <table> encoding a header which says the module name (e.g. "Module: COMP2221 - Programming Paradigms	Dept: Computer Science	Weeks: 1-52 (19 Jul 2021, 17 Jul 2022)")
        # then there's a <span> saying which day is it
        # then there's (possibly) a <table> containing the activity information
        #   - the attributes are ["Activity", "Description", "Module", "Start", "End", "Duration", "Room", "Staff", "Weeks", "Planned Size"]

        # basically, there are gazillions of <tables>, so the easiest way to find them is to search based on the activity <table> attributes.
        # these are ["Activity", "Description", "Module", "Start", "End", "Duration", "Room", "Staff", "Weeks", "Planned Size"].
        # it just so happens that I used "Planned Size" to search for <td>'s.
        # This yields a list of <td>. The parent of each is a <tr>, and the parent of that is the activity <table> itself

        activities_list = list()

        activities_tables = [td.parent.parent for td in soup.find_all("td", text="Planned Size")]

        for table in activities_tables:

            # ----------------------------------- #
            # --- Getting The Day Of The Week --- #
            # ----------------------------------- #

            # the day of the week is contained within a <p> element which is a sibling of the activity table.
            # within the <p> is a <span>; the textContent of this is the name of the day of the week.
            
            day_of_the_week = None

            for sibling in table.previous_siblings:
                if sibling.name == "p":
                    day_of_the_week = sibling.span.string
                    break

            # ----------------------------------- #
            # --- Scraping The Activites Data --- #
            # ----------------------------------- #

            trs = table.find_all("tr", recursive=False)

            # the first <tr> is the attributes of the table, which are as below
            # ignore this <tr> - no point in iterating over it
            ATTRIBUTES = ["Activity", "Description", "Module", "Start", "End", "Duration", "Room", "Staff", "Weeks", "Planned Size"]

            for tr in trs[1:]:

                # the <td>'s within the <tr>
                tds = tr.find_all("td", recursive=False)
                td_values = [td.string for td in tds] # the text content of each <td>

                handle_empty = lambda string: "" if (string == "\xa0") else string
                pad_time     = lambda time: "0"+time if (len(time)==4) else time

                # just a string. E.g. "COMP2271/PRAC/001"
                activity = td_values[ATTRIBUTES.index("Activity")]
                
                # the name of the attribute is "Description", but really it's just the module name as a string
                # e.g. "Programming Paradigms"
                description = td_values[ATTRIBUTES.index("Description")]

                # this is the module code
                module = td_values[ATTRIBUTES.index("Module")]

                # "Start" and "End" are strings of 24h time formats (e.g. '9:00').
                # NB: if the time is earlier than '10:00', the time doesn't begin with '0'.
                # I.e. it'd be '9:00' rather than '09:00'. The `pad_time` anonymous function mitigates this
                raw_start = td_values[ATTRIBUTES.index("Start")]
                raw_end = td_values[ATTRIBUTES.index("End")]
                start = pad_time(raw_start)
                end = pad_time(raw_end)

                # this is a string, and represents the duration as hours and minutes (e.g. '2:00')
                duration = td_values[ATTRIBUTES.index("Duration")]

                # !! "Room" is sometimes empty !!
                # is a room code e.g. "D/RH025"
                room_raw = td_values[ATTRIBUTES.index("Room")]
                room = handle_empty(room_raw)

                # !! "Staff" is sometimes empty !!
                # is a string. Can be a comma-separated (string) list of professor names
                staff_raw = td_values[ATTRIBUTES.index("Staff")]
                staff = handle_empty(staff_raw)
                # staff_list = staff_raw.split(",")

                # ---------------------------------------------------------------- #
                # --- Calculating every day on which this activity takes place --- #
                # ---------------------------------------------------------------- #

                # e.g. "13-21, 26-35, 41-42"
                weeks_raw = td_values[ATTRIBUTES.index("Weeks")] # str

                # will be filled with yyyy-mm-dd strings denoting dates on which the activity will take place
                all_activity_dates = []

                for value in weeks_raw.split(", "):

                    # `value`` will either be a single number-like string (e.g. "42") representing a week number,
                    # or it'll be something like "12-13" (i.e. the span of weeks in which it takes place).

                    if "-" in value: # if it's a span
                        lower, upper = value.split("-")

                        # e.g. if value is "41-44", this'd be ["41", "42", "43", "44"]
                        all_week_numbers = [str(num) for num in range(int(lower), int(upper)+1)]

                        for week in all_week_numbers:
                            week_activity_date = Scraper.get_datetime_date_from_week_number_and_dotw(week, day_of_the_week)
                            all_activity_dates.append(week_activity_date.isoformat())
                
                    else: # it's a singular week
                        week_activity_date = Scraper.get_datetime_date_from_week_number_and_dotw(value, day_of_the_week)
                        all_activity_dates.append(week_activity_date.isoformat())

                # !! "Planned Size" is sometimes empty !!
                # numeric string denoting the capacity of the room e.g. "50"
                planned_size_raw = td_values[ATTRIBUTES.index("Planned Size")]
                planned_size = handle_empty(planned_size_raw)

                # ------------------------------------------ #
                # --- Creating The Final Activities Dict --- #
                # ------------------------------------------ #

                activity_dict = {
                    "Day Of The Week": day_of_the_week,
                    "Activity":        activity,
                    "Description":     description,
                    "Module":          module,
                    "Start":           start,
                    "End":             end,
                    "Duration":        duration,
                    "Room":            room,
                    "Staff":           staff,
                    # "Weeks":           weeks_raw, # weeks
                    "Dates":           all_activity_dates,
                    "Planned Size":    planned_size
                }

                activities_list.append(activity_dict)

                if print_activities:
                    pp.pprint(activity_dict)
                    print()

            if print_activities:
                print("*"*50 + "\n")

        return activities_list

    # ----------

    def get_building_codes(self) -> dict[str, str]:
        '''
        Scrapes the building codes from "https://www.dur.ac.uk/cis/local/facilities/location/?location_id=1" and returns them in a `dict`.

        The keys of the `dict` are `str`s representing the building codes; the values are `str`s representing the full name of the building.

        NB: there are buildings with multiple codes, e.g. `"Rowan House"`.

        ---

        Example return value:
        ```python
        {   
            'BL': 'Biological and Biomedical Sciences',
            'BUSC': 'Business School',
            'CG': 'Chemistry (inc. Courtyard)',
            'CL': '38-39 North Bailey (Classics)',
            'CLC': 'Calman Learning Centre',
            'CM': 'Computing and Maths',
            'D': 'Dawson',
            'E': 'Engineering',
            'ED': 'School of Education',
            'EDBU': 'Burdon House',
            'EDCA': 'Caedmon Building - School of Education',
            'EDU': 'Hild Bede',
            'EH': 'Elvet Hill House',
            'ER1': 'Elvet Riverside 1',
            'ER2': 'Elvet Riverside 2',
            'ERA': 'Elvet Riverside 1',
            'ES': 'E-Science',
            'FONTEYN': 'Dunelm House',
            'GRYHOLG': 'Grey College Holgate House',
            'HS': '43 North Bailey (History)',
            'Hawthorn': 'Mountjoy Centre',
            'Holly': 'Mountjoy Centre',
            'IM': 'Al-Qasimi',
            'L': 'Psychology',
            'MCS': 'Maths & Computer Science',
            'MU': 'Divinity House (Music)',
            'Maple': 'Mountjoy Centre',
            'OE': 'Old Elvet (Sociology)',
            'PC': 'Palatine Centre',
            'PH': 'Physics',
            'PO': '48 Old Elvet',
            'RH': 'Rowan House',
            'Rowan': 'Rowan House',
            'SE': 'Southend House',
            'TH': 'Abbey House (Theology)',
            'TLC': 'Teaching and Learning Centre',
            'W': 'West (Geography)'
        }
        ```
        '''

        URL = "https://www.dur.ac.uk/cis/local/facilities/location/?location_id=1"

        html_response = self.handle_request(URL)
        soup = BeautifulSoup(html_response, "html.parser")

        # the table containing the building codes and the buildings to which they correspond
        # each <tr> has two <td>'s
        # the first/left one is the building code
        # the second/right one is the full name of the building
        table = soup.select("#content263136")[0].table
        
        building_code_dict = dict()

        trs = table.find_all("tr")
        for tr in trs[1:]:
            
            building_code_td, building_name_td = tr.find_all("td")

            building_code = building_code_td.strong.string.strip()
            building_name = building_name_td.string.strip()

            if not ", " in building_code:
                building_code_dict[building_code] = building_name

            # some buildings have multiple building codes, namely Elvet Riverside 1 and Rowan House
            # in the table, their codes are "ER1, ERA" and "RH, Rowan" respectively
            else:
                # print(building_code, building_name)
                for code in building_code.split(", "):
                    building_code_dict[code] = building_name
        
        # pp.pprint(building_code_dict)
        return building_code_dict

    # ----------

    def get_building_locations_urls(self, building_name:str = None) -> 'str|dict[str,str]':
        '''
        Returns the Google Maps url of the location of the building(s) as per the link in the sidebar of https://www.dur.ac.uk/cis/local/facilities/location/?location_id=1.
        
        If a `building_name` is provided, assuming it's valid, a `str` url will be returned.

        If `building_name` is not specified, a `dict` will be returned.
        Each key will be a `str` representing the name of a building, and the value will be a `str` of the Google Maps url.

        In practice, this will probably be called after calling `self.get_building_codes`, so the `building_name` parameter will come from there.

        ---

        Example return value where `building_name` is `"Maths & Computer Science"`:
        ```python
        "https://goo.gl/maps/aAMaHNvBYK5SS9q49"
        ```

        ---

        Example return value where `building_name` is not specified:
        ```python
        {   
            '38-39 North Bailey (Classics)': 'https://goo.gl/maps/ao4mA3JYUCxHQmpa6',
            '43 North Bailey (History)': 'https://goo.gl/maps/xVSVJ94bZz2v8bJCA',
            '48 Old Elvet': 'https://goo.gl/maps/tEZCMAiSXiJnU95GA',
            'Abbey House (Theology)': 'https://goo.gl/maps/i5BRrRDGB3X79Fsn7',
            'Al-Qasimi': 'https://goo.gl/maps/FuuDiFJRrSc1Xbi66',
            'Biological and Biomedical Sciences': 'https://goo.gl/maps/e79atdSuoFx6Fv35A',
            'Burdon House': 'https://goo.gl/maps/fzToLUiavQLxd2kQ9',
            'Business School': 'https://goo.gl/maps/m7heaycvC6o7Fa8Z7',
            'Caedmon Building - School of Education': 'https://goo.gl/maps/KFo1t5f8Kbbdir4AA',
            'Calman Learning Centre': 'https://goo.gl/maps/XjjdJR78ZbmqtZgL7',
            'Chemistry (inc. Courtyard)': 'https://goo.gl/maps/mgHhgft7h5vap4Hy7',
            'Computing and Maths': 'https://goo.gl/maps/TUhw8NMzXurHRMBr8',
            'Dawson': 'https://goo.gl/maps/sM7LT1i34jGDUkZG6',
            'Divinity House (Music)': 'https://goo.gl/maps/fromD6CLyMhYgLSS6',
            'Dunelm House': 'https://goo.gl/maps/H9vTFDRUJJpSmDhEA',
            'E-Science': 'https://goo.gl/maps/EUApsrGatmC8Kdww6',
            'Elvet Hill House': 'https://goo.gl/maps/K1kpSpcp9ZZpmvEAA',
            'Elvet Riverside 1': 'https://goo.gl/maps/JaVz9z9jnE7xdVeK8',
            'Elvet Riverside 2': 'https://goo.gl/maps/UH8Bbn8i14rYF6ko7',
            'Engineering': 'https://goo.gl/maps/ihDnAFZQ1Bs31PKG7',
            'Grey College Holgate House': 'https://goo.gl/maps/RNk623VHkqj51CZy6',
            'Hild Bede': 'https://goo.gl/maps/bZr78Dob2faKwuAu8',
            'Maths & Computer Science': 'https://goo.gl/maps/aAMaHNvBYK5SS9q49',
            'Mountjoy Centre': 'https://goo.gl/maps/9aEjpHXiLdXVQDvL7',
            'Old Elvet (Sociology)': 'https://goo.gl/maps/NwH8XqjNzso1TW6YA',
            'Palatine Centre': 'https://goo.gl/maps/edXnj7rzf2zYTnJK9',
            'Physics': 'https://goo.gl/maps/Gy9meAMkvE4GQfVB9',
            'Psychology': 'https://goo.gl/maps/AnTL6Ubm175QiTew6',
            'Rowan House': 'https://goo.gl/maps/9PRKA3u5xRcMooe8A',
            'School of Education': 'https://goo.gl/maps/zDBLgvo5TzN1fULU7',
            'Southend House': 'https://goo.gl/maps/bgXNQvV8332rWupH8',
            'Teaching and Learning Centre': 'https://goo.gl/maps/zz6HUFT7nCUoByCx8',
            'West (Geography)': 'https://goo.gl/maps/rvuY4yuo1tQBjUSa6'
        }
        ```
        '''

        URL = "https://www.dur.ac.uk/cis/local/facilities/location/?location_id=1"

        html_response = self.handle_request(URL)
        soup = BeautifulSoup(html_response, "html.parser")
        
        # the <div> containing the links
        # https://www.dur.ac.uk/cis/local/facilities/location/?location_id=1#content257296
        google_maps_links_div = soup.select("#content257296")[0]

        # keys are the names in the facility location page, values are the names in the self.get_building_codes() dict
        mappings = {
            '32 Old Elvet (Sociology)': None,
            '38-39 Old Bailey (Classics)': '38-39 North Bailey (Classics)',
            '43 Old Bailey (History)': '43 North Bailey (History)',
            '48 Old Elvet':'48 Old Elvet',
            'Abbey House (Theology)':'Abbey House (Theology)',
            'Al-Qasimi Building':'Al-Qasimi',
            'Bill Bryson Library':None,
            'Biological Sciences':'Biological and Biomedical Sciences',
            'Burdon House':'Burdon House',
            'Business School':'Business School',
            'Caedmon Building':    'Caedmon Building - School of Education',
            'Calman Learning Centre':    'Calman Learning Centre',
            'Chemistry':    'Chemistry (inc. Courtyard)',
            'Computing/Maths':    'Computing and Maths',
            'Courtyard Building':    'Dawson',
            'Dawson Building':    'Divinity House (Music)',
            'Divinity House (Music)': None,
            'Dunelm House (Student Union)':   'Dunelm House',
            'E-Sciences':     'E-Science',
            'Elvet Hill House':    'Elvet Hill House',
            'Elvet Riverside 2':    'Elvet Riverside 2',
            'Elvet Riverside1':     'Elvet Riverside 1',
            'Engineering':    'Engineering',
            'Greys College - Holgate':    'Grey College Holgate House',
            'Hild Bede College':    'Hild Bede',
                'Maths & Computer Science':    'Maths & Computer Science', # ---- this wasn't in self.get_building_codes().values()
            'Mountjoy Centre':    'Mountjoy Centre',
            'Mountjoy Centre - Rowan House':    'Rowan House',
            'Palace Green': None,
            'Palatine Centre':    'Palatine Centre',
            'Physics':    'Physics',
            'Psychology':    'Psychology',
            'School of Education':    'School of Education',
            'Science of Education Building': None,
            'Southend House':    'Southend House',
            'Teaching and Learning Centre':    'Teaching and Learning Centre',
            'West Building (Geography)': 'West (Geography)'
        }

        all_urls = dict()
        for a in google_maps_links_div.find_all("a"):

            # the name of the building inside the <a> tag
            bname = a.string.strip()

            # the value of the "href" attribute
            url = a["href"].strip()

            if not mappings[bname] is None:
                all_urls[mappings[bname]] = url

        # manually added:
        all_urls["Maths & Computer Science"] = "https://goo.gl/maps/aAMaHNvBYK5SS9q49"
        all_urls['Old Elvet (Sociology)'] = "https://goo.gl/maps/NwH8XqjNzso1TW6YA"

        if building_name is None:
            return all_urls
        
        else:
            return all_urls[building_name]

    # ----------

    def get_building_codes_and_location_urls(self, code_param:str = None) -> dict[str,str]:

        codes = self.get_building_codes()
        urls = self.get_building_locations_urls()

        codes_and_urls = {}
        for code, building_name in codes.items():
            codes_and_urls[code] = urls[building_name]

        if code_param:
            if code_param in codes_and_urls.keys():
                return codes_and_urls[code_param]
            else:
                return ""
        
        else:
            return codes_and_urls
    
    # ----------

    

if __name__ == "__main__":
    load_environment_variables()
    scraper = Scraper(
        os.environ.get("APP_SCRAPER_USERNAME"),
        os.environ.get("APP_SCRAPER_PASSWORD")
    )
    
    pp.pprint(
        scraper.get_week_patterns()
    )

# ----------------------------------- #
# --- Getting The Day Of The Week --- #
# ----------------------------------- #
