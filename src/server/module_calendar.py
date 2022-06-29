import os
import json
import re
import datetime
import copy
from pprint import PrettyPrinter

import icalendar
# from yaml import DocumentStartEvent # 4.0.9

from env import load_environment_variables, auth
from scraper import Scraper

pp = PrettyPrinter(indent=4)

class ModuleCalendar:
    '''
    Hi

    ---

    ### Reference:
    - https://www.kanzaki.com/docs/ical/
    '''

    def __init__(self, username:'str', password:'str') -> 'None':
        self.username = username
        self.password = password

        self.scraper = Scraper(self.username, self.password)
    
    # ----------

    @staticmethod
    def display_ical(cal:'icalendar.Calendar', _print:'bool' = False) -> 'None':
        converted = cal.to_ical().decode('ascii').replace('\r\n', '\n').strip()
        if _print:
            print(converted)
        else:
            return converted

    # ----------
    
    @staticmethod
    def format_description(activity_dict:'dict') -> 'str':
        ''' Adapts the values in `activity_dict` and returns a `str` to be used in the `description` of each `VEVENT` component in the main `VCALENDAR`. '''

        # makes the passed-in string bold. Can be a single word or a sentence
        boldify = lambda x: '\033[1m' + x + '\033[0m'

        def reverse_date(date_str:'str') -> 'str':
            '''
            Reverses the order of a date string to make it more readable for humans.

            e.g. converts `"2017/03/08"` to `"08/03/2017"`.
            '''
            return "/".join(date_str.split("-")[::-1])

        activity     = activity_dict["Activity"]
        module       = f'{activity_dict["Module"]} - {activity_dict["Description"]}'
        room         = activity_dict["Room"]
        staff        = activity_dict["Staff"] if (len(activity_dict["Staff"]) != 0) else "(Info not available)"
        dates        = "\n".join([reverse_date(date_str) for date_str in activity_dict["Dates"]])
        planned_size = activity_dict["Planned Size"]

        # description = "\n".join([
        #     "*** Activity ***",
        #     activity     + "\n",
        #     "*** Module ***",
        #     module       + "\n",
        #     "*** Room ***",
        #     room         + "\n",
        #     "*** All Event Dates ***",
        #     dates        + "\n",
        #     "*** Staff ***",
        #     staff        + "\n",
        #     "*** Planned Size ***",
        #     planned_size
        # ])

        description = "\n".join([
            "*** Activity ***",
            activity     + "\n",
            "*** Module ***",
            module       + "\n",
            "*** Room ***",
            room         + "\n",
            "*** All Event Dates ***",
            dates        + "\n",
            "*** Staff ***",
            staff        + "\n",
            "*** Planned Size ***",
            planned_size
        ])

        return description

    # ----------

    @staticmethod
    def combine_date_and_time(activity_dict:'dict', date:'str', start_or_end:'str') -> 'datetime.datetime':
        return datetime.datetime.combine(
            date = datetime.date.fromisoformat(date),
            time = datetime.time.fromisoformat(activity_dict[start_or_end]),
            tzinfo = datetime.timezone.utc
        )

    # ----------

    def get_location(self, activity:'dict', building_codes_and_names:'dict', building_location_urls:'dict') -> 'str':
        '''
        ---

        ### Reference:
        - https://stackoverflow.com/questions/54330631/un-shorten-a-goo-gl-maps-link-to-coordinates
        '''
        room = activity["Room"]
        building_code = self.scraper.get_building_code_from_room_string(list(building_codes_and_names.keys()), room)
        if building_code is not None:

            # the full name of the building e.g. "Teaching and Learning Centre"
            building_name = building_codes_and_names[building_code]

            # google maps url of the building
            building_location = building_location_urls[building_name]

            return building_location
        else:
            return ""

    # ----------

    @staticmethod
    def write_cal_to_file(cal: "icalendar.Calendar") -> 'None':
        # try:
        # with open("~/Downloads/cal.ics", "wb") as f:
        with open("cal.ics", "wb") as f:
            f.write(cal.to_ical())
        # except:
        #     print("Failed")

    # ----------

    @staticmethod
    def get_repeating_pattern(dates:'list[str]') -> 'datetime.timedelta':
        '''
        Given `dates`, figures out the pattern by which the dates repeat, and returns it.
        
        Generally, it appears that the events occur once every 7 days, with gaps of 35 and 42 days denoting the gaps between the Michaelmas/Epiphany and Epiphany/Easter terms.
        Although there are exceptions to this.
        '''

        # There obviously can't be a pattern if the event only occurs on one date
        if len(dates) == 1:
            return [{"partition dates": dates, "params": None}]

        int_split = lambda date_str: [int(x) for x in date_str.split("-")]
        str_to_datetime_date = lambda date_str: datetime.date(*int_split(date_str))
        
        dates2 = copy.deepcopy(dates)
        dates2.sort()

        # The differences between each pair of dates.
        # Therefore len(diffs) == len(dates)-1
        diffs = list()
        diffs_and_dates = list()

        # The below `while` loop calculates the difference between each pair of dates in `dates2`.
        # It extracts the number of days as an `int`.
        lower = 0
        upper = 1
        while upper < len(dates2):

            lower_date_str = dates2[lower]
            upper_date_str = dates2[upper]

            lower_date = datetime.date(*int_split(lower_date_str))
            upper_date = datetime.date(*int_split(upper_date_str))

            diff = upper_date - lower_date # timedelta
            diffs.append(diff.days)

            diffs_and_dates.append([diff.days, dates2[lower], dates2[upper]])

            lower += 1
            upper += 1

        # The below nested `while` loop essentially finds the repeating differences in days and puts them into a sub-list.
        # Basically it finds the "substrings" which repeat the same number consecutively.
        # So essentially `diffs` but where consecutive differences of the same length are put together in sub-lists.
        # e.g:
        #   [ 7, 7, 7, 7, 7, 7, 7, 7,   35,   7, 7, 7, 7, 7, 7, 7, 7, 7,   42,   7 ]
        #       becomes 
        #   [[7, 7, 7, 7, 7, 7, 7, 7], [35], [7, 7, 7, 7, 7, 7, 7, 7, 7], [42], [7]]

        partitioned_diffs = []

        index = 0
        while index < len(diffs):

            # The current value for the difference in days between two dates.
            current_diff = diffs[index]

            # The total number of consecutive repeating difference values that are equal to `current_diff`.
            consecutive = 1

            # While `current_diff` is equal to the next diff, increment the index and the `consecutive` count.
            while (index+1 < len(diffs)) and (current_diff == diffs[index+1]):
                index += 1
                consecutive += 1
            
            # Append a sub-list of length `consecutive` where every element is the value `current_diff` to `partitioned_diffs`.
            sublist = consecutive * [current_diff]
            partitioned_diffs.append(sublist)

            index += 1

        # Now we iterate through `partitioned_diffs`.
        # We convert each sub-list into an object, where the key is the stringified first date, and the value is a dict containing the data

        # print(dates)
        # print(diffs)
        # print(partitioned_diffs)
        # pp.pprint(diffs_and_dates)
        
        event_params = []

        index_of_first_date = 0
        for i, partition in enumerate(partitioned_diffs):
            
            interval, partition_first_date, _ = diffs_and_dates[index_of_first_date]

            # The last date in the span of the `partition`.
            partition_last_date = dates[index_of_first_date + (len(partition))]

            # The number of days between the first date and the last date,
            # and the sum of the differences in `partition`, are the same.
            #   print((str_to_datetime_date(partition_last_date) - str_to_datetime_date(partition_first_date)).days == sum(partition))

            # All of the dates in `dates` corresponding to the current `partition`.
            partition_dates = dates[ dates.index(partition_first_date) : dates.index(partition_last_date)+1 ]
            # print(partition_dates)

            obj = {
                "partition dates": partition_dates,
                "params": {
                    "COUNT": str(len(partition_dates)),
                    "INTERVAL": str(interval),
                    # "FREQ": "DAILY"
                }
            }

            event_params.append(obj)

            index_of_first_date += len(partition)
        
        # print()
        
        return event_params

    # ----------

    def get_geo(self, activity:'dict', building_codes_and_names:'dict', building_location_urls:'dict') -> 'str':
        
        location = self.get_location(activity, building_codes_and_names, building_location_urls)

        if "https://www.google.co" in location:

            # we can extract the latitude and longitude
            # this can be added the event via the "geo" attribute

            # e.g. in the url it'll say something like "@54.767954,-1.5728849"
            # "(-*\d+(\.\d+))" matches a latitude or longitude coordinate
            overall_regex = r"@(-*\d+(\.\d+)),(-*\d+(\.\d+))"

            match = re.search(overall_regex, location)
            if match:
                # match[0][1:] is the string of the match without the '@' at the start
                # the latitude and longitude are separated by a comma
                latitude, longitude = match[0][1:].split(",")

                # https://kanzaki.com/docs/ical/geo.html says latitude and longitude must be separated by a ';'
                return latitude + ";" + longitude
        
        else:
            return ""

    # ----------

    def create_ics_file_from_module_codes(self, module_codes:'list[str]' = []) -> 'str':
        '''
        Returns an iCalendar `.ics` file as a string
        
        ---

        ### References:

        - iCal `summary` attribute --> https://www.kanzaki.com/docs/ical/summary.html
        - iCal `organizer` attribute --> https://www.kanzaki.com/docs/ical/organizer.html
        - iCal `description` attribute --> https://www.kanzaki.com/docs/ical/description.html
        - iCal `dtstart` attribute --> https://www.kanzaki.com/docs/ical/dtstart.html
        - iCal `dtend` attribute --> https://www.kanzaki.com/docs/ical/dtend.html
        - iCal `location` attribute --> https://www.kanzaki.com/docs/ical/location.html
        - iCal `geo` attribute --> https://www.kanzaki.com/docs/ical/geo.html
        '''

        to_datetime = lambda date, time: datetime.datetime.combine(date = datetime.date.fromisoformat(date), time = datetime.time.fromisoformat(time), tzinfo = datetime.timezone.utc)

        # used to get the google maps url for each activity.
        # i've defined these at the top of the function so that they don't have to be repeatedly called.
        # saves having to request multiple times from the internet.
        building_codes_and_names = self.scraper.get_building_codes()
        building_location_urls = self.scraper.get_building_locations_urls()

        if len(module_codes) == 0:
            return ""
        
        # List containing all the activities to be added to the calendar.
        schedule_info = self.scraper.get_module_timetable(module_codes,"list")

        # The overall VCALENDAR component.
        cal = icalendar.Calendar()

        for activity in schedule_info:

            summary = activity["Activity"]
            organizer = activity["Staff"]
            # dtstart = ModuleCalendar.combine_date_and_time(activity, activity["Dates"][0], "Start")
            # dtend = ModuleCalendar.combine_date_and_time(activity, activity["Dates"][0], "End")
            description = ModuleCalendar.format_description(activity)
            location = self.get_location(activity, building_codes_and_names, building_location_urls)
            geo = self.get_geo(activity, building_codes_and_names, building_location_urls)

            # Basically turns all the dates on which the current `activity` occurs
            # into a series of repeating events. This will reduce the number of events 
            # created overall, and should hopefully help link events together so that
            # editing one event applies the same change to the rest of the related events.

            rrule_dicts = ModuleCalendar.get_repeating_pattern(activity["Dates"])

            # print(summary)
            # print(geo)
            # print(activity["Dates"])

            for rrule_dict in rrule_dicts:

                vevent = icalendar.Event()

                dtstart = to_datetime(rrule_dict["partition dates"][0], activity["Start"])
                dtend   = to_datetime(rrule_dict["partition dates"][0], activity["End"])

                vevent.add("summary",     summary)
                vevent.add("organizer",   organizer)
                vevent.add("description", description)
                vevent.add("location",    location)
                vevent.add("dtstart",     dtstart)
                vevent.add("dtend",       dtend)

                # If a latitude and longitude can be found for the location of this particular activity.
                if geo:
                    vevent.add("geo", geo)

                if rrule_dict["params"] is not None:
                    # An RRULE should be added to the VEVENT.

                    interval = rrule_dict["params"]["INTERVAL"]
                    count    = rrule_dict["params"]["COUNT"]
                    
                    vevent.add("rrule", {"freq":"daily", "interval":interval, "count":count})

                cal.add_component(vevent)

                # pp.pprint(rrule_dict)

            # print()

        ModuleCalendar.display_ical(cal,_print=True)
        ModuleCalendar.write_cal_to_file(cal)

    # def create_ics_file_from_module_codes2(self, module_codes:'list[str]' = []) -> 'str':
    """
    def create_ics_file_from_module_codes2(self, module_codes:'list[str]' = []) -> 'str':
        '''
        Returns an iCalendar `.ics` file as a string
        
        ---

        ### References:

        - iCal `summary` attribute --> https://www.kanzaki.com/docs/ical/summary.html
        - iCal `organizer` attribute --> https://www.kanzaki.com/docs/ical/organizer.html
        - iCal `description` attribute --> https://www.kanzaki.com/docs/ical/description.html
        - iCal `dtstart` attribute --> https://www.kanzaki.com/docs/ical/dtstart.html
        - iCal `dtend` attribute --> https://www.kanzaki.com/docs/ical/dtend.html
        - iCal `location` attribute --> https://www.kanzaki.com/docs/ical/location.html
        - iCal `geo` attribute --> https://www.kanzaki.com/docs/ical/geo.html
        '''

        # Used to get the google maps url for each activity.
        # I've defined these at the top of the function so that they don't have to be repeatedly called.
        # Saves having to request multiple times from the internet.
        building_codes_and_names = self.scraper.get_building_codes()
        building_location_urls = self.scraper.get_building_locations_urls()

        if len(module_codes) == 0:
            return ""
        
        # `list` containing all the activities to be added to the calendar
        schedule_info = self.scraper.get_module_timetable(module_codes,"list")

        cal = icalendar.Calendar()

        for activity in schedule_info:

            # the VEVENT component
            event = icalendar.Event()

            event.add("summary", activity["Activity"])
            event.add("organizer", activity["Staff"])

            description = ModuleCalendar.format_description(activity)
            event.add("description", description)

            # --------------------------------------------------------------- #
            # --- Get the start and end datetime.datetimes of the activity --- #
            # --------------------------------------------------------------- #

            all_dates = sorted(activity["Dates"])

            first_date = all_dates[0]
            del all_dates[0]

            # both `start` and `end` are datetime.datetime objects
            start = ModuleCalendar.combine_date_and_time(activity, first_date, "Start")
            event.add("dtstart", start)

            end = ModuleCalendar.combine_date_and_time(activity, first_date, "End")
            event.add("dtend", end)

            # specify dates to repeat this event on
            if len(all_dates) != 0:

                converted_dates = []
                for date in all_dates:
                    year, month, day = date.split("-")
                    converted_date = datetime.date(int(year),int(month),int(day))
                    # converted_date = datetime.datetime.combine(
                    #     date = datetime.date(int(year),int(month),int(day)),
                    #     time = start.time(),
                    #     tzinfo = datetime.timezone.utc
                    # )
                    # print(repr(converted_date))
                    converted_dates.append(converted_date)
                event.add("rdate", converted_dates, parameters = {"VALUE": "DATE"})

                # all_dates = ",".join([date_str.replace("-","") for date_str in all_dates])
                # event.add("rdate", all_dates, parameters = {"VALUE": "DATE"})
                # print("all_dates", all_dates)
                # event.add("rdate", all_dates, parameters = {"value": "date"})

            # -------------------------------------------------------- #
            # --- (Try to) get the google maps URL of the building --- #
            # -------------------------------------------------------- #

            location = self.get_location(activity, building_codes_and_names, building_location_urls)
            event.add("location", location)

            # ---------------------------------------------------------------- #
            # --- (Try to) get latitude and longitude from google maps url --- #
            # ---------------------------------------------------------------- #

            # if the url is shortened, it'll be something like "https://goo.gl/maps/..."
            # however if it's unshortened, it'll look something like "https://www.google.co.uk/maps/..."

            if "https://www.google.co" in location:

                # we can extract the latitude and longitude
                # this can be added the event via the "geo" attribute

                # e.g. in the url it'll say something like "@54.767954,-1.5728849"
                # "(-*\d+(\.\d+))" matches a latitude or longitude coordinate
                overall_regex = r"@(-*\d+(\.\d+)),(-*\d+(\.\d+))"

                match = re.search(overall_regex, location)
                if match:
                    # match[0][1:] gets you the string of the match without the '@' at the start
                    # the latitude and longitude are separated by a comma
                    latitude, longitude = match[0][1:].split(",")

                    # https://kanzaki.com/docs/ical/geo.html says latitude and longitude must be separated by a ';'
                    geo = latitude + ";" + longitude

                    event.add("geo", geo)

            print(activity["Activity"])
            pp.pprint(
                ModuleCalendar.get_repeating_pattern(activity["Dates"])
            )
            print()

            cal.add_component(event)

            # break
            
            # pp.pprint(activity)
            # print()

        # print(cal)
        ModuleCalendar.write_cal_to_file(cal)
        # ModuleCalendar.display_ical(cal,True)
        # return cal.to_ical()
    """

    # ----------

    def ics_from_term_dates(self):

        term_dates = self.scraper.get_term_dates()

        cal = icalendar.Calendar()

        for term, dates in term_dates.items():

            for index, date in enumerate(dates):

                event = icalendar.Event()

                # The first date in `dates` signals the beginning date of the span of time.
                # The second date in signals the end date.
                summary_prefix = "Beginning of " if index == 0 else "End of "

                event.add("summary", summary_prefix + term)

                # According to this: https://stackoverflow.com/a/30249034
                # If you add a DTSTART to a VEVENT and don't include a DTEND, it turns it into an all-day event.
                event.add("dtstart", date)

                cal.add_component(event)

            # event = icalendar.Event()
            # event.add("summary", term)
            # event.add("dtstart", dates[0])
            # event.add("dtend", dates[1])
            # cal.add_component(event)
        
        # print(cal)
        
        ModuleCalendar.display_ical(cal, _print=True)
        ModuleCalendar.write_cal_to_file(cal)

if __name__ == "__main__":
    load_environment_variables()
    mtc = ModuleCalendar(*auth())
    pass

# https://youtu.be/XPeU-Eyo9kw?t=2648
