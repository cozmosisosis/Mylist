import os, logging, sqlite3
from datetime import datetime
from flask import Flask, flash, jsonify, render_template, redirect, session, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import helpers

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'





@app.post("/active_list_add_item")
@helpers.login_required
def active_list_add_item():

    item_to_add = request.form.get('item_to_add').strip()
    quantity_to_add = request.form.get('quantity')
    quantity_to_add_int = int(quantity_to_add)
    if not item_to_add or not quantity_to_add or quantity_to_add_int < 1:
        return redirect(url_for('active_list_data'))

    valid_item = helpers.get_item_by_name_for_user(item_to_add, session['user_id'])

    if not valid_item:

        helpers.create_item_for_user(item_to_add, session['user_id'])
        new_item = helpers.get_item_by_name_for_user(item_to_add, session['user_id'])
        helpers.add_item_to_active_list(new_item['item_id'], session['user_id'], quantity_to_add_int)
        return redirect(url_for('active_list_data'))

    item_on_list = helpers.get_active_item_with_null_group(valid_item['item_id'], session['user_id'])
    if item_on_list:
        new_quantity = item_on_list['active_items_quantity'] + quantity_to_add_int
        helpers.update_active_item_with_null_group_quantity(valid_item['item_id'], session['user_id'], new_quantity)
        return redirect(url_for('active_list_data'))

    helpers.add_item_to_active_list(valid_item['item_id'], session['user_id'], quantity_to_add_int)
    return redirect(url_for('active_list_data'))



@app.post('/add_from_group')
@helpers.login_required
def add_from_group():

    error = None
    items = request.form


    for key in items:
        if key == 'groups_id':
            groups_id = items[key]
        else:
            valid_item = helpers.get_item_by_id_for_user(key, session['user_id'])
            if not valid_item:
                error = 'Invalid Item in submission'

            if not error:
                try:
                    if int(items[key]) < 0:
                        error = 'Invalid quantity submitted'

                except:
                    error = 'One item was submitted with an empty quantity section, please make sure to enter a "0" if there is an item you would not like to add.'



    if error:
        users_groups = helpers.get_users_groups(session['user_id'])
        users_items = helpers.get_users_items(session['user_id'])
        user_active_items = helpers.get_users_active_items(session['user_id'])
        return jsonify(render_template('/ajax_templates/ajax_index.html', users_groups=users_groups, users_items=users_items, user_active_items=user_active_items, error=error))


    for key in items:
        if key != 'groups_id':
            item_in_list = helpers.get_single_user_active_item(session['user_id'], key, groups_id)

            if int(items[key]) != 0:
                if not item_in_list:
                    helpers.add_item_to_active_list_from_group(session['user_id'], key, groups_id, int(items[key]))
                else:
                    new_quantity = int(items[key]) + item_in_list['active_items_quantity']
                    helpers.update_active_item_quantity(new_quantity, session['user_id'], key, groups_id)


    return redirect(url_for('active_list_data'))



@app.post('/add_from_group_verification')
@helpers.login_required
def add_from_group_verification():

    error = None

    group_id = request.form.get('group_id')
    if not group_id:
        error = 'No group id submitted'

    if not error:
        valid_group = helpers.get_group_by_id_for_user( group_id, session['user_id'])
        if not valid_group:
            error = 'Invalid group'

    if not error:
        groups_items = helpers.get_groups_items_by_group_id(group_id)
        if len(groups_items) == 0:
            error = 'Group is empty'

    if error:
        users_groups = helpers.get_users_groups(session['user_id'])
        users_items = helpers.get_users_items(session['user_id'])
        user_active_items = helpers.get_users_active_items(session['user_id'])
        app.logger.error('error found')
        return jsonify(render_template('/ajax_templates/ajax_index.html', users_groups=users_groups, users_items=users_items, user_active_items=user_active_items, error=error))

    group_name = helpers.get_group_name_by_id(group_id)
    return jsonify(render_template('/ajax_templates/ajax_group_items_verification.html', groups_items=groups_items, group_name=group_name))



