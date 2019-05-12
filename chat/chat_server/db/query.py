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
                        'CONSTRAINT fk_users '
                        'FOREIGN KEY (creator) REFERENCES user (nick) ON DELETE CASCADE,'
                        'CHECK (public IN (0, 1)));')

create_table_is_member = ('CREATE TABLE IF NOT EXISTS is_member ('
                          'id INTEGER PRIMARY KEY,'
                          'user TEXT NOT NULL,'
                          'channel TEXT NOT NULL,'
                          'CONSTRAINT fk_users '
                          'FOREIGN KEY (user) REFERENCES user (nick) ON DELETE CASCADE,'
                          'CONSTRAINT fk_channels '
                          'FOREIGN KEY (channel) REFERENCES channel (name) ON DELETE CASCADE);')

# Lookups.
select_nick = ('SELECT nick '
               'FROM user '
               'WHERE nick = ?')


def select_nicks(count):
    return ('SELECT DISTINCT nick '
            'FROM user '
            'WHERE nick IN ({})'
            .format(', '.join('?' * count)))

select_mail = ('SELECT mail '
               'FROM user '
               'WHERE mail = ?')

select_password = ('SELECT password '
                   'FROM user '
                   'WHERE nick = ?')

select_channel = ('SELECT name '
                  'FROM channel '
                  'WHERE name = ?')

select_creator = ('SELECT creator '
                  'FROM channel '
                  'WHERE name = ?')

select_pub_channels = ('SELECT name '
                       'FROM channel '
                       'WHERE public = 1')

select_priv_channels = ('SELECT DISTINCT channel '
                        'FROM is_member '
                        'WHERE user = ?')

# Insertion.
insert_user = ('INSERT INTO user(nick, mail, password) '
               'VALUES (?, ?, ?)')

insert_channel = ('INSERT INTO channel(name, creator, public) '
                  'VALUES (?, ?, ?)')

insert_member = ('INSERT INTO is_member(user, channel) '
                 'VALUES (?, ?)')

# Deletion.
delete_user = ('DELETE FROM user '
               'WHERE nick = ?')

delete_channel = ('DELETE FROM channel '
                  'WHERE name = ?')

select_all = 'SELECT * FROM is_member'
