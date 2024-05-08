import os, sqlite3, click
from functools import wraps
from flask import Flask, flash, render_template, redirect, session, request, url_for,current_app, g



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            flash("Not logged in")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



def get_db():

    conn = sqlite3.connect('mylist.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()



def get_item_by_name_for_user(item_name, user_id):

    db = get_db()
    item = db.execute('SELECT * FROM item WHERE item_name = ? COLLATE NOCASE AND user_id = ?', (item_name, user_id),).fetchone()
    close_db()
    return item
    


def get_item_by_id_for_user(item_id, user_id):

    db = get_db()
    item = db.execute('SELECT * FROM item WHERE item_id = ? AND user_id = ?', (item_id, user_id),).fetchone()
    close_db()
    return item



def create_item_for_user(item_name, user_id):

    db = get_db()
    db.execute('INSERT INTO item (item_name, user_id) VALUES (?, ?)', (item_name, user_id))
    db.commit()
    close_db()
    return True



def add_item_to_active_list(item_id, user_id, quantity):
    
    db = get_db()
    db.execute('INSERT INTO user_active_items (item_id, user_id, active_items_quantity) VALUES (?, ?, ?)', (item_id, user_id, quantity))
    db.commit()
    close_db()
    return True



def add_item_to_active_list_from_group(user_id, item_id, groups_id, quantity):

    db = get_db()
    db.execute('INSERT INTO user_active_items (user_id, item_id, groups_id, active_items_quantity) VALUES (?, ?, ?, ?)', (user_id, item_id, groups_id, quantity))
    db.commit()
    close_db()
    return True



def get_single_user_active_item(user_id, item_id, groups_id):
    
    db = get_db()
    item = db.execute('SELECT * FROM user_active_items WHERE user_id = ? AND item_id = ? AND groups_id = ?', (user_id, item_id, groups_id,)).fetchone()
    close_db()
    return item




def get_active_item_with_null_group(item_id, user_id):
    
    db = get_db()
    item = db.execute('SELECT * FROM user_active_items WHERE item_id = ? AND user_id = ? AND groups_id IS NULL', (item_id, user_id)).fetchone()
    close_db()
    return item



def update_active_item_quantity(new_quantity, user_id, item_id, groups_id):

    db = get_db()
    db.execute('UPDATE user_active_items SET active_items_quantity = ? WHERE user_id = ? AND item_id = ? AND groups_id = ?', (new_quantity, user_id, item_id, groups_id,))
    db.commit()
    close_db()
    return True



def update_active_item_with_null_group_quantity(item_id, user_id, quantity):
    
    db = get_db()
    db.execute('UPDATE user_active_items SET active_items_quantity = ? WHERE item_id = ? AND user_id = ? AND groups_id IS NULL', (quantity, item_id, user_id))
    db.commit()
    close_db()
    return True



def get_users_groups(user_id):

    db = get_db()
    groups = list(db.execute('SELECT * FROM groups WHERE user_id = ?', (user_id,)))
    close_db()
    return groups



def get_users_items(user_id):

    db = get_db()
    items = list(db.execute('SELECT * FROM item WHERE user_id = ? ORDER BY item_name', (user_id,)))
    close_db()
    return items



def get_users_active_items(user_id):
    
    db = get_db()
    users_active_items = list(db.execute('SELECT * FROM user_active_items JOIN item ON user_active_items.item_id = item.item_id WHERE user_active_items.user_id = ? ORDER BY item.item_name', (user_id,)))
    close_db()
    return users_active_items



def get_group_by_id_for_user(group_id, user_id):
    db = get_db()
    group = db.execute('SELECT * FROM groups WHERE groups_id = ? AND user_id = ?', (group_id, user_id)).fetchone()
    close_db()
    return group



def get_groups_items_by_group_id(group_id):
    db = get_db()
    items = list(db.execute('SELECT * FROM groups_items JOIN item ON groups_items.item_id = item.item_id WHERE groups_id = ?', (group_id,)))
    close_db()
    return items