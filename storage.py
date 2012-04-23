import sqlite3


class Forum(object):
    def __init__(self, id, name):
        self.id   = id
        self.name = name
    
    def __str__(self):
        return 'Forum: {name} ({id})'.format(name=self.name, id=self.id)


class Post(object):
    def __init__(self, id, id_forum, date, name, title, post):
        self.id       = id
        self.id_forum = id_forum
        self.date     = date
        self.name     = name
        self.title    = title
        self.post     = post
    
    def __str__(self):
        return 'Post: {title} by {name} {date} ({id})'.format(title=self.title, name=self.name, date=self.date, id=self.id)


class Database(object):
    def __init__(self, filename='./data.sqlite'):
        self.con = sqlite3.connect(filename)
        
    def get_forums(self):
        cursor = self.con.cursor()
        cursor.execute('SELECT id, name FROM forums')
        
        forums = []
        for (id, name) in cursor.fetchall():
            forums.append(Forum(id, name))
            
        return forums
    
    def get_post(self, id):
        cursor = self.con.cursor()
        cursor.execute('SELECT id, id_forum, date, name, title, post FROM posts WHERE id=?', (id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return Post(row[0], row[1], row[2], row[3], row[4], row[5])
        
    def get_posts(self, id_forum = None, limit = 10):
        cursor = self.con.cursor()
        
        if id_forum is None:
            cursor.execute('SELECT id, id_forum, date, name, title, post FROM posts LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT id, id_forum, date, name, title, post FROM posts WHERE id_forum=? LIMIT ?', (id_forum, limit,))
        
        posts = []
        for (id, id_forum, date, name, title, post) in cursor.fetchall():
            posts.append(Post(id, id_forum, date, name, title, post))
        
        return posts
    
    def insert_post(self, post):
        cursor = self.con.cursor()
        cursor.execute('INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?)', (post.id, post.id_forum, post.date, post.name, post.title, post.post))
        self.con.commit()
        
    def update_post(self, post):
        cursor = self.con.cursor()
        cursor.execute('UPDATE posts SET id_forum=?, date=?, name=?, title=?, post=? WHERE id=?', (post.id_forum, post.date, post.name, post.title, post.post, post.id))
        self.con.commit()


def setup_sqlite(filename='./data.sqlite'):
    """ Create a new, fresh sqlite database """
    
    con = sqlite3.connect(filename)
    cursor = con.cursor()
    
    cursor.executescript('''
        DROP TABLE IF EXISTS forums;
        
        CREATE table forums (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        
        INSERT INTO forums VALUES (15, 'For Sale - PC Related');
        INSERT INTO forums VALUES (54, 'Sponsor Specials');
        INSERT INTO forums VALUES (70, 'For Sale - Photography');
        INSERT INTO forums VALUES (71, 'For Sale - Motoring');
        INSERT INTO forums VALUES (77, 'For Sale - Non PC-Related');
        
        DROP TABLE IF EXISTS posts;
        
        CREATE table posts (
            id INTEGER PRIMARY KEY,
            id_forum INTEGER,
            date DATE,
            name TEXT,
            title TEXT,
            post TEXT,
            FOREIGN KEY(id_forum) REFERENCES forums(id)
        );
        
        INSERT INTO posts VALUES (1, 15, '2010-02-01 12:12:12', 'bill', 'stuff for sale', 'blagh');
    
    ''')

    con.commit()
    con.close()


# setup_sqlite();