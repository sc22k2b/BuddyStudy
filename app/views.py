from flask import render_template, flash, redirect, request, make_response
from app import app, models, db, admin
from .forms import LoginForm, CreateAccountForm, EditUserForm, CreateGroupForm, CreateLocationForm, FilterGroupsForm
import logging
import datetime
import json
from datetime import date, datetime
import sys
# from flask_login import LoginManager

with app.app_context():
    from flask_admin.contrib.sqla import ModelView

    from flask_babel import Babel

    babel = Babel(app)

    from .models import User, Group, User_Group, Location

    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Group, db.session))
    admin.add_view(ModelView(Location, db.session))
    admin.add_view(ModelView(User_Group, db.session))

    # login_manager = LoginManager()
    # login_manager.init_app(app)

    logger = logging.getLogger()
    handle = logging.FileHandler('log.txt')
    logger.addHandler(handle)
'''
    Peer-to-peer study group booking website
'''

# Login


@app.route('/', methods=['GET', 'POST'])
def login():

    app.logger.info("Login page accessed ")
    # Process login input
    form = LoginForm()

    if form.validate_on_submit():
        # First check the email exists within the system
        user = getUser(form.email.data)
        if(user is not None):
            # Check the password matches the email
            if(form.password.data == user.password):
                # Redirect to home page
                response = make_response(redirect('/home'))
                response.set_cookie('userId', str(user.id))
                app.logger.info("Successful login by: %s", user.email)
                return response
            else:
                app.logger.info("Attempted login for: %s", user.email)
                flash("Password is incorrect", "error")
        else:
            app.logger.info("Unrecognised email for: %s", user.email)
            flash("Email is incorrect", "error")

    return render_template('login.html', form=form)


@app.route('/loginSuccess', methods=['GET', 'POST'])
def loginSuccess():
    return redirect('/createAccount')


@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():

    # Take form input and add the new user to the db

    form = CreateAccountForm()

    if form.validate_on_submit():

        # Check the user has used a unique email

        if(getUser(form.email.data) is not None):
            flash("Email already in use", "error")
        else:
            createUser(form.name.data, form.email.data, form.password.data,
                       form.institution.data)
            app.logger.info("New account created for: %s", form.email.data)
            return redirect('/')
    return render_template('createAccount.html', form=form)


@app.route('/editUser', methods=['GET', 'POST'])
def editUser():

    id = loginCheck()

    if(id != -1):
        form = EditUserForm()

        user = getUserById(id)

        if(request.method == 'GET'):
            # Prepopulate the data fields so the user can see what
            # they're changing
            form.name.data = user.name
            form.email.data = user.email
            form.institution.data = user.institution

        if(form.validate_on_submit()):
            # Check to see the new email isn't already in use
            userObject = getUserById(id)
            existingEmail = getUser(userObject.email)

            if(existingEmail is not None):
                if(userObject.id == existingEmail.id):
                    updateUser(id, form.name.data, form.email.data,
                               form.institution.data)
                    flash("Successfully updated", "success")
                    app.logger.info("User: %s updated",
                                     form.email.data)
                else:
                    flash("Email already in use", "error")
            else:
                updateUser(id, form.name.data, form.email.data,
                           form.institution.data)
                app.logger.info("User: %s updated",
                                     form.email.data)
    else:
        return redirect('/')

    return render_template('userUpdate.html', form=form)


@app.route('/home')
def homepage():

    id = loginCheck()

    if(id != -1):
        # If the user is logged in get their name
        userName = getUserById(id).name
    else:
        return redirect('/')

    return render_template('home.html', userName=userName)


