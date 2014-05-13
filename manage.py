from flask.ext.script import Manager, prompt
from flask.ext.migrate import Migrate, MigrateCommand
from LandingNet import app, db 
from LandingNet import models

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command("db", MigrateCommand)

@manager.command
def run():
    app.run(host='0.0.0.0', debug=True, use_reloader=True)

@manager.command
def add_product(name, version="0.1"):
    if name is None:
        print "Error : No product specified"
        exit(1)

    if version is None:
        print "No version specified. Using 0.1 as version number"

    product = models.Product()
    product.name = name
    product.version = version

    db.session.add(product);
    db.session.commit()

    print "Product %s, version %s added" % (name, version)

@manager.command
def refresh_dump(did):
    from LandingNet import utils
    from LandingNet import config 
    from pprint import pprint
    import os


    dump = models.MiniDump.query.filter_by(id = did).first()
    if dump is None:
        print "Dump %d not found" % (did)

    ret = utils.processMinidump(dump.minidump)

    dump.signature = ret["signature"]
    dump.data = ret["data"]
    dump.name = ret["name"]

    print ret["data"]

    db.session.add(dump)
    db.session.commit()


@manager.command
def setup_demo():
    import shutil
    from LandingNet import utils, config

    symDir = config.DEBUG_SYMBOLS_DIR + "/A644227F100B5F4CB0793515758846170"
    utils.mkdirs(symDir)

    shutil.copyfile("demo/demo.sym", symDir + "/demo.sym")
    shutil.copyfile("demo/demo.dmp", config.MINIDUMP_UPDLOAD_DIR + "/3e3ce301-b6c9-4970-8c54-8abf2964918c.dmp")

    with open('demo/demo.sql', 'r') as f:
        demoSQL = f.readlines()

    for query in demoSQL:
        db.engine.execute(query);

    print "Demo installed"

if __name__ == "__main__":
    manager.run()
