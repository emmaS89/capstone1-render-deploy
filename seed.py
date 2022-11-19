from app import db
from models import User
db.drop_all()
db.create_all()


data = [{'email' : "test1@gmail.com" , 'password':'Admin!23' , 'name':'hello'},{'email' : "test2@gmail.com" , 'password':'Admin!23' , 'name':'hello1'}
       , {'email' : "test3@gmail.com" , 'password':'Admin!23' , 'name':'hello3'}]

for u in data:
    user = User()
    user.name = u['name']
    user.password = u['password']
    user.email = u['email']
    # add a session in db
    db.session.add(user)
    # save changes in the database
    db.session.commit()