@app.route('/login', methods=['GET', 'POST'])
def login():


    if request.method == 'GET':

        if 'user_id' in session:

            session_user_id_valid = helpers.get_user_by_id(session['user_id'])
            if session_user_id_valid is None:
                session.clear()
                return render_template('login.html')
            flash('Logged in!')
            return redirect(url_for('index'))
        else:
            return render_template('login.html')



    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        if username == "" or password == "":
            error = 'Username and or Password was left empty'

        user = helpers.get_user_by_username(username)


        if user is None or not check_password_hash(user['hashed_password'], password):
            error = 'Username and or Password is Incorrect'

        if error is None:

            session.clear()
            session['user_id'] = user['user_id']
            try:
                helpers.update_users_date_last_active(user['user_id'])
                return redirect(url_for('index'))
            except:
                error = 'Failed to update date last active in account info'

        flash(error)
        return redirect(url_for('login'))






@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for('login'))



@app.route("/register", methods=['POST', 'GET'])
def register():

    if request.method == 'GET':
        try:
            if session['user_id'] is not None:
                flash('Must not be logged in to register')
                return redirect(url_for('index'))
        except: pass
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_verification = request.form['password_verification']
        user_email = request.form['email']
        user_email_verification = request.form['email_verification']
        error = None

        if not username or not password or not password_verification:
            error = 'Please fill out all required fields'
        elif not password == password_verification:
            error = 'Passwords do not match'
        elif helpers.get_user_by_username(username):
            error = 'Username already exists'
        elif helpers.get_user_by_email(user_email):
            error = 'Email already in use'
        elif not user_email:
            user_email = None
        elif not user_email == user_email_verification:
            error = 'Email and email verification do not match!'


        if error is None:

            helpers.create_user(username, generate_password_hash(password), user_email, datetime.utcnow())
            if not user_email:
                flash('Please update email for account recovery.')
            flash('Account created, Please Login!')
            return redirect(url_for('login'))

        flash(error)
        return redirect(url_for('register'))



@app.route("/account", methods=['GET', 'POST'])
@helpers.login_required
def account():

    if 'user_id' in session:
        error = None
        user = helpers.get_user_by_id(session['user_id'])

        if user is None:
            error = "Failure retreving user account info please try logging on again"
            flash(error)
            return redirect(url_for('login'))

        helpers.update_users_date_last_active(session['user_id'])
        return render_template("account.html", user=user)



# Not in use, needs to be reimplemented

@app.route("/change_group_name", methods=['GET', 'POST'])
@helpers.login_required
def change_group_name():

    if request.method == 'GET':
        flash('invalid method')
        return redirect(url_for('my_groups'))

    groups_id = request.form.get('groups_id_for_name_change')
    groups_new_name = request.form.get('groups_new_name')

    if not groups_id or not groups_new_name:
        flash('Must select and fill out all of form before submitting')
        return redirect(url_for('my_groups'))

    valid_group = helpers.get_group_by_id_for_user(groups_id, session['user_id'])
    if not valid_group:
        flash('Error Invalid submission')
        return redirect(url_for('my_groups'))

    if valid_group['groups_name'] == groups_new_name:
        flash('New name is the same as old')
        return redirect(url_for('my_groups'))

    helpers.update_groups_name(groups_new_name, groups_id, session['user_id'])
    flash('changed group name')
    return redirect(url_for('my_groups'))

# Not in use, needs to be reimplemented end



