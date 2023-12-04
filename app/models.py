from app import db

'''
    Student attributes:
        - ID
        - Name
        - Email
        - Password
        - Instituion
    
    Group attributes:
        - ID
        - Title {I}
        - Topic {I}
        - Description   {I}
        - Booking date
        - Start date    {I}
        - Start time    {I}
        - Capacity  {I}
        - Location (Seperate object? [FK])
        - Institution   {I}

    Student-Group (JOIN_TABLE):
        - ID
        - Student_ID [FK]
        - Group_ID [FK]
        - Creator (Boolean)

    Location:
        - ID
        - Place
        - Description
        - Image?

    A Student can book onto many groups and a group
    can have many students

'''

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    email = db.Column(db.String(500))
    password = db.Column(db.String(500))
    institution = db.Column(db.String(500))
    user_groups = db.relationship('User_Group', backref='user', lazy='dynamic')

    def __repr__(self):
        return '{}{}{}{}{}'.format(self.id, self.name, self.email, self.password, self.institution)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    topic = db.Column(db.String(500))
    description = db.Column(db.Text)
    startDate = db.Column(db.String(500))
    startTime = db.Column(db.String(500))
    capacity = db.Column(db.Integer)
    attendance = db.Column(db.Integer)
    meetingLocation = db.Column(db.Integer, db.ForeignKey('location.locationId'))
    institution = db.Column(db.String(500))
    user_groups = db.relationship('User_Group', backref='group', lazy='dynamic')

    def __repr__(self):
        return '{}{}{}{}{}{}{}{}'.format(self.id, self.title, self.topic, self.description, self.startDate, self.startTime, self.capacity, self.institution)

class User_Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.Column(db.Boolean)

    def __repr__(self):
        return'{}{}'.format(self.id, self.creator)

class Location(db.Model):
    locationId = db.Column(db.Integer, primary_key=True)
    locationTitle = db.Column(db.String(500))
    locationDescription = db.Column(db.Text)
    accessible = db.Column(db.Boolean)
    groups = db.relationship('Group', backref='location', lazy='dynamic')

    def __repr__(self):
        return'{}{}{}{}'.format(self.locationId,self.locationTitle,self.locationDescription,self.accessible)
    


