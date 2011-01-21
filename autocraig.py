# Author : Alex Ksikes

# requires 
# - send_mail.py
# - html2text.py

# TODO:
# - faster page retrieval (concurrent dnl)
# - test auto email
# - test duplicates by bag of words
# - it'd be nicer to specify some set of keywords (no urls)
# then create one big page for all the queries

import re, urllib

def autocraig(search_url, auto=False, report=False, 
              ignore_duplicates=False, quiet=False, 
              duplicates_file=None, conf_file=None):
    # read config file
    read_conf(conf_file)
    # set the duplicate file
    if not duplicates_file:
        duplicates_file = conf['DUPLICATES']
    # load duplicates
    duplicates = {}
    if not ignore_duplicates:
        duplicates = load_duplicates(duplicates_file)
    # get all posts
    posts = get_all_posts(search_url, duplicates)
    # add to duplicates
    add_to_duplicates(duplicates_file, posts)
    # report an hrml if needed
    if report:
        email_digest(posts)
    # auto email all autors
    if auto:
        email_authors(posts, auto)
    # output result to stdout
    if not quiet:
        print rep(posts),
    
conf = {
    'FROM_EMAIL' : '',
    'REPLY_EMAIL' : '',
    'CC_EMAIL' : '',
    'NUM_DAYS' : 3,
    'NUM_PAGES' : 3,
    'TO_EMAIL' : '',
    'DEEP' : 1,
    'DUPLICATES' : 'autocraig.duplicates',
    'VALID' : 15,
    'SIMILARITY' : 0.9}
def read_conf(conf_file):
    global conf
    for l in open(conf_file):
        if re.match('^#|\s+[#\s]*', l):
            continue
        (k, v) = map(lambda s: s.strip(), l.split('='))
        conf[k.upper()] = v
    
d_sep = '@#@#@'
def load_duplicates(duplicate_file):
    duplicates = {}
    data = open(duplicate_file).read().split(d_sep)
    for (craig_id, text) in zip(data[0::2], data[1::2]):
        duplicates[craig_id] = text
    return duplicates

import urlparse
def get_all_posts(search_url, duplicates, deep=conf['DEEP']):
    posts = []
    #for i in range(deep):
    #    search_url += '&s=%s' % i * 100
    for u in get_post_urls(search_url):
        post = get_post(urlparse.urljoin(search_url, u))
        if not duplicates or not is_duplicates(duplicates, post):
            posts.append(post)
    return posts

#p_urls = re.compile('<p>&nbsp;.*?&nbsp;&nbsp;&nbsp;<a href="(.*?)">.*?</a>', re.I)
#p_urls = re.compile('<p>.*?\-.*?<a href="(.*?)">.*?</a>', re.I)
p_urls = re.compile('\s\-.*?<a\shref="(.*?)">.*?</a>')
def get_post_urls(search_url):
    html = urllib.urlopen(search_url).read()
    return p_urls.findall(html)

import html2text
p_post = {'reply' : re.compile('mailto:(.*?)\?', re.I), 
          'description_html' : re.compile('(<h2>.*?postingid:\s[0-9]+)<br>', re.I|re.S)}
def get_post(post_url):
    post, html = {}, urllib.urlopen(post_url).read()
    post['url'] = post_url
    post['craig_id'] = re.findall('/([0-9]+)\.html', post_url)[0]
    for type, p in p_post.items():
        txt = p.findall(html)
        if txt:
            txt = txt[0]
        else:
            txt = ''
        post[type] = txt
    try:
        post['description_text'] = html2text.html2text(post['description_html']).encode('utf-8')
    except:
        post['description_text'] = ''
    post['phone'], post['email_alternative'] = analyze(post['description_text'])
    return post
    
def is_duplicates(duplicates, post):
    #print post['craig_id']
    if duplicates.has_key(post['craig_id']):
        return True
    for text in duplicates.values():
        if dot(text, post['description_text']) >= conf['SIMILARITY']:
            return True
    return False
    
def get_bag(s):
    v = {}
    for w in s.split():
        v[w] = v.get(w, 0) + 1
    return v

