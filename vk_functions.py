import logging
import os.path
import json
import time
import requests
from bs4 import BeautifulSoup
from collections import Counter
from dotenv import load_dotenv
from urllib.request import urlopen

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')


def get_id(nickname):
    if '/' in nickname:
        nickname = nickname[nickname.rfind('/')+1:]
    url = f"https://api.vk.com/method/users.get?user_ids={nickname}&lang=ru&access_token={VK_TOKEN}&v=5.130"
    resp = urlopen(url)
    html = resp.read()
    status = json.loads(html)
    try:
        id = str(status['response'][0]['id'])
    except:
        return 'Не удалось выяснить id'
    return id


def get_friends(user_id):
    friends = {}
    urlFull = f'https://api.vk.com/method/friends.get?user_id={user_id}&lang=ru&fields=first_name,last_name&access_token={VK_TOKEN}&v=5.130'
    respFull = urlopen(urlFull)
    htmlFull = respFull.read()
    reqVkFull = json.loads(htmlFull)
    try:
        friends_list = reqVkFull['response']['items']
        for friend in friends_list:
            friends[str(friend['id'])] = f"{friend['last_name']} {friend['first_name']}"
    except:
        url = f"https://onli-vk.ru/pivatfriends.php?id={user_id}"
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.141 YaBrowser/22.3.3.852 Yowser/2.5 Safari/537.36',
            'cookie': '_ym_uid=1655392315715518907; _ym_d=1655392315; _ym_isad=2; _ym_visorc=b'
        }
        req = requests.get(url, headers=header)
        soup = BeautifulSoup(req.text, 'html.parser')
        for a in soup.find_all('a'):
            if 'vk.com/id' in a['href']:
                friendID = str(a)
                pos = friendID.find('com/id')
                friendID = friendID[pos + 6:]
                pos = friendID.find('\"')
                friendID = friendID[:pos]
                name = str(a)
                pos = name.find('>')
                name = name[pos + 1:]
                pos = name.find('<')
                name = name[:pos]
                if friendID != user_id:
                    friends[friendID] = name
        # if len(friends) > 1:
        #     del friends[user_id]
    return friends


def get_best_friends(user_id):
    big_dict = get_friends(user_id)
    big_list = list(big_dict)
    for friend in big_dict:
        big_list.extend(list(get_friends(friend)))
        big_dict = big_dict | get_friends(friend)
    count = Counter(big_list)
    list_count = list(count.items())
    list_count.sort(key=lambda i: i[1])
    list_count.reverse()
    best_friends = 'Наибольшее количество общих друзей:\n'
    j = 0
    for i in list_count:
        best_friends += f"id{i[0]} - {big_dict[i[0]]}, общих друзей {i[1]}\n"
        j += 1
        if j == 20 or i[1] == 1:
            break


def get_list_friends(list_ids: list):
    list_friends = []
    for user_id in list_ids:
        urlFull = f'https://api.vk.com/method/friends.get?user_id={user_id}&lang=ru&access_token={VK_TOKEN}&v=5.130'
        respFull = urlopen(urlFull)
        htmlFull = respFull.read()
        reqVkFull = json.loads(htmlFull)
        try:
            friends = map(str, reqVkFull['response']['items'])
        except:
            urlFull = "https://onli-vk.ru/pivatfriends.php?id=" + user_id
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.141 YaBrowser/22.3.3.852 Yowser/2.5 Safari/537.36',
                'cookie': '_ym_uid=1655392315715518907; _ym_d=1655392315; _ym_isad=2; _ym_visorc=b'
            }
            req = requests.get(urlFull, headers=header)
            soup = BeautifulSoup(req.text, 'html.parser')
            friends = []
            print(req.status_code)
            for a in soup.find_all('a'):
                if 'vk.com/id' in a['href']:
                    friendID = str(a)
                    pos = friendID.find('com/id')
                    friendID = friendID[pos + 6:]
                    pos = friendID.find('\"')
                    friendID = friendID[:pos]
                    friends.append(friendID)
        list_friends.extend(friends)
    c = Counter(list_friends)
    clear_list = [x for x in list_friends if c[x] == len(list_ids)]
    return set(clear_list)