@app.route("/delete_account", methods=['GET', 'POST'])
@helpers.login_required
def delete_account():

    db = helpers.get_db()
    if request.method == 'GET':
        helpers.close_db()
        return render_template('delete_account.html')

    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        flash('Must fill out both username and password to DELETE account')
        helpers.close_db()
        return redirect(url_for('delete_account'))

    user = db.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()


    if user is None or username != user['username'] or not check_password_hash(user['hashed_password'], password):
        flash('Error with submitted User Info for deletion. Please log out, log back in, and then try deleting account again.')
        helpers.close_db()
        return redirect(url_for('delete_account'))



    db.execute("DELETE FROM users WHERE user_id = ?", (session['user_id'],))

    db.commit()
    helpers.close_db()

    session.clear()
    flash("Account Deleted")
    return redirect(url_for('login'))



@app.route("/edit_account", methods=['POST', 'GET'])
@helpers.login_required
def edit_account():

    if request.method == 'GET':
        return render_template('edit_account.html')

    flash('post to edit account')    
    return redirect(url_for('account'))



@app.route("/edit_account/<info_to_edit>", methods=['POST', 'GET'])
@helpers.login_required
def edit_account_route(info_to_edit):

    db = helpers.get_db()
    valid_routes = ['username', 'password', 'email']

    if info_to_edit not in valid_routes:
        flash('Invalid info to edit')
        return redirect(url_for('edit_account'))
    
    if request.method == 'GET':
        return render_template('edit_account_route.html', info_to_edit=info_to_edit)

    if request.method == 'POST':

        value_edditing = request.form['value_edditing']
        new_value = request.form['new_value']
        current_username = request.form['current_username']
        current_password = request.form['current_password']

        if not new_value or not current_password or not current_username:
            flash('All Fields must be filled out')
            return redirect(f'/edit_account/{info_to_edit}')

        user = db.execute("SELECT * FROM users WHERE user_id = ?", (session['user_id'],)).fetchone()


        if current_username != user['username'] or not check_password_hash(user['hashed_password'], current_password) or session['user_id'] != user['user_id']:
            flash('Account not verified, please try again')
            helpers.close_db()
            return redirect(f'/edit_account/{info_to_edit}')


        if value_edditing == 'username':
            if user['username'] == new_value:
                flash('Inputed new username is the same as old username')
                helpers.close_db()
                return redirect(f'/edit_account/{info_to_edit}')
            db.execute("UPDATE users SET username = ? WHERE user_id = ?", (new_value, session['user_id'],))
        elif value_edditing == 'password':
            value_edditing = 'hashed_password'
            if check_password_hash(user['hashed_password'], new_value):
                flash('Inputed new password is the same as old password')
                helpers.close_db()
                return redirect(f'/edit_account/{info_to_edit}')
            db.execute("UPDATE users SET hashed_password = ? WHERE user_id = ?", ( generate_password_hash(new_value), session['user_id'],))
        elif value_edditing == 'email':
            value_edditing = 'user_email'
            if user['user_email'] == new_value:
                flash('Inputed new email is the same as old email')
                helpers.close_db()
                return redirect(f'/edit_account/{info_to_edit}')
            try:
                db.execute("UPDATE users SET user_email = ? WHERE user_id = ?", (new_value, session['user_id'],))
            except:
                flash('Unable to add email, email already associated with an account')

        db.commit()
        helpers.close_db()
        return redirect(url_for('account'))



@app.post("/change_quantity_in_group")
@helpers.login_required
def change_quantity_in_group():

    db = helpers.get_db()
    groups_items_id = request.form.get('id')
    value = request.form.get('value')

    valid_groups_item = db.execute("SELECT * FROM groups_items JOIN groups ON groups_items.groups_id = groups.groups_id WHERE groups.user_id = ? AND groups_items.groups_items_id = ?", (session['user_id'], groups_items_id)).fetchone()
    if not valid_groups_item:
        app.logger.error(groups_items_id)
        helpers.close_db()
        return redirect(url_for('my_groups_data'))

    value = int(value)
    if value > 0:
        db.execute("UPDATE groups_items SET quantity = ? WHERE groups_items_id = ?", (value, groups_items_id,))
        db.commit()
        helpers.close_db()
        return redirect(url_for('my_groups_data'))

    else:
        db.execute("DELETE FROM groups_items WHERE groups_items_id = ?", (groups_items_id,))
        db.commit()
        helpers.close_db()
        return redirect(url_for('my_groups_data'))



