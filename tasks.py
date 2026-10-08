import json
import os

from datetime import date
from Browser.utils.data_types import SelectAttribute


from robocorp.tasks import task
from RPA.Browser.Playwright import Playwright

from bs4 import BeautifulSoup

JSON_DIR="output/dates.json"

class scrape_calendar:

    def __init__(self):
        self.browser=Playwright() #type: ignore
        self.month=0
        self.year=0
        self.BeautifulSoup=BeautifulSoup()
        self.parsedElement=None
        
        
    def navigate(self):
        """Navigation for the calendar page"""
        self.browser.new_browser(headless=False,slowMo=0.5)
        self.browser.new_context()
        self.browser.new_page("https://nepalipatro.com.np/calendar/")
       
        
    def set_presentdate(self):
        """Set to present date"""
        today=date.today()
        self.month=today.month
        self.year=today.year
           
    
    def conversion_ad(self):
        """Converting calendar into BS format"""
        self.browser.click("#main-content > div > div > div.col-lg-9 > div:nth-child(1) > div.full-cal-height.bg-light.mb-4.d-none.d-sm-none.d-md-none.d-lg-block.d-xl-block.d-xxl-block > header > div.mail-tools.tooltip-demo.m-t-md > div.header-button > div.btn-group.dropdown.mb-2.mx-1 > button")
        self.browser.click('ul.dropdown-menu > li.dropdown-item:has-text("ई.सं.") >> nth=1')
        
        
    def browse_bfryr(self):
        """Browse calendar to starting date of data"""
        self.browser.click("#main-content > div > div > div.col-lg-9 > div:nth-child(1) > div.full-cal-height.bg-light.mb-4.d-none.d-sm-none.d-md-none.d-lg-block.d-xl-block.d-xxl-block > header > div.mail-tools.tooltip-demo.m-t-md > div.header-button > div:nth-child(3) > button")
        self.browser.select_options_by("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > select",SelectAttribute.value,"BS")
        starting_year=2082 #fixing the data year from 2082
        self.browser.fill_text("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > div > div:nth-child(1) > input",str(starting_year) )       
        self.browser.select_options_by("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > div > div:nth-child(2) > select",SelectAttribute.value,"0")
        self.browser.click("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > button.btn.btn-default.float-end.btn-lg.modal-button")
       
     
    def get_cdDate(self):
        """Get AD Date and BS Date of the running calendar"""
        element=self.browser.get_elements('#main-content > div > div > div.col-lg-9 > div:nth-child(1) > div.full-cal-height.bg-light.mb-4.d-none.d-sm-none.d-md-none.d-lg-block.d-xl-block.d-xxl-block > div.calendar > div.rows.flex-nowrap > div.col.cell:is(.color-normal, .np-holiday) > div[id^="date-"]')
        result={}
        print(len(element))
        for e in element:
            html=self.browser.get_property(e,"outerHTML")
            div=BeautifulSoup(html, "html.parser").find("div")
            if div is None:
                continue
            NP_Date=str(div.get("id","")).replace("date-", "")
            # NP_Raw=str(div.get("data-np-date",""))
            # NP_Date="-".join(reversed(NP_Raw.split('.')))
            EN_Raw=div.find("time", class_="date-value")
            EN_Date=EN_Raw.get("datetime")
            result[EN_Date]=NP_Date
        return result  
    
    def loop_calendar(self):
        """Loop through calendars ranging from starting date to ending date"""
        while True:
            self.browser.click("#main-content > div > div > div.col-lg-9 > div:nth-child(1) > div.full-cal-height.bg-light.mb-4.d-none.d-sm-none.d-md-none.d-lg-block.d-xl-block.d-xxl-block > header > div.mail-tools.tooltip-demo.m-t-md > div.header-button > div:nth-child(3) > button")
            running_year=int(self.browser.get_text("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > div > div:nth-child(1) > input"))
            print(self.browser.get_selected_options("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > div > div:nth-child(2) > select",SelectAttribute.value)[0])
            running_month=int(self.browser.get_selected_options("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > div > div:nth-child(2) > select",SelectAttribute.value)[0])+1
            print(type(running_month))
            self.browser.click("#main-content > div.modal.fade.show.mixed-font-swap > div > div > div > form > button.btn.btn-default.float-end.btn-lg.modal-button")
            
            if(running_year,running_month) > (2099 ,12): #fixing the last extraction date to 2099-12
                break
            
            results=self.get_cdDate()
            self.generate_json(results)
            self.browser.click("#main-content > div > div > div.col-lg-9 > div:nth-child(1) > div.full-cal-height.bg-light.mb-4.d-none.d-sm-none.d-md-none.d-lg-block.d-xl-block.d-xxl-block > header > div.mail-tools.tooltip-demo.m-t-md > div.header-button > div:nth-child(2) > button:nth-child(3)")    
            
    
    def generate_json(self, dates):
        """Generates the json in fixture format with major date of BS to AD mapping in fixture format"""
        data = []
        if os.path.exists(JSON_DIR):
            with open(JSON_DIR, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

        current_pk = len(data) + 1
        existing_eng_dates = {item["fields"]["eng_date"] for item in data}

        for eng_date, nep_date in sorted(dates.items()):
            if eng_date not in existing_eng_dates:
                data.append({
                    "model": "commons.dateconvertermodel",
                    "pk": current_pk,
                    "fields": {
                        "nep_date": nep_date,
                        "eng_date": eng_date
                    }
                })
                current_pk += 1

        os.makedirs(os.path.dirname(JSON_DIR), exist_ok=True)
        
        with open(JSON_DIR, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
                
    def close(self):
        """Close the browser with current context"""
        self.browser.close_browser() 


@task
def map_date():
    """Mapping Operation of from BSs: (2025-04)-(2043-04) to BSs: (2082-01)-(2100-01)"""
    scraper=scrape_calendar()
    
    try:
        scraper.navigate()
        scraper.set_presentdate()
        scraper.browse_bfryr()
        scraper.loop_calendar()
    except Exception as e:
        print(e)
    finally:
        scraper.close()
       
    
        
    
    

        
        


    
    
    
    
    
   