import icalendar

class Timetable:
    ''' Given a list of module codes, constructs a timetable. '''

    def __init__(self, username: str, password: str, module_codes:list[str]) -> None:
        self.username = username
        self.password = password
        self.modules = module_codes

    def module_timetable_to_ics(self, module_code:str):
        from pprint import PrettyPrinter
        pp = PrettyPrinter(indent=4)

        from scraper import Scraper
        scraper = Scraper(self.username, self.password)

        # list of activities for the given module_code
        module_timetable = scraper.get_module_timetable([module_code])

        pp.pprint(module_timetable)

# print(*dir(icalendar.Calendar), sep="\n")