@app.get('/')
@helpers.login_required
def index():

    error = None
    db = helpers.get_db()
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()

    if not user:
        error = "Failure retreving user account info please try logging on again"
        flash(error)
        helpers.close_db()
        return redirect(url_for('login'))

    db.execute('UPDATE users SET date_last_active = ? WHERE user_id = ?', (datetime.utcnow(), session['user_id']))
    db.commit()
    helpers.close_db()
    return render_template("/index.html")



@app.get("/active_list_data")
@helpers.login_required
def active_list_data():

    db = helpers.get_db()
    users_groups = list(db.execute("SELECT * FROM groups WHERE user_id = ?", (session['user_id'],)))
    users_items = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    user_active_items = list(db.execute("SELECT * FROM user_active_items JOIN item ON user_active_items.item_id = item.item_id WHERE user_active_items.user_id = ? ORDER BY item.item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template('/ajax_templates/ajax_index.html', users_groups=users_groups, users_items=users_items, user_active_items=user_active_items))



@app.post('/active_list_quantity')
@helpers.login_required
def active_list():

    db = helpers.get_db()
    user_active_items_id = request.form.get('id')
    value = request.form.get('value')
    if not value or not user_active_items_id or type(int(value)) is not int or not int(user_active_items_id):
        app.logger.error('error with values')
        return redirect(url_for('active_list_data'))

    value = int(value)
    user_active_items_id = int(user_active_items_id)
    valid_user_active_items = db.execute("SELECT * FROM user_active_items WHERE user_id = ? AND user_active_items_id = ?", (session['user_id'], user_active_items_id)).fetchone()

    if not valid_user_active_items:
        app.logger.error('invalid active item')
        return redirect(url_for('active_list_data'))

    if value > 0:
        db.execute("UPDATE user_active_items SET active_items_quantity = ? WHERE user_active_items_id = ?", (value, user_active_items_id))
        db.commit()
        return redirect(url_for('active_list_data'))

    else:
        db.execute("DELETE FROM user_active_items WHERE user_active_items_id = ?", (user_active_items_id,))
        db.commit()
        return redirect(url_for('active_list_data'))



# BEST TECHNIQUE SO FAR
    
@app.get("/my_items")
@helpers.login_required
def my_items():

    return render_template('my_items.html')



@app.get("/my_items_data")
@helpers.login_required
def my_items_data():

    db = helpers.get_db()
    item = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item))



@app.post("/create_item")
@helpers.login_required
def create_item():

    error = None
    db = helpers.get_db()
    new_item_name = request.form.get('item_name').strip()
    if not new_item_name:
        error = 'Cannot create an item with no name, please try again.'

    if not error:
        item_exists = db.execute("SELECT * FROM item WHERE item_name = ? COLLATE NOCASE AND user_id = ?", (new_item_name, session['user_id'],)).fetchone()
        if item_exists:
            error = 'Item already exists'

    if error:
        item = db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],))
        item = list(item)
        helpers.close_db()
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))

    db.execute("INSERT INTO item (user_id, item_name) VALUES (?, ?)", (session['user_id'], new_item_name, ))
    db.commit()
    helpers.close_db()
    return redirect(url_for('my_items_data'))



