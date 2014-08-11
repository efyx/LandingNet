def mkdirs(path):
    import os, errno
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass

def processMinidump(f):
    import subprocess
    from LandingNet import app 
    import os
    import json
    import hashlib

    data = subprocess.check_output([
            app.config["STACKWALKER"], 
            os.path.join(app.config["MINIDUMP_UPDLOAD_DIR"], f), 
            app.config["BREAKPAD_DEBUG_SYMBOLS_DIR"]])

    pdata = json.loads(data)

    signature = "No crashing thread"
    separator = ""
    lastCall = None

    i = 0;
    if pdata.get("crashing_thread"):
        for frame in pdata["crashing_thread"]["frames"]:
            if i > 10:
                break;

            fn = None
            line = None
            if "function" in frame:
                fn = frame["function"]

            if "line" in frame:
                line = str(frame["line"])
            elif "module_offset" in frame:
                line = str(frame["module_offset"])

            if lastCall is None and fn is not None and line is not None:
                lastCall = "%s:%s" % (fn, line)

            if fn is None:
                fn = "N/A"
            if line is None:
                line = "N/A"

            signature += separator + fn + ":" + line 

            separator = "-"

            i = i + 1
    else:
        lastCall = "N/A : No crashing thread"

    if lastCall is None:
        lastCall = "N/A"

    # Since system info is used to be inserted into database
    # cast int to string
    systemInfo = pdata["system_info"]
    for k,v in systemInfo.iteritems():
        if not isinstance(v, basestring):
            systemInfo[k] = str(v) 
    return dict(
        data = data, 
        signature =  hashlib.md5(signature).hexdigest(), 
        systemInfo = systemInfo,
        name = lastCall)