@app.route('/viewGroups/institution=<inst>/accessible=<accessible>/topic=<topic>', methods = ['GET', 'POST'])
def viewGroups(inst, accessible, topic):

    id = loginCheck()

    app.logger.info("View group page accessed")

    if(id != -1):

        allUserBookedSessions(id)

        allUserCreatedSessions(id)

        form = FilterGroupsForm()

        if(request.method == 'GET'):

            # Prefill to what the user inputted on the previous page
            form.topic.data = topic

            if(inst == "True"):
                form.institution.data = True

            if(accessible == "True"):
                form.accessible.data = True

        if(form.validate_on_submit()):

            # Set up the new URL to redirect the user to
            inst = form.institution.data
            accessible = form.accessible.data
            topic = form.topic.data
            redirectURL = "/viewGroups/institution=" + str(inst) +"/accessible=" + str(accessible) + "/topic=" + topic
            return redirect(redirectURL)

        # Check if the user requested to filter on the previous page
        if(inst != "False" or accessible != "False" or topic != "None"):
            groups = None
            # Sort the groups as selected
            if(inst != "False"):
                user = models.User.query.filter_by(id=id).first()
                groups = institutionSort(user.institution, groups)

            if(accessible != "False"):
                groups = accessibleSort(groups)

            if(topic != "None"):
                groups = topicSort(topic, groups)
        else:
            groups = allCurrentGroups()
    else:
        return redirect('/')

    # Filter out any groups that the user won't be able to pick
    groups = allCurrentPickableGroups(groups, id)

    return render_template('groupsView.html', groups=groups, userId=id,
                           form=form)


@app.route('/book', methods=['POST'])
def book():
    data = json.loads(request.data)
    ids = data.get('ids')
    idSplit = ids.split(',')
    groupId = idSplit[0]
    userId = idSplit[1]

    full=False
    group = models.Group.query.filter_by(id=groupId).first()
    # Check the user hasn't already booked
    user_group = models.User_Group.query.filter_by(user_id=userId,
                                                   group_id=groupId).first()
    if(user_group is None):
        # Check there still is space for another booking
        if(group.attendance < group.capacity):
            attendance = createAJAXBooking(groupId, userId)
            app.logger.info("User %s booked onto session %s",
                            userId, groupId)
        else:
            full=True
            attendance = group.attendance
    else:
        if(user_group.creator is False):
            attendance = deleteBooking(groupId, userId)
            app.logger.info("User %s deleted group booking %s",
                            userId, groupId)
        else:

            attendance = getGroup(groupId)['attendance']

    return json.dumps({'status': 'OK', 'attendance': attendance, 'full': full})


@app.route('/createGroup', methods=['GET', 'POST'])
def groupCreate():

    id = loginCheck()

    if(id != -1):
        form = CreateGroupForm()
        locationForm = CreateLocationForm()

        if(form.validate_on_submit()):

            # Split the date and time into component parts
            # (Year, Month, Day, Hour, Minute)
            dateSplit = form.startDate.data.split('-')
            timeSplit = form.startTime.data.split(':')

            # Create a datetime object
            userDate = datetime(int(dateSplit[0]), int(dateSplit[1]),
                                int(dateSplit[2]), int(timeSplit[0]),
                                int(timeSplit[1]))

            # Retrieve the current time
            currentDateTime = datetime.now()

            # Check the user inputted time/date is not before the current time
            # as this would make it invalid
            if(userDate <= currentDateTime):
                flash("The date and time you have entered is before the current time", "error")
            else:
                if(locationForm.locationTitle.data is not None and
                   locationForm.locationDescription.data is not None and
                   locationForm.accessible.data is not None):
                    # Create a new location record and retrieve the object so
                    # the new id for the location can be utilsied
                    location = createLocation(locationForm.locationTitle.data,
                                              locationForm.locationDescription.data,
                                              locationForm.accessible.data)

                    app.logger.info("New location: %s created",
                                    locationForm.locationTitle.data)
                    # Create a new group
                    createGroup(id, form.title.data, form.topic.data,
                                form.description.data, form.startDate.data,
                                form.startTime.data, form.capacity.data,
                                location.locationId, form.institution.data)

                    app.logger.info("New group: %s created",
                                    form.title.data)

                    flash("Group created", "success")
                else:
                    flash("The location needs a title, description and accessability type", "error")
    else:
        return redirect('/')

    return render_template('groupCreate.html', form=form,
                           locationForm=locationForm)


