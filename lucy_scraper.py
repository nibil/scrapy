from __future__ import unicode_literals
from bs4 import BeautifulSoup
from itertools import izip
from lxml import etree
import requests
import random
import json
import csv
import base64
from scrapers.linkedin import linkedin_fetch

from slacker import Slacker
slack = Slacker('')


cleanup_bs4 = lambda x: x[0].text if x else None


def readData(inputFile=None,outputFile=None):

    ########################
    ## Read Data from CSV ##
    ########################


    f = open(inputFile)
    lines = f.readlines()
    f.close()
    f = open(outputFile,"w")
    count = 0
    writer = csv.DictWriter(f, fieldnames = ["name", "Linkedin", "industry", "location", "title", "languages" , "college1" , "course1", "cperiod1" ,\
                    "college2" , "course2", "cperiod2", "college3" , "course3", "cperiod3", "company1", "designation1", "period1", "company2",\
                    "designation2", "period2", "company3", "designation3", "period3" , "skills"])
    writer.writeheader()
    for lk in lines:
        url = ''
        cc = lk.decode('utf-8').split(",")
        linkedin = []
        try:
            for x in cc:
                if "http" in x:
                    linkedin.append(x)
            url = linkedin[0].replace("\r\n", "")
            proc = linkedin_fetch(url=url)
        except:
            data = ''
        # proc = processData(data)
        if proc:
            experience = skills = education = languages = industry = location = title = name = ''
            name = proc.get('name','')
            experience = proc.get('experience','')
            skills = ",".join(proc.get('skills',''))
            education = proc.get('education','')
            languages =  ",".join(proc.get('languages',''))
            industry = proc.get('industry','')
            loc = proc.get('location','')
            if loc:
                location = loc.encode('ascii', 'ignore')
            tit = proc.get('title','')
            if tit:
                title = tit.encode('ascii', 'ignore')

            college1 = course1 = cperiod1 = college2 = course2 = cperiod2 = college3 = course3 = cperiod3 = company1 = designation1 = period1 = company2 = designation2 = period2 = company3 = designation3 = period3 = " "

            if education:
                try:
                    college1 = education[0].get('institution','').encode('ascii', 'ignore')
                    course1 = education[0].get('course','').encode('ascii', 'ignore')
                    cperiod1 = education[0].get('span','').encode('ascii', 'ignore')
                except:
                    pass


                try:
                    college2 = education[1].get('institution','').encode('ascii', 'ignore')
                    course2 = education[1].get('course','').encode('ascii', 'ignore')   
                    cperiod2 = education[1].get('span','').encode('ascii', 'ignore')
                except:
                    pass

                try:
                    college3 = education[2].get('institution','').encode('ascii', 'ignore')
                    course3 = education[2].get('course','').encode('ascii', 'ignore')
                    cperiod3 = education[2].get('span','').encode('ascii', 'ignore')
                except:
                    pass

            if experience:

                try:
                    company1 = experience[0].get('organization','').encode('ascii', 'ignore')
                    designation1 = experience[0].get('position','').encode('ascii', 'ignore')
                    period1 = experience[0].get('span','').encode('ascii', 'ignore')
                except:
                    pass

                try:
                    company2 = experience[1].get('organization','').encode('ascii', 'ignore')
                    designation2 = experience[1].get('position','').encode('ascii', 'ignore')
                    period2 = experience[1].get('span','').encode('ascii', 'ignore')
                except:
                    pass

                try:
                    company3 = experience[2].get('organization','').encode('ascii', 'ignore')
                    designation3 = experience[2].get('position','').encode('ascii', 'ignore')
                    period3 = experience[2].get('span','').encode('ascii', 'ignore')
                except:
                    pass

            writer = csv.writer(f)
            try:
                writer.writerow([name, url, industry, location, title, languages , college1 , course1, cperiod1 ,\
                    college2 , course2, cperiod2, college3 , course3, cperiod3, company1, designation1, period1, company2,\
                    designation2, period2, company3, designation3, period3 , skills])
            except:
                print "Skipped"
                try:
                    writer.writerow(['---', url])
                except:
                    writer.writerow(['---'])
        else:
            try:
                writer = csv.writer(f)
                writer.writerow(['---', url])
            except:
                writer = csv.writer(f)
                writer.writerow(['---'])
        count = count + 1
        print count 
        proc = None
    f.close()
    completed_message(inputFile, outputFile)


def process_completed():

    #################################
    ### Send Email After Scraping ###
    #################################

    pass


def processData(data):

    #######################################
    ## Data Processed Out Here - from URL##
    #######################################

    try:
        profile = {}
        html = BeautifulSoup(data['content'])
        tree = etree.HTML(data['content'])
        profile['name'] = cleanup_bs4(html.select('h1.fn'))
        profile['title'] = cleanup_bs4(html.select('p.title'))
        try:
            profile['industry'] =  tree.xpath('//*[@id="demographics"]/dd[2]/text()')[0]
        except:
            profile['industry'] = ''
        profile['skills'] = [x.text for x in html.select('.skill')]
        profile['languages'] = [x.text for x in html.select('.language')]
        try:
            profile['location'] = tree.xpath('//*[@id="demographics"]/dd[1]/span/text()')[0]
        except:
            profile['location'] = ''
        try:
            profile['education'] = [
                {
                    'institution': cleanup_bs4(exp.select(".item-title")),
                    'course': cleanup_bs4(exp.select(".item-subtitle")),
                    'span': cleanup_bs4(exp.select(".date-range")),
                    'location': cleanup_bs4(exp.select(".location")),
                    'desc': cleanup_bs4(exp.select(".description"))
                }
                for exp in html.select('.school')
            ]
        except:
            pass
        try:
            profile['experience'] = [
                {
                    'position': cleanup_bs4(exp.select(".item-title")),
                    'organization': cleanup_bs4(exp.select(".item-subtitle")),
                    'span': cleanup_bs4(exp.select(".date-range")),
                    'location': cleanup_bs4(exp.select(".location")),
                    'desc': cleanup_bs4(exp.select(".description"))
                }
                for exp in html.select('.position')
            ]
        except:
            pass
    except Exception as e:
        print "Error: %s" % str(e)
        print "Data Extracted before Failure:\n%s" % json.dumps(profile, indent=4)
        return False
    return profile


def completed_message(msg, out):
    message = "@nibil @vetti scraper completed file - " + msg 
    slack.chat.post_message('#scrapie', message)
    down = slack.files.upload(out)
    link = down.body['file']['url_private_download']
    mess = "download link " + link
    slack.chat.post_message('#scrapie', mess)


"""
Run Functions out here. 
give the input output file names

"""

readData(inputFile="B2BFC.csv", outputFile="output.csv")

