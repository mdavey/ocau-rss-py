import sqlite3
import sys


class Forum(object):
    def __init__(self, id, name, filename):
        self.id   = id
        self.name = name
        self.filename = filename
    
    def __str__(self):
        return 'Forum: {name} ({id})'.format(name=self.name, id=self.id)


class Post(object):
    def __init__(self, id, id_forum, date, name, title, post, url):
        self.id       = id
        self.id_forum = id_forum
        self.date     = date
        self.name     = name
        self.title    = title
        self.post     = post
        self.url      = url
    
    def __str__(self):
        return 'Post: {title} by {name} {date} ({id})'.format(title=self.title, name=self.name, date=self.date, id=self.id)


class Database(object):
    def __init__(self, filename='./data.sqlite'):
        self.con = sqlite3.connect(filename)
        
    def get_forums(self):
        cursor = self.con.cursor()
        cursor.execute('SELECT id, name, filename FROM forums')
        
        forums = []
        for (id, name, filename) in cursor.fetchall():
            forums.append(Forum(id, name, filename))
            
        return forums
    
    def get_post(self, id):
        cursor = self.con.cursor()
        cursor.execute('SELECT id, id_forum, date, name, title, post, url FROM posts WHERE id=?', (id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return Post(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        
    def get_posts(self, id_forum = None, limit = 10):
        cursor = self.con.cursor()
        
        if id_forum is None:
            cursor.execute('SELECT id, id_forum, date, name, title, post, url FROM posts LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT id, id_forum, date, name, title, post, url FROM posts WHERE id_forum=? LIMIT ?', (id_forum, limit,))
        
        posts = []
        for (id, id_forum, date, name, title, post, url) in cursor.fetchall():
            posts.append(Post(id, id_forum, date, name, title, post, url))
        
        return posts
    
    def insert_post(self, post):
        cursor = self.con.cursor()
        cursor.execute('INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?)', (post.id, post.id_forum, post.date, post.name, post.title, post.post, post.url))
        self.con.commit()
        
    def update_post(self, post):
        cursor = self.con.cursor()
        cursor.execute('UPDATE posts SET id_forum=?, date=?, name=?, title=?, post=?, url=?WHERE id=?', (post.id_forum, post.date, post.name, post.title, post.post, post.url, post.id))
        self.con.commit()


def setup_sqlite(filename='./data.sqlite'):
    """ Create a new, fresh sqlite database """
    
    con = sqlite3.connect(filename)
    cursor = con.cursor()
    
    cursor.executescript('''
        DROP TABLE IF EXISTS forums;
        
        CREATE table forums (
            id INTEGER PRIMARY KEY,
            name TEXT,
            filename TEXT
        );
        
        INSERT INTO forums VALUES (15, 'For Sale - PC Related',     'for_sale_pc_related.rss');
        INSERT INTO forums VALUES (54, 'Sponsor Specials',          'for_sale_sponser_specials.rss');
        INSERT INTO forums VALUES (70, 'For Sale - Photography',    'for_sale_photography.rss');
        INSERT INTO forums VALUES (71, 'For Sale - Motoring',       'for_sale_motoring.rss');
        INSERT INTO forums VALUES (77, 'For Sale - Non PC-Related', 'for_sale_non_pc_related.rss');
        
        DROP TABLE IF EXISTS posts;
        
        CREATE table posts (
            id INTEGER PRIMARY KEY,
            id_forum INTEGER,
            date DATE,
            name TEXT,
            title TEXT,
            post TEXT,
            url TEXT,
            FOREIGN KEY(id_forum) REFERENCES forums(id)
        );
        
    ''')

    con.commit()
    con.close()




if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'setup':
        if raw_input('Re-create database [yes/no]?') == 'yes':
            print 'Recreating database'
            setup_sqlite();
        else:
            print 'Aborting'
    else:
        print 'Usage:', sys.argv[0], 'setup'


