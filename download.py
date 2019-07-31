# -*- coding:utf8 -*-

import configparser
import requests
import re
import os
import time

from bs4 import BeautifulSoup
from urllib import parse

'''
author: VastSky Miaow
description: a simple program to help you download the resources of your course
datetime: 2019/07/26
'''


'''
This function is to read the username and password from the configuration, and 
store them if can not find the configuration.
'''


def read_config():
    try:
        print('[INFO]:' + '读取配置文件\n')
        conf = configparser.ConfigParser()
        conf.read('conf.ini')
        username = conf.get('Default', 'username')
        password = conf.get('Default', 'password')
        print('[INFO]:' + '读取配置文件成功\n')
        print('[INFO]:当前正使用\t[    ' + username + '    ]\t登陆\n')
    except:
        print('[WARNING]:' + '没有配置文件conf.ini！\n')
        username, password = input("请输入用户名和密码（以空格隔开）：").split()
        config = configparser.ConfigParser()
        config['Default'] = {
            'username': username,
            'password': password
        }
        with open('conf.ini', 'w') as configfile:
            config.write(configfile)
    return username, password


'''
This function is to download resources with the given url.

:param session: the session we need for requests
:param path: the current absolute path to store the resources
:param resource_name: the full name of the resources
:param resource_url: the url for downloading the resources

:return None
'''


def download_files(session, path, resource_name, resource_url):
    res = session.get(resource_url)
    file_path = path + '/' + str(resource_name)

    isExists = os.path.exists(file_path)
    if isExists:
        print('[INFO]:跳过文件\t%s\t，该文件已下载' % resource_name + '\n')
        return
    file = open(file_path, 'wb')

    # count = 0
    # count_tmp = 0
    # length = float(res.headers['Content-Length'])
    # time1 = time.time()
    for chunk in res.iter_content(chunk_size=512):
        file.write(chunk)
        # count += len(chunk)
        # if time.time() - time1 > 0.05:
        #     p = count / length * 100
        #     speed = (count - count_tmp) / 1024 / 1024 / 2
        #     count_tmp = count
        #     print('[INFO]:' + resource_name + ': ' + '{:.2f}'.format(p) + '%' + ' Speed: ' + '{:.2f}'.format(speed) + 'M/S')
        #     time1 = time.time()
    file.close()
    print('[INFO]:\t' + str(resource_name) + '已下载完成\n')


'''
This function is to download the resources from the subfolder. (Suggest that there are 
sub folders in the resource page.)

| resource_folder
|__ sub_folder1
|__ sub_folder2


:param session: the session we need for requests
:param path: the current absolute path to store the resources
:param resource_bsObj: a BeautifulSoup Objective of the sub resource BeautifulSoup Objective
:param course_url: a url to locate the course (not used)
:param function_url: a url to request the sub resource web page
:param sakai_csrf_token: token for fill the post request packet
'''


def get_subfolder_file(session, path, resource_bsObj, course_url, function_url, sakai_csrf_token):
    collectionId = resource_bsObj.input.get('value')

    temp_list = list(collectionId[::-1])
    temp_list.pop(0)

    # sub_folder_name = collectionId[-temp_list.index('/')-1: -1]
    sub_folder_name = str(resource_bsObj.label.contents)[6:-2]
    path = path + '/' + sub_folder_name
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)

    # print('this is ' + collectionId)
    data = {'source': '0', 'collectionId': collectionId, 'navRoot': '', 'criteria': 'title',
            'sakai_action': 'doNavigate', 'rt_action': '', 'selectedItemId': '', 'itemHidden': 'false',
            'itemCanRevise': 'false', 'sakai_csrf_token': sakai_csrf_token}

    s = session.post(function_url, data=data, allow_redirects=True)

    sub_resource_bsObj = BeautifulSoup(s.text, 'html.parser')
    # sub_resource_bsObj = sub_resource_bsObj.encode('ASCII')
    # sub_resource_bsObj = sub_resource_bsObj.encode('UTF-8')
    resource_url_bsObj_set = sub_resource_bsObj.find_all('td', {'class': 'specialLink title'})
    resource_url_bsObj_set.pop(0)

    sub_resource_bsObj_list = sub_resource_bsObj.find_all('td', {'class': 'attach', 'headers': 'checkboxes'})
    if sub_resource_bsObj_list:
        sub_resource_bsObj_list.pop(0)
    # print(sub_resource_bsObj_list)

    for resource in resource_url_bsObj_set:
        resource_url = resource.find('a').get('href')
        if resource_url == '#':

            get_subfolder_file(session, path, sub_resource_bsObj_list[0], course_url, function_url, sakai_csrf_token)
            sub_resource_bsObj_list.pop(0)
            continue
        # extract the resource name from <span>
        # resource_name = resource.find('span', {'class': 'hidden-sm hidden-xs'}).contents
        # resource_name = str(resource_name)[2:-2]

        # extract the resource name from 'resource_url'
        temp_list = list(resource_url[::-1])

        resource_name = parse.unquote(resource_url[-temp_list.index('/'):])

        print('[INFO]:即将下载\t' + str(resource_name))

        print('[INFO]:切换至\t' + path + '\n')
        download_files(session, path, resource_name, resource_url)
    return None