@app.route('/viewLocation/locationId=<id>')
def viewLocation(id):

    userId = loginCheck()

    if(userId != -1):
        with app.app_context():
            location = models.Location.query.filter_by(locationId=id).first()
            title = location.locationTitle
            description = location.locationDescription
            accesssible = location.accessible

            app.logger.info("Location: %s viewed by user %s",
                                    title, userId)
    else:
        return redirect('/')

    return render_template('locationView.html', title=title,
                           description=description, accessible=accesssible)


@app.route('/viewUserGroups', methods=['GET', 'POST'])
def viewUserGroups():

    id = loginCheck()

    if(id != -1):
        createdSessions = allUserCreatedSessions(id)
        bookedSessions = allUserBookedSessions(id)

        app.logger.info("User: %s checked their groups", id)
    else:
        return redirect('/')

    return(render_template('userBookings.html',
                           createdSessions=createdSessions,
                           bookedSessions=bookedSessions))


@app.route('/viewCurrentUserGroups', methods=['GET', 'POST'])
def viewCurrentUserGroups():

    id = loginCheck()

    if(id != -1):
        createdSessions = allCurrentUserCreatedSessions(id)
        bookedSessions = allCurrentUserBookedSessions(id)

        app.logger.info("User: %s checked their groups", id)
    else:
        return redirect('/')

    return(render_template('userCurrentBookings.html',
                           createdSessions=createdSessions,
                           bookedSessions=bookedSessions))


@app.route('/deleteBooking/groupId=<id>', methods=['GET', 'POST'])
def deleteUserBooking(id):

    userId = loginCheck()

    if(id != -1):
        deleteBooking(id, userId)
        app.logger.info("Booking: %s deleted by %s",
                        id, userId)
    else:
        redirect('/')

    return(redirect('/viewCurrentUserGroups'))


@app.route('/deleteGroup/groupId=<id>', methods=['GET', 'POST'])
def deleteWholeGroup(id):

    userId = loginCheck()

    if(userId != -1):
        deleteGroup(id)
        app.logger.info("Group: %s deleted by %s",
                        id, userId)
    else:
        redirect('/')

    return(redirect('/viewCurrentUserGroups'))


@app.route('/updateGroup/groupId=<id>', methods=['GET', 'POST'])
def updateGroup(id):

    userId = loginCheck()

    if(loginCheck != -1):
        # Only allow the user who created the group change it
        if(getCreator(userId, id)):
            group = getGroup(id)

            form = CreateGroupForm()
            locationForm = CreateLocationForm()

            if(request.method == 'GET'):
                # Prefill the information the user is updating
                # so they know what they're changing
                form.title.data = group['title']
                form.topic.data = group['topic']
                form.description.data = group['description']
                form.startDate.data = group['startDate']
                form.startTime.data = group['startTime']
                form.capacity.data = group['capacity']
                locationForm.locationTitle.data = group['locationTitle']
                locationForm.locationDescription.data = group['locationDescription']
                locationForm.accessible.data = group['accessible']
                form.institution.data = group['institution']

            if(form.validate_on_submit()):

                # Check the date is correct
                if(dateChecker(form.startDate.data, form.startTime.data)):

                    # Update the group with the information in the form
                    updateGroup(id, form.title.data, form.topic.data,
                                form.description.data,
                                form.startDate.data,
                                form.startTime.data, form.capacity.data,
                                group['meetingLocation'],
                                form.institution.data,
                                locationForm.locationTitle.data,
                                locationForm.locationDescription.data,
                                locationForm.accessible.data)

                    flash("Group successfully updated", "success")
                    app.logger.info("Group: %s updated by %s",
                        id, userId)

                else:
                    flash("The date and time you have entered is before the current time", "error")

        else:
            return redirect('/home')
    else:
        return redirect('/')

    return(render_template('groupUpdate.html', form=form,
                           locationForm=locationForm))


