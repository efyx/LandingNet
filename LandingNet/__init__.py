from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from LandingNet import utils 
from LandingNet.HttpException import InvalidUsage

app = Flask(__name__)
app.config.from_object('LandingNet.config')
db = SQLAlchemy(app)

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)

@app.route("/")
def index():
    from sqlalchemy import func
    from LandingNet.models import Crashs
    # TODO : Update this to query MiniDump and join with product and stacktrace
    traces = Crashs.query.order_by(Crashs.updated.desc()).limit(10).all()
    return render_template("index.html", traces=traces)

@app.route("/crash/<int:cid>")
def crash(cid):
    from LandingNet.models import Crashs, MiniDump
    import json
    crash = Crashs.query.filter_by(id = cid).first_or_404()
    dumps = MiniDump.query.filter_by(crash_id = crash.id).order_by(MiniDump.timestamp.desc()).all()
    if len(dumps) == 0:
        raise InvalidUsage("No dumps for trace " + str(cid))

    crash.data = json.loads(dumps[0].data)

    return render_template("crash.html", crash=crash, dumps=dumps)
    
@app.route("/minidump/<int:did>")
def minidump(did):
    from LandingNet.models import MiniDump
    import json
    dump = MiniDump.query.filter_by(id = did).first_or_404()
    dump.data = json.loads(dump.data)
    return render_template("minidump.html", dump=dump)

@app.route("/upload_symbols", methods=["POST"])
def uploadSymbols():
    from flask import request
    from werkzeug import secure_filename
    import os

    if "symbols" not in request.files:
        raise InvalidUsage("Missing symbols file")

    fields = ["revision", "arch", "system"]
    for field in fields:
        if field not in request.form:
            raise InvalidUsage("Missing field " + field)

    file = request.files["symbols"]
    ext = file.filename.rsplit(".", 1)[1]

    symFile = None
    debugFile = None
    if ext == "zip":
        import zipfile
        import tempfile
        zfile = zipfile.ZipFile(file)
        zsymFile = None

        for name in zfile.namelist():
            (dirname, filename) = os.path.split(name)
            zext = filename.rsplit(".", 1)[1]
            if zext == "sym" and symFile is None:
                symFile = tempfile.TemporaryFile(dir="/home/efyx/dev/")
                symFile.write(zfile.read(name))
                symFile.seek(0)
            elif zext == "debug" and debugFile is None:
                debugFile = tempfile.TemporaryFile(dir="/home/efyx/dev/")
                debugFile.write(zfile.read(name))
                debugFile.seek(0)

        if symFile is None:
            raise InvalidUsage("No .sym file found in archive")
    elif ext == "sym":
        symFile = file
    else:
        raise InvalidUsage("Wrong symbols format, .sym or .zip extension expected")


    # Debug symbols need to be stored with a specific directory structure :
    # DEBUG_SYMBOLS_DIR/<exec name>/<hash>/<exec name>.sym

    # The first line of the sym file give the needed information
    # eg : MODULE Linux x86_64 6EDC6ACDB282125843FD59DA9C81BD830 test
    #                          |> Hash                           |> Exec name
    tmp = symFile.readline()
    tmp = tmp.split(" ")
    symFile.seek(0)
    execName = tmp[4].strip()

    path = os.path.join(app.config["BREAKPAD_DEBUG_SYMBOLS_DIR"], execName, tmp[3].strip())
    utils.mkdirs(path)

    with open(os.path.join(path, tmp[4].strip() + ".sym"), "w") as handle:
        handle.write(symFile.read())

    symFile.close()

    if debugFile is not None:
        name = "%s_%s_%s_%s.debug" % (execName, request.form["system"], request.form["arch"], request.form["revision"])
        with open(os.path.join(app.config["DEBUG_SYMBOLS_DIR"], name), "w") as handle:
            handle.write(debugFile.read())

        debugFile.close()
            
    return render_template("upload_success.html")

@app.route("/submit", methods=["POST"])
def submit():
    from flask import request
    from LandingNet import models
    from werkzeug import secure_filename
    import os
    import uuid

    minidumpArg = ""
    if "minidump" in request.files:
        minidumpArg = "minidump"
    elif "upload_file_minidump" in request.files: # Special case for OSX breakpad crash reporter
        minidumpArg = "upload_file_minidump"
    else:
        raise InvalidUsage("No minidump specified")

    file = request.files[minidumpArg]

    if file is None or file.filename.rsplit(".", 1)[1] != "dmp":
        raise InvalidUsage("Wrong dump format")

    if "build" not in request.form:
        raise InvalidUsage("Build is not specified")

    if "product" not in request.form:
        raise InvalidUsage("Product is not specified")

    if "version" not in request.form:
        raise InvalidUsage("Version is not specified")

    product = models.Product.query.filter_by(version=request.form["version"], name=request.form["product"]).first()
    if product is None:
        raise InvalidUsage("Product %s version %s not found" % (request.form["product"], request.form["version"]))

    filename = str(uuid.uuid4()) + ".dmp"
    file.save(os.path.join(app.config["MINIDUMP_UPDLOAD_DIR"], filename))

    ret = utils.processMinidump(filename)

    crash = models.Crashs.query.filter_by(signature = ret["signature"]).first()
    if crash is None:
        crash = models.Crashs()
        crash.count = 0
        crash.name = ret["name"]
        crash.signature = ret["signature"]
        db.session.add(crash)
        db.session.commit()

    md = models.MiniDump()
    md.crash_id = crash.id
    md.product_id = product.id
    md.signature = ret["signature"]
    md.minidump = filename
    md.build = request.form["build"]
    md.data = ret["data"]
    md.system_info = ret["systemInfo"]
    md.name = ret["name"]

    crash.count = crash.count + 1

    db.session.add(md)
    db.session.commit()

    return render_template("upload_success.html")

@app.errorhandler(InvalidUsage)
def handleInvalidUsage(error):
    from flask import jsonify
    return "ERROR : " + error.message + "\r\n", 422

@app.template_filter("datetime")
def format_datetime(value):
    from babel.dates import format_datetime
    return format_datetime(value, "YYYY-MM-dd 'at' HH:mm:ss")

@app.template_filter("normalizeFilename")
def normalizeFilename(value):
    filename = "N/A"

    if isinstance(value, basestring) :
        filename = value.rsplit("/", 1)[1]

    return filename

@app.template_filter("normalizeFrame")
def normalizeFrame(frame):
    if frame.get("function"):
        return frame["function"] + ":" + str(frame["line"])
    else:
        return "N/A"
