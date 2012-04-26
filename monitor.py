# core
import os
import re
import time
import datetime
import traceback

# library
from bs4 import BeautifulSoup
from dateutil import parser
import requests
import PyRSS2Gen

# local
from storage import Database, Post


LOGIN_DETAILS = '/home/matthewd/.ocau-login'
RSS_DIRECTORY = '/home/matthewd/code/ocau-rss-py/rss'
REFRESH_DELAY = 240


def perform_login():
    """ Post to the login page with my username/password and use
        requests.session to store my cookies for all future requests
        
        Description of keys:
            securitytoken               No idea  (always 'guest')
            vb_login_md5password        rather than post a plain text password
                                        VB can use javascript to make a md5 hash
                                        Passing an empty strin is acceptable
            vb_login_md5password_utf    As above
            vb_login_username           Account username
            vb_login_password           Account password (plaintext)
            s                           No idea (seems to have a random key?)
            do                          Action to perform (always 'login')   """

    login_details = open(LOGIN_DETAILS, 'r').read()
    (username, password) = login_details.split('#')

    url = 'http://forums.overclockers.com.au/login.php?do=login';
    payload = {
        'securitytoken'            : 'guest',
        'vb_login_md5password'     : '',
        'vb_login_md5password_utf' : '',
        'vb_login_password'        : password,
        'vb_login_username'        : username,
        's'                        : '',
        'do'                       : 'login',
    }

    session = requests.session()
    req = session.post('http://forums.overclockers.com.au/login.php?do=login', data=payload)
    
    if "Thank you for logging in" not in req.text:
        return None
    
    return session


def get_thread_ids(soup):
    """return an array of thread ids (ignoring any sticky theads)"""

    def get_thread_id_for_row(row):
        """ Given a row, find all the a tags and check for a link to
            showthread.php """
        for a in row.find_all('a'):
            if a.has_attr('href'):
                match = re.match("showthread.php\?t=(\d+)", a['href'])
                if match is not None:
                    return int(match.group(1))
        return None
    
    def row_is_sticky(row):
        """ Given a row, find all the img tags and check if there is one that
            points to sticky.gif """
        for img in row.find_all('img'):
            if img['src'] == 'images/misc/sticky.gif':
                return True
        return False

    thread_ids = []
    rows = soup.find_all('tr')
    for row in rows:
        thread_id = get_thread_id_for_row(row)
        if (thread_id is not None) and (row_is_sticky(row) == False):
            thread_ids.append(thread_id)
    
    return thread_ids


def get_post_details(soup):
    """ Get post details from print preview html page like the below
       - http://forums.overclockers.com.au/printthread.php?t=1025975&pp=1 """
    
    def get_title(soup):
        """ Use the page title as it has state tags.  Though we need to remove
            the prefix """
        return soup.head.title.string.replace('Overclockers Australia Forums - ', '')
    
    def get_name(soup):
        tags = soup.find_all('td', {'style': 'font-size:14pt'})
        if len(tags) != 1:
            return None
        return tags[0].string
    
    def get_datetime(soup):
        """ Use date_util.parser.parse because dates are hard """
        tags = soup.find_all('td', {'class': 'smallfont', 'align': 'right'});
        if len(tags) != 1:
            return None
        print 'date', tags[0].string, 'parsed', parser.parse(tags[0].string)
        return parser.parse(tags[0].string)
        
    def get_post(soup):
        """ There is a single td with the class=page and inside are two divs
            the first has the page title, and the second the post contents
            
            We use renderContents to get all children of the div tag join
            together nicely  (div[1] still has the div tag)"""
        tds = soup.find_all('td', {'class': 'page'})
        if len(tds) != 1:
            return None
        divs = tds[0].find_all('div')
        if len(divs) < 2:
            return None        
        return unicode(divs[1].renderContents(), 'utf-8')
    
    title = get_title(soup)
    name  = get_name(soup)
    date  = get_datetime(soup)
    post  = get_post(soup)
    
    for (i,j) in [('title', title), ('name', name), ('date', date), ('post', post)]:
        if j is None:
            print 'Could not find {}'.format(i)
            return None
        
    if all([title is not None, name is not None, date is not None, post is not None]) == False:
        return None
    
    return {
        'date':  date,
        'name':  name,
        'title': title,
        'post':  post,
    }
    
def update_all_rss_files():
    database = Database()
    
    print 'Writting RSS files'
    for forum in database.get_forums():
        write_rss_file(RSS_DIRECTORY + '/' + forum.filename, forum.name, forum.id, entries=25)
        
    write_rss_file(RSS_DIRECTORY + '/for_sale_all.rss', 'For Sale: All', None, entries=50)

    

def write_rss_file(dest, title, id_forum = None, entries = 20):
    database = Database()
    
    posts = database.get_posts(id_forum, entries)
    rss_items = []
    
    for post in posts:
        pubDate = parser.parse(post.date)
        pubDate += datetime.timedelta(hours=-10) # rss wants GMT time.  this is going to break come DST
        rss_items.append(PyRSS2Gen.RSSItem(
            title = post.title,
            link = post.url,
            description = post.get_post(),
            guid = PyRSS2Gen.Guid(post.url),
            pubDate = pubDate))

    rss = PyRSS2Gen.RSS2(
        title = title,
        link = "http://project-2501.net/index.php/ocau-for-sale-rss-feed/",
        description = "OCAU For Sale RRS Feed",
        lastBuildDate = datetime.datetime.utcnow(),
        items=rss_items)
    
    print 'Writing:', dest
    with open(dest, 'w+') as f:
        rss.write_xml(f)



database = Database()

while True:
    try:
        
        print 'Re-starting requests.session'
        session  = perform_login()
        for forum in database.get_forums():
            request    = session.get('http://forums.overclockers.com.au/forumdisplay.php?f=' + str(forum.id))
            soup       = BeautifulSoup(request.text);
            thread_ids = get_thread_ids(soup)
            
            for thread_id in thread_ids:
                
                if database.get_post(thread_id) is not None:
                    # print 'Already fetched post for thread {id}'.format(id=thread_id)
                    continue
                
                request          = session.get('http://forums.overclockers.com.au/printthread.php?pp=1&t=' + str(thread_id))
                soup             = BeautifulSoup(request.text)
                post_details     = get_post_details(soup)
                
                if post_details is None:
                    print 'Failed gettin post details for thread {id}'.format(id=thread_id)
                    continue
                
                p = Post(
                    id=thread_id,
                    id_forum=forum.id,
                    date=post_details['date'],
                    name=post_details['name'],
                    title=post_details['title'],
                    post=post_details['post'],
                    url='http://forums.overclockers.com.au/showthread.php?t=' + str(thread_id),
                )
                
                database.insert_post(p)
                print 'Saved post {id}'.format(id=thread_id)

        update_all_rss_files()
        print 'Sleeping for', REFRESH_DELAY, 'seconds before next check'
        time.sleep(REFRESH_DELAY)
    
    except:
        print 'Exception'
        print '-'*60
        traceback.print_exc(file=os.sys.stdout)
        print '-'*60
        print 'Sleeping for', REFRESH_DELAY, 'seconds'
        time.sleep(REFRESH_DELAY)
        
