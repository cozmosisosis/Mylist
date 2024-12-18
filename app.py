import os, logging, sqlite3
from datetime import datetime
from flask import Flask, flash, jsonify, render_template, redirect, session, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import helpers

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SESSION_PERMANENT'] = True





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

    if request.method == 'GET':
        return render_template('delete_account.html')

    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        flash('Must fill out both username and password to DELETE account')
        return redirect(url_for('delete_account'))

    user = helpers.get_user_by_id(session['user_id'])

    if user is None or username != user['username'] or not check_password_hash(user['hashed_password'], password):
        flash('Error with submitted User Info for deletion. Please log out, log back in, and then try deleting account again.')
        return redirect(url_for('delete_account'))

    helpers.delete_user(session['user_id'])
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

        user = helpers.get_user_by_id(session['user_id'])

        if current_username != user['username'] or not check_password_hash(user['hashed_password'], current_password) or session['user_id'] != user['user_id']:
            flash('Account not verified, please try again')
            return redirect(f'/edit_account/{info_to_edit}')


        if value_edditing == 'username':
            if user['username'] == new_value:
                flash('Inputed new username is the same as old username')
                return redirect(f'/edit_account/{info_to_edit}')
            helpers.update_username(session['user_id'], new_value)
        elif value_edditing == 'password':
            value_edditing = 'hashed_password'
            if check_password_hash(user['hashed_password'], new_value):
                flash('Inputed new password is the same as old password')
                return redirect(f'/edit_account/{info_to_edit}')
            helpers.update_user_password(generate_password_hash(new_value), session['user_id'])
        elif value_edditing == 'email':
            value_edditing = 'user_email'
            if user['user_email'] == new_value:
                flash('Inputed new email is the same as old email')
                return redirect(f'/edit_account/{info_to_edit}')
            
            user_with_email = helpers.get_user_by_email(new_value)
            if user_with_email:
                flash('Unable to add email, email already associated with an account')

            else:
                helpers.update_user_email(new_value, session['user_id'])

        return redirect(url_for('account'))



@app.post("/change_quantity_in_group")
@helpers.login_required
def change_quantity_in_group():

    groups_items_id = request.form.get('id')
    value = request.form.get('value')

    valid_groups_item = helpers.get_item_in_group(session['user_id'], groups_items_id)
    if not valid_groups_item:
        return redirect(url_for('my_groups_data'))

    value = int(value)
    if value > 0:
        helpers.update_groups_items_quantity(value, groups_items_id)
        return redirect(url_for('my_groups_data'))

    else:
        helpers.delete_item_from_group(groups_items_id)
        return redirect(url_for('my_groups_data'))



@app.get('/')
@helpers.login_required
def index():

    error = None
    user = helpers.get_user_by_id(session['user_id'])

    if not user:
        error = "Failure retreving user account info please try logging on again"
        flash(error)
        return redirect(url_for('login'))

    helpers.update_users_date_last_active(session['user_id'])
    return render_template("/index.html")



@app.get("/active_list_data")
@helpers.login_required
def active_list_data():

    users_groups = helpers.get_users_groups(session['user_id'])
    users_items = helpers.get_users_items(session['user_id'])
    user_active_items = helpers.get_users_active_items(session['user_id'])
    return jsonify(render_template('/ajax_templates/ajax_index.html', users_groups=users_groups, users_items=users_items, user_active_items=user_active_items))



@app.post('/active_list_quantity')
@helpers.login_required
def active_list():

    user_active_items_id = request.form.get('id')
    value = request.form.get('value')
    if not value or not user_active_items_id or type(int(value)) is not int or not int(user_active_items_id):
        app.logger.error('error with values')
        return redirect(url_for('active_list_data'))

    value = int(value)
    user_active_items_id = int(user_active_items_id)
    valid_user_active_items = helpers.get_active_item_by_active_item_id(session['user_id'], user_active_items_id)

    if not valid_user_active_items:
        app.logger.error('invalid active item')
        return redirect(url_for('active_list_data'))

    if value > 0:
        helpers.update_active_item_quantity_by_active_item_id(value, user_active_items_id)
        return redirect(url_for('active_list_data'))

    else:
        helpers.delete_user_active_item(user_active_items_id)
        return redirect(url_for('active_list_data'))



# BEST TECHNIQUE SO FAR
    
@app.get("/my_items")
@helpers.login_required
def my_items():

    return render_template('my_items.html')



@app.get("/my_items_data")
@helpers.login_required
def my_items_data():

    item = helpers.get_users_items(session['user_id'])
    return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item))



@app.post("/create_item")
@helpers.login_required
def create_item():

    error = None
    new_item_name = request.form.get('item_name').strip()
    if not new_item_name:
        error = 'Cannot create an item with no name, please try again.'

    if not error:
        item_exists = helpers.get_item_by_name_for_user(new_item_name, session['user_id'])
        if item_exists:
            error = 'Item already exists'

    if error:
        item = helpers.get_users_items(session['user_id'])
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))

    helpers.create_item_for_user(new_item_name, session['user_id'])
    return redirect(url_for('my_items_data'))