def dot(s1, s2):
    v1, v2 = get_bag(s1), get_bag(s2)
    score = 0
    for w, val in v1.items():
        if v2.has_key(w):
            score += v2[w] * val
    norm = max(len(s1.split()), len(s2.split()))
    if norm == 0:
        norm = 1
        score = 0
    return 1.0 * score / norm 

def add_to_duplicates(duplicates_file, posts):
    o = open(duplicates_file, 'a')
    for post in posts:
        o.write(post['craig_id'] + d_sep + post['description_text'] + d_sep)
    o.close()

# from dive into python
phonePattern = re.compile(r'''
                # don't match beginning of string, number can start anywhere
    (\d{3})     # area code is 3 digits (e.g. '800')
    \D*         # optional separator is any number of non-digits
    (\d{3})     # trunk is 3 digits (e.g. '555')
    \D*         # optional separator
    (\d{4})     # rest of number is 4 digits (e.g. '1212')
    \D*         # optional separator
    (\d*)       # extension is optional and can be any number of digits
    $           # end of string
    ''', re.I)
# from aspn cookbook
mailPattern = re.compile(r'''
    [\w\-][\w\-\.]*@[\w\-][\w\-\.]+[a-zA-Z]{1,4}
    ''', re.I) 
def analyze(description_text):
    phone = phonePattern.findall(description_text)
    if not phone:
        phone = ['']
    email = mailPattern.findall(description_text)
    if not email:
        email = ['']
    return (phone[0], email[0])
    
from send_mail import send_mail
import datetime
def email_digest(posts):
    if posts:
        send_mail(to_addrs=conf['TO_EMAIL'].split(','), cc_addrs=conf['CC_EMAIL'].split(','), 
                  message=rep(posts, html=True), from_addr=conf['FROM_EMAIL'],
                  content_type='text/html', subject='craigslist-auto-%s' % datetime.datetime.now())
        
def email_authors(posts, msg):
    for post in posts:
        send_mail(to_addrs=post['reply'], from_addrs=conf['FROM_EMAIL'], 
                  cc_addrs=conf['CC_EMAIL'].split(','), message=msg, subject=post['title'])
    
def rep(posts, html=False):
    s = ''
    for post in posts:
        if html:
            info = '<a href="%s">source</a>' % post['url']
            sep = '<hr>\n'
            desc = 'description_html'
        else:
            info = 'source : ' + post['url']
            sep = 50 * '#' + '\n'
            desc = 'description_text'
        info += post['phone'] + post['email_alternative']
        s += sep + info + post[desc] + '\n'
    return s[:-1]
    
def usage():
    print "Usage: python autocraig.py [options] search_url"
    print
    print "Description:" 
    print "Scrape craigslist posts for a section specified by the search url."
    print "Print to stdout all the posts that have been scraped."
    print "Auto email the author's of each post."
    print "All config options are specified in cwd/autocraig.conf."
    print "Lists of duplicates are kept in cwd/autocraig.duplicates."
    print
    print "Options:" 
    print "--conf config_file: path to autocraig.conf"
    print "--auto msg_file: email all authors wiht msg_file or use - to read from stdin"
    print "--report : send digest html email with pictures and summary"
    print "--ignore-duplicates : ignore the duplicate detection facility"
    print "--duplicate-file file : use another duplicate file"
    print "--quiet : do not show the emailed posts and summary"
    print "--help : this help message"
    print
    print "Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)" 
    
import sys, getopt
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", 
                        ["conf=", "auto", "report", "ignore-duplicates", "quiet", "duplicate-file=", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    auto = report = ignore_duplicates = quiet = False
    duplicate_file = None
    conf_file = 'autocraig.conf'
    for o, a in opts:
        if o  == "--auto":
            auto = a
            if a == '-':
                auto = sys.stdin.read()  
        elif o == "--report":
            report = True   
        elif o == "--ignore-duplicates":
            ignore_duplicates = True   
        elif o == "--quiet":
            quiet = True  
        elif o == "--conf":
            conf_file = a  
        elif o == "--duplicate-file":
            duplicate_file = a  
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) < 1:
        usage()
    else:
        autocraig(args[-1], auto=auto, report=report, 
                  ignore_duplicates=ignore_duplicates, quiet=quiet, 
                  duplicates_file=duplicate_file, conf_file=conf_file)
      
if __name__ == '__main__':
    main()