def get_big_list(user_id):
    urlFull = f'https://api.vk.com/method/friends.get?user_id={user_id}&lang=ru&fields=schools,status,last_seen,occupation,nickname,relatives,relation,personal,connections,exports,activities,interests,music,movies,tv,books,games,about,quotes,career,nickname,domain,bdate,city,country,photo_100,has_mobile,contacts,education,relation,last_seen,universities,status&access_token={VK_TOKEN}&v=5.130'
    respFull = urlopen(urlFull)
    htmlFull = respFull.read()
    reqVkFull = json.loads(htmlFull)
    try:
        answerFull = reqVkFull['response']['items']
    except:
        info5 = 'Профиль скрыт настройками приватности. Данные носят ориентировочный характер.\n\n'
        info5 += get_big_list_private(user_id)
        return info5
    info2 = f'Всего найдено {len(answerFull)} возможных друзей\n'
    for friend in answerFull:
        time.sleep(0.1)
        info2 += 'id'
        info2 += str(friend['id'])
        friendID = 'id' + str(friend['id'])
        try:
            domain = friend['domain']
            if domain != '' and domain != friendID:
                info2 += ' ('
                info2 += domain
                info2 += ')'
        except:
            nickname = ''
        info2 += ' - '
        info2 += friend['first_name']
        try:
            nickname = friend['nickname']
            if nickname != '':
                info2 += ' '
                info2 += nickname
        except:
            nickname = ''
        info2 += ' '
        info2 += friend['last_name']
        try:
            bdate = friend['bdate']
            if bdate != '':
                info2 += ', ДР: '
                info2 += bdate
        except:
            bdate = ''
        try:
            country = friend['country']['title']
            if country != '':
                info2 += ', '
                info2 += country
        except:
            country = ''
        try:
            city = friend['city']['title']
            if city != '':
                info2 += ', '
                info2 += city
        except:
            city = ''
        try:
            university_name = friend['university_name']
            if university_name != '' and university_name != '0':
                info2 += ', '
                info2 += university_name
        except:
            university_name = ''
        try:
            faculty_name = friend['faculty_name']
            if faculty_name != '' and faculty_name != '0':
                info2 += ', '
                info2 += faculty_name
        except:
            faculty_name = ''
        try:
            graduation = friend['graduation']
            if graduation != '' and graduation != '0' and len(graduation) > 1:
                info2 += ' ('
                info2 += graduation
                info2 += ')'
        except:
            graduation = ''
        try:
            occupation = friend['occupation']['name']
            if occupation != '' and occupation != '0' and occupation != university_name:
                info2 += ', '
                info2 += occupation
        except:
            occupation = ''
        try:
            career = friend['career']
            if len(career) > 0:
                for work in career:
                    if work['company'] != occupation:
                        info2 += ', '
                        info2 += work['company']
                    try:
                        position = work['position']
                        if len(position) > 1:
                            info2 += ' '
                            info2 += position
                    except:
                        position = ''
                    try:
                        workfrom = work['from']
                        if len(str(workfrom)) > 1:
                            info2 += ' c '
                            info2 += workfrom
                    except:
                        workfrom = ''
                    try:
                        workuntil = work['until']
                        if len(str(workuntil)) > 1:
                            info2 += ' по '
                            info2 += workuntil
                    except:
                        workuntil = ''
        except:
            career = ''
        try:
            relation = friend['relation']
            if relation == 1:
                info2 += ', не женат/не замужем'
            elif relation == 4:
                info2 += ', женат/замужем'
            elif relation == 7:
                info2 += ', влюблен/влюблена'
        except:
            relation = ''
        try:
            relation_partner = friend['relation_partner']
            if len(relation_partner) > 0:
                info2 += ' ('
                info2 += friend['relation_partner']['first_name']
                info2 += ' '
                info2 += friend['relation_partner']['last_name']
                info2 += ', id'
                info2 += str(friend['relation_partner']['id'])
                info2 += ')'
        except:
            relation_partner = ''
        try:
            mobile_phone = friend['mobile_phone']
            if mobile_phone != '' and mobile_phone != '0' and len(mobile_phone) > 4:
                info2 += ', '
                info2 += mobile_phone
        except:
            mobile_phone = ''
        try:
            home_phone = friend['home_phone']
            if home_phone != '' and home_phone != '0' and len(home_phone) > 4:
                info2 += ', '
                info2 += home_phone
        except:
            home_phone = ''
        info2 += '\n'
    return info2