@app.post("/change_item_name")
@helpers.login_required
def change_item_name():

    error = None
    item_id = request.form.get('item_id')
    item_new_name = request.form.get('item_new_name').strip()

    if not item_id or not item_new_name:
        error = 'Please select item and choose a new name before submitting. New name must not be empty.'

    if not error:
        valid_item = helpers.get_item_by_id_for_user(item_id, session['user_id'])
        if not valid_item:
            error = 'Error with item selected, please try again.'

    if not error:
        if valid_item['item_name'] == item_new_name:
            error = 'New item name is the same as old'

        elif not valid_item['item_name'].casefold() == item_new_name.casefold():
            item_exists_with_name = helpers.get_item_by_name_for_user(item_new_name, session['user_id'])
            if item_exists_with_name:
                error = 'Item with given name exists'

    if error:
        item = helpers.get_users_items(session['user_id'])
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))


    helpers.change_item_name(item_new_name, session['user_id'], item_id)
    return redirect(url_for('my_items_data'))



@app.post("/delete_item")
@helpers.login_required
def delete_item():

    error = None
    item_to_delete = request.form.get('item_id')
    if not item_to_delete:
        error = 'Error no item found in submition'
        app.logger.error('No item id')

    if not error:
        valid_item = helpers.get_item_by_id_for_user(item_to_delete, session['user_id'])
        if not valid_item:
            error = 'Error with item submitted'

    if error:
        item = helpers.get_users_items(session['user_id'])
        return jsonify(render_template('/ajax_templates/ajax_my_items.html', item=item, error=error))

    helpers.delete_item(session['user_id'], item_to_delete)
    return redirect(url_for('my_items_data'))
    
# BEST TECHNIQUE SO FAR END




@app.get("/my_groups")
@helpers.login_required
def my_groups():

    return render_template("/my_groups.html")



@app.get("/my_groups_data")
@helpers.login_required
def my_groups_data():

    groups = helpers.get_users_groups(session['user_id'])
    group_items = helpers.get_users_groups_and_items(session['user_id'])
    users_items = helpers.get_users_items(session['user_id'])
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items))



@app.post("/create_group")
@helpers.login_required
def create_group():

    error = None
    new_group_name = request.form.get('new_group_name').strip()

    if not new_group_name:
        error = 'Must fill out name to create new group'

    if not error:
        existing_group = helpers.get_group_by_name(session['user_id'], new_group_name)
        if existing_group:
            error = 'Group already exists'

    if not error:
        helpers.create_group(session['user_id'], new_group_name)
        return redirect(url_for('my_groups_data')) 

    groups = helpers.get_users_groups(session['user_id'])
    group_items = helpers.get_users_groups_and_items(session['user_id'])
    users_items = helpers.get_users_items(session['user_id'])
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))



@app.post("/delete_group")
@helpers.login_required
def delete_group():

    error = None
    group_to_delete = request.form.get('group_to_delete')
    if not group_to_delete:
        error = 'Error with group selected, no value found'

    if not error:
        valid_group = helpers.get_group_by_id_for_user(group_to_delete, session['user_id'])
        if not valid_group:
            error = 'Error with group trying to delete'

    if not error:
        helpers.delete_users_group(session['user_id'], group_to_delete)
        app.logger.error('deleetet deleetet')
        return redirect(url_for('my_groups_data'))

    groups = helpers.get_users_groups(session['user_id'])
    group_items = helpers.get_users_groups_and_items(session['user_id'])
    users_items = helpers.get_users_items(session['user_id'])
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))



@app.post("/add_item_to_group")
@helpers.login_required
def add_item_to_group():

    error = None
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
        users_group = helpers.get_group_by_id_for_user(selected_group, session['user_id'])
        if users_group is None:
            error = 'Group submitted is invalid'

    if not error:
        existing_item = helpers.get_item_by_name_for_user(submitted_item, session['user_id'])
        if not existing_item:
            helpers.create_item_for_user(submitted_item, session['user_id'])
            new_item = helpers.get_item_by_name_for_user(submitted_item, session['user_id'])
            
            helpers.add_item_to_group(selected_group, new_item['item_id'], inputed_quantity)
            return redirect(url_for('my_groups_data'))
        else:
            item_in_group = helpers.item_in_group_by_item_id(selected_group, existing_item['item_id'])
            if not item_in_group:
                helpers.add_item_to_group(selected_group, existing_item['item_id'], inputed_quantity)
                return redirect(url_for('my_groups_data'))
            else:
                error = 'Item is in groups already, to change quantity or remove from group, use the quantity input by the item in the group you would like to change'



    groups = helpers.get_users_groups(session['user_id'])
    group_items = helpers.get_users_groups_and_items(session['user_id'])
    users_items = helpers.get_users_items(session['user_id'])
    return jsonify(render_template("/ajax_templates/ajax_my_groups.html", groups=groups, group_items=group_items, users_items=users_items, error=error))



@app.route("/favicon.ico")
def favicon():
    return 'favicon placeholder'



@app.errorhandler(404)
def page_not_found(error):
    flash('Invalid route')
    app.logger.error('error 404 route')
    return redirect(url_for('index'))



@app.errorhandler(405)
def page_not_found(error):
    flash('Method not allowed for route')
    app.logger.error('error 405 route')
    return redirect(url_for('index'))
