# -*- coding: utf-8 -*-
"""
Idaho Pharmacy Search
"""
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import pandas as pd
import time
import sys
import os

#Set intial web browser and search
def idaho_pharmacy_search(lastname_string):
    url = 'https://idbop.mylicense.com/verification/Search.aspx'
    licensetype_dropdownid = 't_web_lookup__license_type_name'
    lastname_formid = 't_web_lookup__last_name'
    submit_buttonid = 'sch_button'
    browser = webdriver.Firefox()
    type(browser)
    browser.get(url)
    s1 = Select(browser.find_element_by_id(licensetype_dropdownid))
    s1.select_by_visible_text('Pharmacist')
    lastname_fill = browser.find_element_by_id(lastname_formid)
    lastname_fill.send_keys(lastname_string+'*')
    browser.find_element_by_id(submit_buttonid).click()
    time.sleep(2)
    return browser

#Return field values from record page by xpath
def get_details(browser,xpath):
    try:
        return browser.find_element_by_xpath(xpath).text
    except:
        return "none"

#Append Dataframe with field values
def append_details(df,browser,xpaths):
    temp_firstname = get_details(browser,xpaths['xpath_firstname'])
    temp_middlename = get_details(browser,xpaths['xpath_middlename'])
    temp_lastname = get_details(browser,xpaths['xpath_lastname'])
    temp_license = get_details(browser,xpaths['xpath_license'])
    temp_issued = get_details(browser,xpaths['xpath_issued'])
    temp_expiry = get_details(browser,xpaths['xpath_expiry'])
    temp_renewed = get_details(browser,xpaths['xpath_renewed'])
    df = df.append(
                {'firstname' : temp_firstname,
                 'middlename' : temp_middlename,
                 'lastname' : temp_lastname,
                 'license' : temp_license,
                 'issued' : temp_issued,
                 'expiry' : temp_expiry,
                 'renewed' : temp_renewed
                 },
                 ignore_index = True
                 )
    return df

#Main
def main():    
    detailed = pd.DataFrame(columns=['firstname',
                                     'middlename',
                                     'lastname',
                                     'license',
                                     'issued',
                                     'expiry',
                                     'renewed'])
    xpath_dict = {'xpath_firstname' : '//*[@id="_ctl27__ctl1_first_name"]',
                'xpath_middlename' : '//*[@id="_ctl27__ctl1_m_name"]',
                'xpath_lastname' : '//*[@id="_ctl27__ctl1_last_name"]',
                'xpath_license' : '//*[@id="_ctl36__ctl1_license_no"]',
                'xpath_issued' : '//*[@id="_ctl36__ctl1_issue_date"]',
                'xpath_expiry' : '//*[@id="_ctl36__ctl1_expiry"]',
                'xpath_renewed' : '//*[@id="_ctl36__ctl1_last_ren"]'
                }
    #Can take argument for last name search instead of default 'L'
    try:
        if sys.argv[1].isalpha():
            lastname_startswith = sys.argv[1]
        else:
            print('Argument not alphabet characters')
            print('Executing for "L"')
            lastname_startswith = 'L'
    except:
        lastname_startswith = 'L'
    browser = idaho_pharmacy_search(lastname_startswith)
    #iterate through pages of html table
    i = 1
    default_handle = browser.current_window_handle
    while True:
        #print(i)
        df = pd.read_html(browser.page_source)
        if i == 1:
            general = df[4].dropna()
        else:
            general = general.append(df[4].dropna(),ignore_index = True)
        j = 3
        #iterate through each record hyperlink to gather additional field values
        while True:
            try:
                browser.find_element_by_xpath('//*[@id="datagrid_results__ctl{}_name"]'.format(j)).click()
                time.sleep(1)
                browser.switch_to.window(browser.window_handles[1])
                detailed = append_details(detailed,browser,xpath_dict)
                browser.close()
                browser.switch_to_window(default_handle)
                j = j+1
                time.sleep(2)
            except:
                break
        try:
            browser.find_element_by_xpath('/html/body/form/table/tbody/tr[2]/td[2]/table[2]/tbody/tr[3]/td/table/tbody/tr[42]/td/a[{}]'.format(i)).click()
            i = i+1
            time.sleep(2)
        except:
            main = general[general['Name'].str.startswith(lastname_startswith)]
            final = main.merge(detailed, left_on='License #', right_on='license',
                    suffixes=('_main', '_detail'))
            final = final.drop(columns=['Name','license'])
            final = final.rename(columns={'firstname':'First Name',
                          'middlename':'Middle Name',
                          'lastname':'Last Name',
                          'issued':'Original Issued Date',
                          'expiry':'Expiry',
                          'renewed':'Renewed'})
            currentDirectory = os.getcwd()
            path = currentDirectory+'\pharmacy_results2.csv'
            final.to_csv(path,index=False)
            #print(final.head())
            break

if __name__ == "__main__":
    main()
    