from app import create_app,db
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand
from app.models import Role,User

app=create_app()
manager=Manager(app)

migrate=Migrate(app,db)

def make_shell_context():
    return dict(app=app,db=db,role=Role,user=User)

manager.add_command('db',MigrateCommand)
manager.add_command('shell',Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()