@app.route('/viewGroup/groupId=<id>', methods=['GET', 'POST'])
def viewGroup(id):

    return(render_template('groupView.html', group=getGroup(id),
                           users=allUserToGroup(id)))
# ------------------ Get functions ------------------


def getUser(userEmail):

    with app.app_context():

        # Search through all users to see if they already exist

        for i in models.User.query.all():

            if(i.email == userEmail):
                return i

        # If the loop is exited and there has been no user found
        # The user does not exist and therefore return None

        return None


def getUserById(userId):

    with app.app_context():

        # Loop through all the records to find the matching
        # id and return the object

        for i in models.User.query.all():

            if(int(i.id) == int(userId)):
                return i

        return None


def getLocationId(title, description, accessible):

    with app.app_context():

        # Loop through all the location records and get
        # the id that exactly matches the attributes

        for i in models.Location.query.all():

            if(i.locationTitle == title and
               i.locationDescription == description and
               i.accessible == accessible):
                return i.locationId


def getLocation(id):

    # Get the correpsonding location to the id
    # Load the data into a dictionary
    with app.app_context():
        location = models.Location.query.filter_by(locationId=id).first()
        location_dictionary = [{'id': location.locationId,
                                'title': location.locationTitle,
                                'description': location.locationDescription}]

        return location_dictionary


def getGroup(id):

    with app.app_context():
        g = models.Group.query.filter_by(id=id).first()

        location = models.Location.query.filter_by(locationId=g.meetingLocation).first()

        dictionary = {'id': g.id, 'title': g.title, 'topic': g.topic,
                      'description': g.description, 'startDate': g.startDate,
                      'startTime': g.startTime, 'capacity': g.capacity,
                      'meetingLocation': g.meetingLocation,
                      'locationTitle': location.locationTitle,
                      'locationDescription': location.locationDescription,
                      'accessible': location.accessible,
                      'institution': g.institution,
                      'attendance': g.attendance}

        return dictionary


def getCreator(userId, groupId):

    with app.app_context():

        # Find if the user_group exists
        # Check if the user is the creator

        ug = models.User_Group.query.filter_by(user_id=userId, group_id=groupId).first()
        return ug.creator


# -------------------------------------------------

# ---------------------- Get all objects -------------

def allCurrentGroups():

    with app.app_context():

        # Set up an array to hold all the dictionaries
        # of each object

        dictionaryArray = []

        for g in models.Group.query.all():

            # Retrieve the correpsonding location so the title can be used
            location = models.Location.query.filter_by(locationId=g.meetingLocation).first()

            if(location is not None):
                # ! Check the date and time so expired groups aren't included !
                if(dateChecker(g.startDate, g.startTime)):

                    if(dateSoon(g.startDate, g.startTime)):
                        soonDate = True
                    else:
                        soonDate = False
                    dictionary = [{'id': g.id, 'title': g.title,
                                   'topic': g.topic,
                                   'description': g.description,
                                   'startDate': g.startDate,
                                   'startTime': g.startTime,
                                   'capacity': g.capacity,
                                   'meetingLocation': g.meetingLocation,
                                   'locationTitle': location.locationTitle,
                                   'institution': g.institution,
                                   'attendance': g.attendance,
                                   'soonDate': soonDate}]

                    dictionaryArray.append(dictionary)

    return dictionaryArray