def get_big_list_private(user_id):
    info5 = ''
    url = "https://onli-vk.ru/pivatfriends.php?id=" + user_id
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.141 YaBrowser/22.3.3.852 Yowser/2.5 Safari/537.36',
        'cookie': '_ym_uid=1655392315715518907; _ym_d=1655392315; _ym_isad=2; _ym_visorc=b'
    }
    req = requests.get(url, headers=header)
    soup = BeautifulSoup(req.text, 'html.parser')
    friends = {}
    for a in soup.find_all('a'):
        if 'vk.com/id' in a['href']:
            friendID = str(a)
            pos = friendID.find('com/id')
            friendID = friendID[pos + 6:]
            pos = friendID.find('\"')
            friendID = friendID[:pos]
            name = str(a)
            pos = name.find('>')
            name = name[pos + 1:]
            pos = name.find('<')
            name = name[:pos]
            if friendID != user_id:
                friends[friendID] = name
    user_id = ''
    info5 += f'Всего найдено {len(friends)} возможных друзей\n'
    for i in friends:
        user_id = user_id + i
        user_id = user_id + ','
    user_id = user_id[0:-1]
    urlFull = f'https://api.vk.com/method/users.get?user_ids={user_id}&lang=ru&fields=schools,status,last_seen,occupation,nickname,relatives,relation,personal,connections,exports,activities,interests,music,movies,tv,books,games,about,quotes,career,nickname,domain,bdate,city,country,photo_100,has_mobile,contacts,education,relation,last_seen,universities,status&access_token={VK_TOKEN}&v=5.130'
    respFull = urlopen(urlFull)
    htmlFull = respFull.read()
    reqVkFull = json.loads(htmlFull)
    try:
        answerFull = reqVkFull['response']
    except:
        answerFull = 'Закрытый профиль'
    for friend in answerFull:
        time.sleep(0.2)
        info5 += 'id'
        info5 += str(friend['id'])
        friendID = 'id' + str(friend['id'])
        try:
            domain = friend['domain']
            if domain != '' and domain != friendID:
                info5 += ' ('
                info5 += domain
                info5 += ')'
        except:
            nickname = ''
        info5 += ' - '
        info5 += friend['first_name']
        try:
            nickname = friend['nickname']
            if nickname != '':
                info5 += ' '
                info5 += nickname
        except:
            nickname = ''
        info5 += ' '
        info5 += friend['last_name']
        try:
            bdate = friend['bdate']
            if bdate != '':
                info5 += ', ДР: '
                info5 += bdate
        except:
            bdate = ''
        try:
            country = friend['country']['title']
            if country != '':
                info5 += ', '
                info5 += country
        except:
            country = ''
        try:
            city = friend['city']['title']
            if city != '':
                info5 += ', '
                info5 += city
        except:
            city = ''
        try:
            university_name = friend['university_name']
            if university_name != '' and university_name != '0':
                info5 += ', '
                info5 += university_name
        except:
            university_name = ''
        try:
            faculty_name = friend['faculty_name']
            if faculty_name != '' and faculty_name != '0':
                info5 += ', '
                info5 += faculty_name
        except:
            faculty_name = ''
        try:
            graduation = friend['graduation']
            if graduation != '' and graduation != '0' and len(graduation) > 1:
                info5 += ' ('
                info5 += graduation
                info5 += ')'
        except:
            graduation = ''
        try:
            occupation = friend['occupation']['name']
            if occupation != '' and occupation != '0' and occupation != university_name:
                info5 += ', '
                info5 += occupation
        except:
            occupation = ''
        try:
            career = friend['career']
            if len(career) > 0:
                for work in career:
                    if work['company'] != occupation:
                        info5 += ', '
                        info5 += work['company']
                    try:
                        position = work['position']
                        if len(position) > 1:
                            info5 += ' '
                            info5 += position
                    except:
                        position = ''
                    try:
                        workfrom = work['from']
                        if len(str(workfrom)) > 1:
                            info5 += ' c '
                            info5 += workfrom
                    except:
                        workfrom = ''
                    try:
                        workuntil = work['until']
                        if len(str(workuntil)) > 1:
                            info5 += ' по '
                            info5 += workuntil
                    except:
                        workuntil = ''
        except:
            career = ''
        try:
            relation = friend['relation']
            if relation == 1:
                info5 += ', не женат/не замужем'
            elif relation == 4:
                info5 += ', женат/замужем'
            elif relation == 7:
                info5 += ', влюблен/влюблена'
        except:
            relation = ''
        try:
            relation_partner = friend['relation_partner']
            if len(relation_partner) > 0:
                info5 += ' ('
                info5 += friend['relation_partner']['first_name']
                info5 += ' '
                info5 += friend['relation_partner']['last_name']
                info5 += ', id'
                info5 += str(friend['relation_partner']['id'])
                info5 += ')'
        except:
            relation_partner = ''
        try:
            mobile_phone = friend['mobile_phone']
            if mobile_phone != '' and mobile_phone != '0' and len(mobile_phone) > 4:
                info5 += ', '
                info5 += mobile_phone
        except:
            mobile_phone = ''
        try:
            home_phone = friend['home_phone']
            if home_phone != '' and home_phone != '0' and len(home_phone) > 4:
                info5 += ', '
                info5 += home_phone
        except:
            home_phone = ''
        info5 += '\n'
    return info5