if __name__ == '__main__':
    print('****************************************************')
    print('***                                              ***')
    print('***        UCAS Resources Download Script        ***')
    print('***                                              ***')
    print('****************************************************')
    print('\n')
    print('[TIPS]:请在校园内网（而不是CMCC和ChinaUnicom）下使用，否则需要验证码验证，导致登陆失败\n')

    username, password = read_config()

    '''
    login in the sep.ucas.ac.cn
    '''

    session = requests.Session()
    s = session.get("http://sep.ucas.ac.cn/slogin?userName=" + username + "&pwd=" + password + "&sb=sb&rememberMe=1")
    bsObj = BeautifulSoup(s.text, "html.parser")
    nameTag = bsObj.find("li", {"class": "btnav-info", "title": "当前用户所在单位"})
    if nameTag is None:
        print('[ERROR]:登录失败，请核对用户名密码\n')
        exit()
    name = nameTag.get_text()
    print('[INFO]:登陆中................')

    match = re.compile(r"\s*(\S*)\s*(\S*)\s*").match(name)
    if match:
        institute = match.group(1)
        name = match.group(2)
        print('[INFO]:成功登陆！')
        print('[INFO]:欢迎您,' + name + '\t所在单位：' + institute + '\n')
    else:
        print('[ERROR]:脚本运行错误，请重新尝试')
        exit()

    '''
    to get the BeautifulSoup objective of the course html
    '''
    # 课程网站[Full request URI: http://sep.ucas.ac.cn/portal/site/16/801]
    s = session.get('http://sep.ucas.ac.cn/portal/site/16/801')
    bsObj = BeautifulSoup(s.text, 'html.parser')
    newUrl = bsObj.find('noscript').meta.get("content")[6:]
    new_s = session.get(newUrl)
    new_bsObj = BeautifulSoup(new_s.text, 'html.parser')

    '''
    to get the courses which have been selected and build a course map in the following form:
    [index, name, url]
    '''
    # course = bsObj.find('ul', {'class': "otherSitesCategorList favoriteSiteList"})
    all_course_url = new_bsObj.find('a', {'class': "Mrphs-toolsNav__menuitem--link"}).get('href')
    all_course_obj = session.get(all_course_url)
    all_course_html = BeautifulSoup(all_course_obj.text, 'html.parser')

    all_course = all_course_html.find_all('div', {'class': "fav-title"})

    course_list = []
    index = 1

    for i in all_course:
        course = []
        course.append(index)
        course.append(i.find('a').get('title'))
        course.append(i.find('a').get('href'))
        course_list.append(course)
        index += 1

    course_list.pop(-1)
    print('[INFO]:查询到您选择了如下课程：')
    for course in course_list:
        print(str(course[0]) + '\t' + course[1])

    select_course = set()
    print('\n[INFO]:请输入需要下载课件的课程编号（以空格隔开）')
    print('[DETAILS]:如  ' + str(course_list[0][0]) + '\t表示课程    ['+course_list[0][1] + ']')
    print('[DETAILS]:如需全部下载，请输入0\n')
    course_id = input('在此输入：').split(' ')

    if '0' in course_id:
        course_id = []
        for course in course_list:

            course_id.append(course[0])

    path = input('[INFO]:请输入存储课件的路径（回车默认在脚本的路径下保存）：')
    if not path:
        current_path = os.path.abspath('.')
    else:
        current_path = path
    print('[INFO]:当前路径为' + current_path + '\n')
    for c_id in course_id:
        course_name = course_list[int(c_id)-1][1]
        print('[INFO]:当前选择的是：\t' + course_name + '\t课程\n')
        course_url = course_list[int(c_id)-1][2]
        path = current_path + '/' + course_name

        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)
        s = session.get(course_url)
        course_bsObj = BeautifulSoup(s.text, 'html.parser')

        '''
        get the url of the resource page
        '''

        resource_page_url = course_bsObj.find('a', {'title': '资源 - 上传、下载课件，发布文档，网址等信息'}).get('href')

        s = session.get(resource_page_url)
        resource_bsObj = BeautifulSoup(s.text, 'html.parser')

        '''
        get the url of the resources
        '''

        resource_url_bsObj_set = resource_bsObj.find_all('td', {'class': 'specialLink title'})
        resource_url_bsObj_set.pop(0)

        '''
        to find whether if a sub folder and add it in the list
        '''

        sub_resource_bsObj_list = resource_bsObj.find_all('td', {'class': 'attach', 'headers': 'checkboxes'})
        sub_resource_bsObj_list.pop(0)

        # to get the option url
        function_url = resource_bsObj.find('form').get('action')
        # to get the sakai_csrf_token which is a param of the post packets in HTTP requests
        sakai_csrf_token = resource_bsObj.find('input', {'name': 'sakai_csrf_token'}).get('value')
        print('[INFO]:切换至\t' + path + '\n')
        for resource in resource_url_bsObj_set:
            resource_url = resource.find('a').get('href')
            if resource_url == '#':

                get_subfolder_file(session, path, sub_resource_bsObj_list[0], course_url, function_url, sakai_csrf_token)

                sub_resource_bsObj_list.pop(0)
                continue
            # print(resource)
            # resource_name = resource.find('span', {'class': 'hidden-sm hidden-xs'}).contents
            # resource_name = str(resource_name)[2:-2]

            temp_list = list(resource_url[::-1])
            resource_name = parse.unquote(resource_url[-temp_list.index('/'):])

            print('[INFO]:即将下载\t' + str(resource_name))
            download_files(session, path, resource_name, resource_url)

        print('[INFO]: 程序已经执行完毕！')