def allUserBookedSessions(id):

    with app.app_context():

        bookedSessionArray = []

        # Loop through all the user_group records
        for i in models.User_Group.query.all():

            # If the ids are equal then add the group to the associated array
            if(i.user_id == int(id) and i.creator is False):
                # Get the corresponding group and location obejcts
                g = models.Group.query.filter_by(id=i.group_id).first()

                if(g is not None):
                    location = models.Location.query.filter_by(locationId=g.meetingLocation).first()
                
                    if(location is not None):
                        # Load into a dictionary
                        dictionary = [{'id': g.id, 'title': g.title,
                                       'topic': g.topic,
                                       'description': g.description,
                                       'startDate': g.startDate,
                                       'startTime': g.startTime,
                                       'capacity': g.capacity,
                                       'meetingLocation': g.meetingLocation,
                                       'locationTitle': location.locationTitle,
                                       'institution': g.institution,
                                       'attendance': g.attendance}]

                        # Add the dictionary to the array
                        bookedSessionArray.append(dictionary)

    return bookedSessionArray


def allUserCreatedSessions(id):

    with app.app_context():

        createdSessionArray = []

        # Loop through all the user_group records
        for i in models.User_Group.query.all():

            # If the ids are equal then add the group to the associated array
            if(i.user_id == int(id) and i.creator is True):
                # Get the corresponding group and location obejcts
                g = models.Group.query.filter_by(id=i.group_id).first()

                location = models.Location.query.filter_by(locationId=g.meetingLocation).first()

                if(location is not None):
                    # Load into a dictionary
                    dictionary = [{'id': g.id, 'title': g.title,
                                   'topic': g.topic,
                                   'description': g.description,
                                   'startDate': g.startDate,
                                   'startTime': g.startTime,
                                   'capacity': g.capacity,
                                   'meetingLocation': g.meetingLocation,
                                   'locationTitle': location.locationTitle,
                                   'institution': g.institution,
                                   'attendance': g.attendance}]

                    # Add the dictionary to the array
                    createdSessionArray.append(dictionary)

    return createdSessionArray


def allCurrentUserBookedSessions(id):

    with app.app_context():

        bookedSessionArray = []

        # Loop through all the user_group records
        for i in models.User_Group.query.all():

            # If the ids are equal then add the group to the associated array
            if(i.user_id == int(id) and i.creator is False):
                # Get the corresponding group and location obejcts
                g = models.Group.query.filter_by(id=i.group_id).first()

                if(g is not None):
                    location = models.Location.query.filter_by(locationId=g.meetingLocation).first()
                
                    if(location is not None):
                        if(dateChecker(g.startDate, g.startTime)):

                            if(dateSoon(g.startDate, g.startTime)):
                                soonDate = True
                            else:
                                soonDate = False
                            dictionary = [{'id': g.id, 'title': g.title,
                                           'topic': g.topic,
                                           'description': g.description,
                                           'startDate': g.startDate,
                                           'startTime': g.startTime,
                                           'capacity': g.capacity,
                                           'meetingLocation': g.meetingLocation,
                                           'locationTitle': location.locationTitle,
                                           'institution': g.institution,
                                           'attendance': g.attendance,
                                           'soonDate': soonDate}]

                            bookedSessionArray.append(dictionary)

    return bookedSessionArray


def allCurrentUserCreatedSessions(id):

    with app.app_context():

        createdSessionArray = []

        # Loop through all the user_group records
        for i in models.User_Group.query.all():

            # If the ids are equal then add the group to the associated array
            if(i.user_id == int(id) and i.creator is True):
                # Get the corresponding group and location obejcts
                g = models.Group.query.filter_by(id=i.group_id).first()

                location = models.Location.query.filter_by(locationId=g.meetingLocation).first()

                if(location is not None):
                    # Load into a dictionary
                    if(dateChecker(g.startDate, g.startTime)):

                        if(dateSoon(g.startDate, g.startTime)):
                            soonDate = True
                        else:
                            soonDate = False

                        dictionary = [{'id': g.id,
                                       'title': g.title, 'topic': g.topic,
                                       'description': g.description,
                                       'startDate': g.startDate,
                                       'startTime': g.startTime,
                                       'capacity': g.capacity,
                                       'meetingLocation': g.meetingLocation,
                                       'locationTitle': location.locationTitle,
                                       'institution': g.institution,
                                       'attendance': g.attendance,
                                       'soonDate': soonDate}]

                        # Add the dictionary to the array
                        createdSessionArray.append(dictionary)

    return createdSessionArray


