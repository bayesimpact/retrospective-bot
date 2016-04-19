from . import db
from datetime import datetime

class Sprint(db.Model):
    ''' Scrum Sprint (Sprint #1, Sprint #2 etc...)
    '''
    __tablename__ = 'sprints'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Unicode())
    creation_date = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return '<Sprint: {}, Created: {}>'.format(self.id, self.creation_date)

    @classmethod
    def get_current_sprint(cls, user_name):
        ''' Return lasted sprint.
        '''
        sprint = Sprint.query.order_by(Sprint.id.desc()).first()
        if not sprint:
            # If no sprint has been started yet, we create one
            sprint = cls.create_new_sprint(user_name)
        return sprint

    @classmethod
    def create_new_sprint(cls, user_name):
        sprint = Sprint(user_name=user_name)
        db.session.add(sprint)
        db.session.commit()
        return sprint

class RetrospectiveItem(db.Model):
    ''' Item logged for a sprint.

    Example:
    "Good: Eva joined the team!"
    "Bad: github was down"
    '''
    __tablename__ = 'retrospective_items'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    sprint_id = db.Column(db.Integer, index=True)
    category = db.Column(db.Unicode(), index=True)
    text = db.Column(db.Unicode())
    user_name = db.Column(db.Unicode())
    creation_date = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return '<RetrospectiveItem: {}: {}, Sprint: {}>'.format(self.category, self.text, self.sprint_id)

    @classmethod
    def get_retrospective_items_for_sprint(cls, sprint):
        ''' Return a dict of retrospective items grouped by categoty

        {
            'good': [item1, item2],
            'bad': [item3, item4],
            'try': [item5],
        }
        '''
        items = RetrospectiveItem.query.filter(RetrospectiveItem.sprint_id == sprint.id)
        return items
