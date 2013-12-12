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

    tmp = pdata["crashing_thread"]["frames"][0]
    lastCall = ""

    if "function" in tmp:
        lastCall += tmp["function"] 
    else:
        lastCall += "N/A"

    if "line" in tmp:
        lastCall += ":" + str(tmp["line"])
    elif "function_offset" in tmp:
        lastCall += ":" + str(tmp["function_offset"])
    elif "module_offset" in tmp:
        lastCall += ":" + str(tmp["module_offset"])
        
    signature = ""
    separator = ""

    i = 0;
    for frame in pdata["crashing_thread"]["frames"]:
        if i > 10:
            break;

        fn = "N/A"
        line = "N/A" 
        if "function" in frame:
            fn = frame["function"]

        if "line" in frame:
            line = str(frame["line"])
        elif "module_offset" in frame:
            line = str(frame["module_offset"])

        signature += separator + fn + ":" + line 

        separator = "-"

        i = i + 1

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