def allUserToGroup(groupId):

    users = []
    # Loop through all the user_groups related to the group
    # and find each user and add it to the list
    for i in models.User_Group.query.filter_by(group_id=groupId):

        user = models.User.query.filter_by(id=i.user_id).first()
        users.append(user.name)

    return users

def allCurrentPickableGroups(groups, userId):

    pickableGroups = []

    for group in groups:
        # Get the user_group related to both the user and group
        user_group = models.User_Group.query.filter_by(group_id=group[0].get('id'), user_id=userId).first()

        # Check the user isn't already booked on and that there is
        # still space 
        if(user_group is None):

            if(int(group[0].get('attendance')) < int(group[0].get('capacity'))):

                pickableGroups.append(group)

    return pickableGroups


# ---------------- Create methods -------------

def createUser(inputName, inputEmail, inputPassword, inputInstitution):

    # Take the users details and add them to an object to add
    # to the database

    user = models.User(name=inputName, email=inputEmail,
                       password=inputPassword, institution=inputInstitution)
    db.session.add(user)
    db.session.commit()


def createAJAXBooking(groupId, userId):

    # First make the booking with the specific user who booked it
    user_group = models.User_Group(group_id=groupId,
                                   user_id=userId, creator=False)
    db.session.add(user_group)
    db.session.commit()

    # Increment the attendance as now there is another person attending
    group = models.Group.query.get(groupId)
    group.attendance = group.attendance + 1
    db.session.commit()

    return group.attendance


def createGroup(userId, title, topic, description, startDate, startTime,
                capacity, meetingLocation, institution):

    # Create the group record
    group = models.Group(title=title, topic=topic, description=description,
                         startDate=startDate, startTime=startTime,
                         capacity=capacity, attendance=1,
                         meetingLocation=meetingLocation,
                         institution=institution)
    db.session.add(group)
    db.session.commit()

    # Add the creator of the group to the booking (as the creator)
    group_user = models.User_Group(user_id=userId, group_id=group.id,
                                   creator=True)
    db.session.add(group_user)
    db.session.commit()


def createLocation(title, description, accessible):

    # Add a new location record to the database
    location = models.Location(locationTitle=title,
                               locationDescription=description,
                               accessible=accessible)
    db.session.add(location)
    db.session.commit()

    return location

# ------------------- Update methods ---------------


def updateUser(id, name, email, institution):

    with app.app_context():

        # Find the entry to update and change the details
        # Any details the user kept the same will be rewritten

        user = models.User.query.filter_by(id=id).first()
        user.name = name
        user.email = email
        user.institution = institution
        db.session.commit()


def updateGroup(groupId, title, topic, description, startDate, startTime,
                capacity, meetingLocation, institution, locationTitle,
                locationDescription, locationAccessible):

    with app.app_context():

        group = models.Group.query.filter_by(id=groupId).first()

        location = models.Location.query.filter_by(locationId=meetingLocation).first()

        group.title = title
        group.topic = topic
        group.description = description
        group.startDate = startDate
        group.startTime = startTime
        group.capacity = capacity
        group.institution = institution

        location.locationTitle = locationTitle
        location.locationDescription = locationDescription
        location.accessible = locationAccessible

        db.session.commit()


# ---------------------- Delete methods ------------------

def deleteBooking(groupId, userId):

    with app.app_context():

        # Find the booking the user is trying to undo and delete it
        user_group = models.User_Group.query.filter_by(group_id=groupId, user_id=userId).first()
        db.session.delete(user_group)
        db.session.commit()

        # Decrement the attendance as a user is no longer attending
        group = models.Group.query.get(groupId)
        group.attendance = group.attendance - 1
        db.session.commit()

        return group.attendance


