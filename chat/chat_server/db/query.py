# Table creation.
create_table_user = ('CREATE TABLE IF NOT EXISTS user ('
                     'user_id INTEGER PRIMARY KEY,'
                     'nick TEXT UNIQUE NOT NULL,'
                     'mail TEXT UNIQUE NOT NULL,'
                     'password TEXT NOT NULL);')

create_table_channel = ('CREATE TABLE IF NOT EXISTS channel ('
                        'channel_id INTEGER PRIMARY KEY,'
                        'name TEXT UNIQUE NOT NULL,'
                        'creator TEXT NOT NULL,'
                        'public INTEGER NOT NULL,'
                        'FOREIGN KEY (creator) REFERENCES user (nick),'
                        'CHECK (public IN (0, 1)));')

create_table_is_member = ('CREATE TABLE IF NOT EXISTS is_member ('
                          'id INTEGER PRIMARY KEY,'
                          'user TEXT NOT NULL,'
                          'channel TEXT NOT NULL,'
                          'FOREIGN KEY (user) REFERENCES user (nick),'
                          'FOREIGN KEY (channel) REFERENCES channel (name));')

# Lookups.
select_nick = ('SELECT nick '
               'FROM user '
               'WHERE nick = ?')

select_mail = ('SELECT mail '
               'FROM user '
               'WHERE mail = ?')

select_password = ('SELECT password '
                   'FROM user '
                   'WHERE nick = ?')

# Insertion.
insert_user = ('INSERT INTO user(nick, mail, password) '
               'VALUES (?, ?, ?)')

# Deletion.
delete_user = ('DELETE FROM user '
               'WHERE nick = ?')