@app.post("/change_item_name")
@helpers.login_required
def change_item_name():

    error = None
    db = helpers.get_db()
    item_id = request.form.get('item_id')
    item_new_name = request.form.get('item_new_name').strip()

    if not item_id or not item_new_name:
        error = 'Please select item and choose a new name before submitting. New name must not be empty.'

    if not error:
        valid_item = db.execute("SELECT * FROM item WHERE user_id = ? AND item_id = ?", (session['user_id'], item_id,)).fetchone()
        if not valid_item:
            error = 'Error with item selected, please try again.'

    if not error:
        if valid_item['item_name'] == item_new_name:
            error = 'New item name is the same as old'

        elif not valid_item['item_name'].casefold() == item_new_name.casefold():
            item_exists_with_name = db.execute("SELECT * FROM item WHERE user_id = ? AND item_name = ? COLLATE NOCASE", (session['user_id'], item_new_name)).fetchone()
            if item_exists_with_name:
                error = 'Item with given name exists'

    if error:
        item = db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],))
        item = list(item)
        helpers.close_db()
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))


    db.execute("UPDATE item SET item_name = ? WHERE user_id = ? AND item_id = ?", (item_new_name, session['user_id'], item_id))
    db.commit()
    return redirect(url_for('my_items_data'))



@app.post("/delete_item")
@helpers.login_required
def delete_item():

    error = None
    db = helpers.get_db()
    item_to_delete = request.form.get('item_id')
    if not item_to_delete:
        error = 'Error no item found in submition'
        app.logger.error('No item id')

    if not error:
        valid_item = db.execute("SELECT * FROM item WHERE user_id = ? AND item_id = ?", (session['user_id'], item_to_delete)).fetchone()
        if not valid_item:
            error = 'Error with item submitted'

    if error:
        item = db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],))
        item = list(item)
        helpers.close_db()
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))

    db.execute("DELETE FROM item WHERE user_id = ? AND item_id = ?", (session['user_id'], item_to_delete))
    db.commit()
    return redirect(url_for('my_items_data'))
    
# BEST TECHNIQUE SO FAR END




@app.get("/my_groups")
@helpers.login_required
def my_groups():

    return render_template("/my_groups.html")



@app.get("/my_groups_data")
@helpers.login_required
def my_groups_data():

    db = helpers.get_db()
    groups = list(db.execute("SELECT * FROM groups WHERE user_id = ? ORDER BY groups_name", (session['user_id'],)))
    group_items = list(db.execute("SELECT groups_items.groups_id, item.item_id, item.item_name, groups_items.quantity, item.user_id, groups_items.groups_items_id FROM item JOIN groups_items ON groups_items.item_id = item.item_id WHERE item.user_id = ? ORDER BY item_name", (session['user_id'],)))
    users_items = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items))



@app.post("/create_group")
@helpers.login_required
def create_group():

    error = None
    db = helpers.get_db()
    new_group_name = request.form.get('new_group_name').strip()

    if not new_group_name:
        error = 'Must fill out name to create new group'

    if not error:
        existing_group = db.execute("SELECT * FROM groups WHERE user_id = ? AND groups_name = ? COLLATE NOCASE", (session['user_id'], new_group_name,)).fetchone()
        if existing_group:
            error = 'Group already exists'

    if not error:    
        db.execute("INSERT INTO groups (user_Id, groups_name) VALUES (?, ?)", (session['user_id'], new_group_name))
        db.commit()
        helpers.close_db()
        return redirect(url_for('my_groups_data')) 
    
    groups = list(db.execute("SELECT * FROM groups WHERE user_id = ? ORDER BY groups_name", (session['user_id'],)))
    group_items = list(db.execute("SELECT groups_items.groups_id, item.item_id, item.item_name, groups_items.quantity, item.user_id FROM item JOIN groups_items ON groups_items.item_id = item.item_id WHERE item.user_id = ? ORDER BY item_name", (session['user_id'],)))
    users_items = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))



