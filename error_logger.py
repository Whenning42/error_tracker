import sys
import traceback
import imp
import os
import pymongo
import sh

NOT_FOUND = "Not found"
PATH = "/home/william/error_logger"
GIT_PATH = PATH + "/tracked_files"

def is_system_path(pathname):
    v = pathname is None or 'site-packages' in pathname or 'python' in pathname or pathname == NOT_FOUND
    return v

def is_this_file(pathname):
    return os.path.basename(pathname) == "error_logger.py"

def commit_tracked_files(files_to_track):
    git = sh.git.bake(_cwd = GIT_PATH)

    for file in files_to_track:
        local_path = GIT_PATH + file
        sh.mkdir('-p', os.path.dirname(local_path))
        sh.cp(file, local_path)
        git.add(local_path)
    return git.commit('--allow-empty', '--allow-empty-message', m = "").split()[0]

def add_database_entry(commit_hash, exception_type, exception_value, the_traceback):
    # sh.mongod("--fork", "--dbpath", PATH + "/mongo_data", "--logpath", PATH + "/mongo_log/mongodb.log")
    client = pymongo.MongoClient(serverSelectionTimeoutMS = 500)
    db = client.error_database
    error_collection = db.errors
    error_collection.insert_one({"commit": commit_hash,
                                 "exception_type": str(exception_type),
                                 "exception_value": str(exception_value),
                                 "formatted_exception": traceback.format_exception(exception_type, exception_value, the_traceback)})
    # sh.mongod("--dbpath", PATH + "/mongo_data", "--shutdown")

def exception_handler(type, value, tb):
    paths = []
    for k in sys.modules.keys():
        try:
            path = imp.find_module(k.split(".")[0])[1]
            paths.append(path)
        except:
            paths.append(NOT_FOUND)

    files_to_track = [path for path in paths if not is_system_path(path) and not is_this_file(path)]
    files_to_track.append(os.path.abspath(tb.tb_frame.f_code.co_filename))

    commit_hash = commit_tracked_files(files_to_track)
    add_database_entry(commit_hash, type, value, tb)

    traceback.print_exception(type, value, tb)

sys.excepthook = exception_handler
