# LandingNet
LandingNet is a lightweight crash collector for Breakpad. It's written in python using flask. It use PostgreSQL database.

# Setting up LandingNet 

## Requirements
- Python >= 2.7
- PostgreSQL >= 9.1 (with HSTORE extension)
- Breakpad
- Minidump stackwalker

### Build breakpad and minidump stackwalker
Minidump stackwalker is a small executable that will read a minidump file and extract all of his information in a JSON format. 
It use parts from google breakpad, so you need to build google-breakpad too.

*Run the following command from the root of LandingNet repo*

- Download and build google breakpad

```bash
cd third-party
svn co http://google-breakpad.googlecode.com/svn/trunk/ google-breakpad
mkdir obj-breakpad/
cd obj-breakpad/ 
../google-breakpad/configure && make
cd ../
```

- Download and build minidump-stackwalk json

```bash
hg clone http://hg.mozilla.org/users/tmielczarek_mozilla.com/minidump-stackwalk -b json
cd minidump-stackwalk
make
cp stackwalker ../../bin/
cd ../../
```

### Python dependencies
You can install needed dependencies through pip. Before doing so it's recommanded (but not mandatory) to create a python virtual env : 

```bash
virtualenv .venv
source .venv/bin/activate
```

Install required python packages : 
```bash
pip install -r requirements.txt
```

## Configure LandingNet
Copy the file in `LandingNet/config.sample.py` to `LandingNet/config.py` and edit as needed 

Then run the setup script to setup the database : 

```bash
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

Additionaly you might want to fill the database with a demo application and minidumps (for testing purpose). To do so, run the following : 
```bash
python manage.py setup_demo
```

## Try it !
Once you are ready, you can run LandingNet with flask default web server, using : 

```bash
python manage.py run
```

If you installed the demo, you can point your browser to http://localhost:5000 and see some processed minidumps

# Using LandingNet
The first things you want to do is to : 

- Add a product 
- Export debug symbols from your application and submit it to LandingNet
- Get a minidump from a crash in your program and submit it to LandingNet
- Look at the processed minidump in LandingNet

## Adding a product
```bash
python manage.py add_product <product_name> [<product_version>]
```

## Submitting debug symbols and minidumps
LandingNet provide two endpoints : 

- `/upload_symbols (POST)` : for submitting debug symbols
- `/submit (POST)` : for submitting minidumps

### Debug symbols
Debug symbols are used by stackwalk executable to add filename, functions and line numbers to stack trace. 

You can use curl to upload debug symbols : 

```bash
curl -F symbols=@demo/demo.sym http://localhost:5000/upload_symbols
```

**Endpoint arguments :**
```
/upload_symbols
    symbols  : Can be a breakpad .sym file or a zip file containing breakpad .sym file and (optionally) debug symbols for your application (the file must end with .debug)
    build : Build number (Can be any string up to 40 character)
    arch : The architecture of the uploaded symbols
    system : The system of the uploaded symbols
```

*The fields build, arch and system are used to store the debug symbols with a unique name debug-symbols/<exec name>_<system>_<arch>_<build>.debug so later you can retreive it easily if needed*

### Minidump
Minidump are files uploaded when a crash occur.

You can use curl to upload a minidump : 
```bash
curl -F minidump=@demo/demo.dmp -F product=Demo -F version=0.1 -F build=foobar http://localhost:5000/submit
```

**Endpoint arguments :**
```
/submit
    minidump : The minidump file
    build : Build number (Can be any string up to 40 character)
    product : Product name (Must be an existing product)
    version : Version number (Must be an existing version)
```

# Licence 
LandingNet is distributed under GPL V3