@app.post("/delete_group")
@helpers.login_required
def delete_group():

    error = None
    db = helpers.get_db()
    group_to_delete = request.form.get('group_to_delete')
    if not group_to_delete:
        error = 'Error with group selected, no value found'

    if not error:
        valid_group = db.execute("SELECT * FROM groups WHERE user_id = ? AND groups_id = ?", (session['user_id'], group_to_delete)).fetchone()
        if not valid_group:
            error = 'Error with group trying to delete'

    if not error:
        db.execute("DELETE FROM groups WHERE user_id = ? AND groups_id = ?", (session['user_id'], group_to_delete))
        db.commit()
        helpers.close_db()
        return redirect(url_for('my_groups_data'))

    groups = list(db.execute("SELECT * FROM groups WHERE user_id = ? ORDER BY groups_name", (session['user_id'],)))
    group_items = list(db.execute("SELECT groups_items.groups_id, item.item_id, item.item_name, groups_items.quantity, item.user_id FROM item JOIN groups_items ON groups_items.item_id = item.item_id WHERE item.user_id = ? ORDER BY item_name", (session['user_id'],)))
    users_items = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))



@app.post("/add_item_to_group")
@helpers.login_required
def add_item_to_group():

    error = None
    db = helpers.get_db()

    selected_group = request.form.get('groups')
    submitted_item = request.form.get('item_to_add')
    inputed_quantity = request.form.get('quantity')



    if not selected_group or not submitted_item or not inputed_quantity:
        error = 'Must select group, item to add and a valid quantity (greater than 0)'

    if not error:
        inputed_quantity = int(inputed_quantity)
        if inputed_quantity <= 0:
            error = 'Must input a valid quantity (greater than 0)'


    if not error:
        users_group = db.execute("SELECT * FROM groups WHERE groups_id = ? and user_id = ?", (selected_group, session['user_id'],)).fetchone()
        if users_group is None:
            error = 'Group submitted is invalid'

    if not error:
        existing_item = db.execute("SELECT * FROM item WHERE item_name = ? COLLATE NOCASE and user_id = ?", (submitted_item, session['user_id'],)).fetchone()
        if not existing_item:
            db.execute("INSERT INTO item (user_id, item_name) VALUES (?, ?)", (session['user_id'], submitted_item,))
            db.commit()
            new_item = db.execute("SELECT * FROM item WHERE item_name = ? COLLATE NOCASE and user_id = ?", (submitted_item, session['user_id'],)).fetchone()
            db.execute('INSERT INTO groups_items (groups_id, item_id, quantity) VALUES (?, ?, ?)', (selected_group, new_item['item_id'], inputed_quantity))
            db.commit()
            helpers.close_db()
            return redirect(url_for('my_groups_data'))
        else:
            item_in_group = db.execute("SELECT * FROM groups_items WHERE groups_id = ? AND item_id = ?", (selected_group, existing_item['item_id'],)).fetchone()
            if not item_in_group:
                db.execute("INSERT INTO groups_items (groups_id, item_id, quantity) VALUES (?, ?, ?)", (selected_group, existing_item['item_id'], inputed_quantity))
                db.commit()
                helpers.close_db()
                return redirect(url_for('my_groups_data'))
            else:
                error = 'Item is in groups already, to change quantity or remove from group, use the quantity input by the item in the group you would like to change'



    groups = list(db.execute("SELECT * FROM groups WHERE user_id = ? ORDER BY groups_name", (session['user_id'],)))
    group_items = list(db.execute("SELECT groups_items.groups_id, item.item_id, item.item_name, groups_items.quantity, item.user_id FROM item JOIN groups_items ON groups_items.item_id = item.item_id WHERE item.user_id = ? ORDER BY item_name", (session['user_id'],)))
    users_items = list(db.execute("SELECT * FROM item WHERE user_id = ? ORDER BY item_name", (session['user_id'],)))
    helpers.close_db()
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))




@app.errorhandler(404)
def page_not_found(error):
    flash('Invalid route')
    return redirect(url_for('index'))



@app.errorhandler(405)
def page_not_found(error):
    flash('Method not allowed for route')
    return redirect(url_for('index'))