def deleteGroup(id):

    # First delete all associated bookngs with the group
    for i in models.User_Group.query.filter_by(group_id=id):

        db.session.delete(i)

    db.session.commit()

    # Delete the group
    group = models.Group.query.get(id)
    db.session.delete(group)
    db.session.commit()

# ---------------------- Sort methods -------------------------


def institutionSort(inst, allGroups):

    if(allGroups is None):
        allGroups = allCurrentGroups()

    instGroups = []

    for i in range(len(allGroups)):

        # Get the specific group at this index
        group = allGroups[i]
        # Check to see if the institutions match
        if(inst == group[0].get("institution")):
            # Filter out any groups that are not part of the instituion
            instGroups.append(group)

    return instGroups


def topicSort(topic, allGroups):

    if(allGroups is None):
        allGroups = allCurrentGroups()

    topicGroups = []

    for i in range(len(allGroups)):

        # Get the specific group at index i]
        group = allGroups[i]

        # Filter out any groups that do not cover a certain topic
        if(topic == group[0].get("topic")):

            topicGroups.append(group)

    return topicGroups


def accessibleSort(allGroups):

    if(allGroups is None):
        allGroups = allCurrentGroups()

    accessibleGroups = []

    for i in range(len(allGroups)):

        # Get the specific group at index i
        group = allGroups[i]

        l = models.Location.query.filter_by(locationId = group[0].get("meetingLocation")).first()
        # Filter out any unaccessible groups
        if(l.accessible is True):

            accessibleGroups.append(group)

    return accessibleGroups


def attendanceSortAscending(groups):

    # Quicksort to sort groups by number of attendants

    if(groups is None):
        allGroups = allCurrentGroups()
    else:
        allGroups = groups

    # Arrays to hold the dictionary of each value
    # depending if they are less, equal or above the pivot
    lessThan = []
    equal = []
    greaterThan = []

    group = allGroups[0]
    pivot = group['attendance']
    for i in allGroups:

        # Loop through all groups and determine if the attendnace
        # is above or below the attendance of the pivot
        compareGroup = allGroups[i]
        if(compareGroup['attendance'] < pivot):
            lessThan.append(compareGroup)
        elif(compareGroup['attendance'] == pivot):
            equal.append(compareGroup)
        elif(compareGroup['attendance'] == pivot):
            greaterThan.append(compareGroup)

        # Recursivley sort the divided arrays
        return attendanceSortAscending(lessThan) + equal + attendanceSortAscending(greaterThan)

# ----------------------- Other methods ----------------------


def dateChecker(date, time):
    # Split the date and time into component parts
    # (Year, Month, Day, Hour, Minute)
    dateSplit = date.split('-')
    timeSplit = time.split(':')

    # Create a datetime object
    userDate = datetime(int(dateSplit[0]), int(dateSplit[1]),
                        int(dateSplit[2]),
                        int(timeSplit[0]), int(timeSplit[1]))

    # Retrieve the current time
    currentDateTime = datetime.now()

    # Check the user inputted time/date is not before the current time
    # as this would make it invalid
    if(userDate <= currentDateTime):
        return False
    else:
        return True


def dateSoon(date, time):

    # Split the date and time into component parts
    # (Year, Month, Day, Hour, Minute)
    dateSplit = date.split('-')
    timeSplit = time.split(':')

    # Create a datetime object
    userDate = datetime(int(dateSplit[0]),
                        int(dateSplit[1]), int(dateSplit[2]),
                        int(timeSplit[0]), int(timeSplit[1]))

    # Retrieve the current time
    currentDateTime = datetime.now()

    # Check if the date is today
    if(userDate.day == currentDateTime.day):
        return True
    else:
        return False


# --------------------- Login functions ---------------------

def loginCheck():

    # Get the cookie

    id = request.cookies.get('userId')

    # Check to see the cookie exist as this means a user
    # actually logged in
    if(id is not None):
        return int(id)
    else:
        return -1