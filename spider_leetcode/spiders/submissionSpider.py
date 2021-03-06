#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by LJ on 2019-02-24
import json
import os
import time
import ast
import scrapy

from spider_leetcode.items import CheckDayInfo


class SubmissionSpider(scrapy.Spider):
    # 名称，启动方式 scrapy crawl submission
    name = "submission"
    checkDate = '2019-02-28'

    # 序号
    count = 0
    # 用户submission地址
    submissonUrls = []
    # 用户信息输入路径
    path = "/leetcode-address.csv"

    submissionOfToday = 0

    submissionCount = 0

    def datetime2Timestamp(self, dt):
        time.strptime(dt, '%Y-%m-%d %H:%M:%S')
        s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S'))
        return int(s)

    def unixtime2Date(self, unixtime):
        return time.strftime('%Y-%m-%d', time.localtime(int(unixtime)))

    def userHasSubmissionOnDay(self, submission, day):
        """
        :param submission: 用户submission数据
        :param day: 查卡日期，eg：'2019-02-24'
        :return:
        """
        if submission != None:
            possibleUnixTime = [self.datetime2Timestamp(day + " 00:00:00"), self.datetime2Timestamp(day + " 08:00:00"),
                                self.datetime2Timestamp(day + " 16:00:00")]
            for i in possibleUnixTime:
                if str(i) in submission:
                    self.submissionOfToday = submission[str(i)]
                    return True
        return False

    def getSubmissionUrlsFromUserAddress(self, path):
        """
        :param path:
        :return: eg: https://leetcode.com/api/user_submission_calendar/uwi/
        """
        module_path = os.path.dirname(__file__)

        with open(module_path + path, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.split(',')[1]
                splitResult = line[8:].split("/")
                domain = splitResult[0]
                username = splitResult[1]
                submissionUrl = "https://" + domain + "/api/user_submission_calendar/" + username
                self.submissonUrls.append(submissionUrl)

    def start_requests(self):
        self.getSubmissionUrlsFromUserAddress(self.path)
        self.checkDate = time.strftime("%Y-%m-%d", time.localtime())
        for url in self.submissonUrls:
            username = url.split('/')[-1]
            yield scrapy.Request(url=url, callback=self.parse_submission, dont_filter=True,
                                 meta={'username': username})

    def checkDaysInTheLastYear(self, submissions):
        submissions = json.loads(submissions)
        days = set()
        for key, value in submissions.items():
            days.add(self.unixtime2Date(key))
        return len(days)

    def parse_submission(self, response):
        username = response.meta['username']

        self.count += 1
        submissions = json.loads(response.text)

        checkDaysInTheLastYear = self.checkDaysInTheLastYear(submissions)

        submissions = ast.literal_eval(submissions)
        sum = 0
        for key, value in submissions.items():
            sum += value
        checkDayInfo = CheckDayInfo()
        checkDayInfo['username'] = username
        checkDayInfo['checkDate'] = time.strftime("%Y-%m-%d", time.localtime())
        checkDayInfo['submissionOfToday'] = self.submissionOfToday

        checkDayInfo['submissionCount'] = sum

        checkDayInfo['checkDaysInTheLastYear'] = int(checkDaysInTheLastYear)
        if self.userHasSubmissionOnDay(submissions, self.checkDate):
            checkDayInfo['checked'] = 0
        else:
            checkDayInfo['checked'] = 1

        yield checkDayInfo
