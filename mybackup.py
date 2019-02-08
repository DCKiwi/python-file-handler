import os, os.path, pickle, shutil, sys, time, logging.handlers
from HasherMod import createFileSignature

myArchive = os.path.expanduser("~/Desktop/myArchive")
myObjects = os.path.expanduser("~/Desktop/myArchive/objects")
myIndex = os.path.expanduser("~/Desktop/myArchive/index.txt")


# ======================================================================================================================
# LOGGER
# ======================================================================================================================


PROGRAM_NAME = "mybackup"
LOG_FILE = os.path.join(myArchive, PROGRAM_NAME + ".log")

CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.INFO

logger = logging.getLogger(PROGRAM_NAME)
logger.setLevel(logging.DEBUG)

# FILE-BASED LOG =======================================================================================================


def file_logger():

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create log file after init called
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(FILE_LOG_LEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Add timestamp
    logger.info('\n---------\nLog started on %s.\n---------\n' % time.asctime())

    return logger

# ======================================================================================================================
# INIT -  creates a new archive directory and within it creates a subdirectory called objects and an empty index file
# ======================================================================================================================


def initializedir():

    if os.path.exists(myObjects) and os.path.isdir(myObjects):
        print("myArchive and its subdirectory objects exists")
        if os.path.exists(myIndex) and os.path.isfile(myIndex):
            print("And Finally - Index file Exists")
        else:
            print("No Index file present - creating now\n...\nDone!")
            open(myIndex, 'w+')

    else:
        print("myArchive does not Exist - Creating myArchive and its subdirectories\n...\nDone!")
        os.makedirs(myObjects)
        if os.path.exists(myIndex) and os.path.isfile(myIndex):
            print("And Finally - Index file Exists")
        else:
            print("No Index file present - creating now\n...\nDone!")
            open(myIndex, 'w+')


# ======================================================================================================================
# STORE - recursively backups up all files in the named directory and saves them into the objects directory, and
# updates the index of what's in the archive.
# ======================================================================================================================


def mysource():
    while True:
        sourcepath = os.path.expanduser(input("Please enter the full path of the directory you want to backup"
                                              " - otherwise abort by pressing 'qq'"))
        if os.path.exists(sourcepath) and os.path.isdir(sourcepath):
            print("Thank you backing up commencing \n...\n....\n.....")
            processStart(sourcepath)

            break

        elif sourcepath == 'qq':
            print("Aborting store process")
            break


def processStart(sourcepath):
    # Check if index file is empty or not
    if os.path.getsize(myIndex) == 0:
        ff = open(myIndex, "ab+")
        newdict = {}

        for thisdirpath, dirnames, filenames in os.walk(sourcepath):
            print("scanning " + thisdirpath)

            for filename in filenames:
                working = os.path.join(thisdirpath, filename)

                # Create Signature Hash for file
                sig = createFileSignature(working)
                destObjectsFolder = os.path.join(myObjects, sig)
                shutil.copy(working, destObjectsFolder)

                newdict[working] = sig
        print("Backup complete")
        print("These files were added to the Archive: ", '\n')

        for kk, vv in newdict.items():
            print(kk, '\n')

            logger.info("These files were added to the Archive:  " + kk + " " + time.ctime())

        pickle.dump(newdict, ff)
        ff.close()


    else:
        noAddCounter = 0

        # creating temp list and dict to hold the values from file and the new values to be appended to file
        dict2 = {}
        tlist = []
        ff = open(myIndex, "rb")

        # Load via Pickle the Data already in Index.txt and take data and append in the tlist:
        # We have a list of existing Signatures
        obj_dict = pickle.load(ff)
        for k, v in obj_dict.items():
            tlist.append(v)

        for thisdirpath, dirnames, filenames in os.walk(sourcepath):
            print("scanning " + thisdirpath, '\n')

            for filename in filenames:
                working = os.path.join(thisdirpath, filename)
                sig = createFileSignature(working)

                # Compare file sig to existing sigs - If not there then file has not been backed up
                # and we will back it up and Index
                if sig not in tlist:
                    destObjectsFolder = os.path.join(myObjects, sig)
                    shutil.copy(working, destObjectsFolder)
                    dict2[working] = sig
                else:
                    noAddCounter += 1
                    continue

        if noAddCounter > 0:
            print("The number of files not backed up as they are already stored in Archive Folder is: ", noAddCounter, '\n')

        if dict2 == {}:
            print("No new files were added to the Archive")
        else:
            print("These files were added to the Archive: \n")
            for kk, vv in dict2.items():
                print(kk, '\n')

                logger.info("These files were added to the Archive:  " + kk + " " + time.ctime())

        z = {**dict2, **obj_dict}

        with open(myIndex ,'wb') as writeff:
            pickle.dump(z, writeff)

        with open(myIndex, 'rb') as readff:
            newz = pickle.load(readff)

        ff.close()
        return

# ======================================================================================================================
# LIST - lists any path that contains the pattern, or if no pattern is specified, displays the paths of all files in
# the archive.
# ======================================================================================================================


def indexchek():

    # try to load entries in index using pickle - won't work if empty index file throw EOFERROR otherwise
    try:
        index_file = pickle.load(open(myIndex, "rb"))
        user_pattern = input("Please insert pattern you are looking for:  ")
        thislist(user_pattern, myObjects, index_file)

    except EOFError:
        print("Index File empty - must store some files first - before using list command.")
        quit()


def thislist(pattern, objects, index):

    # iterate through objects and the corresponding dict
    tmpCount = 0
    # Loop through file names of files stored in objects folder
    for anobject in os.listdir(objects):


        for path_key, hash_value in index.items():

            if anobject == hash_value:
                file_dir, file_name = os.path.split(path_key)

                if pattern in file_name:
                    print(path_key)
                    print("Hash: " + anobject + "\n")
                    tmpCount += 1
    if tmpCount == 0:
        newInput = input("No file with that pattern found. Please enter a new pattern, or no pattern to list all files in archive.")
        thislist(newInput, myObjects, index)


# ======================================================================================================================
# TEST - checks that ALL the objects listed in the index have matching files in the objects directory, and checks that
# the files in the objects have the correct content: i.e. that the hash of the file's contents matches its filename.
# ======================================================================================================================


def checktwo(myObjects):
    for thisdirpath, dirnames, filenames in os.walk(myObjects):

        for specificFile in filenames:
                    fPath = os.path.join(myObjects , specificFile)
                    sigcheck = createFileSignature(fPath)
                    if specificFile == sigcheck:
                        continue
                    else:
                        print()
                        print("Found erroneously named file:")
                        print(specificFile, " does not have the correct filename. It should be: ", sigcheck)


def dictLoop(dict1, dict2, acounter):
        for key in dict1:

            firstvalue = dict1[key]

            for akey in dict2:
                secondvalue = dict2[akey]

                if firstvalue == secondvalue:
                    acounter += 1
                    del dict2[akey]

                    break

            del dict1[key]
            break

        if len(dict1) == 0 or len(dict2) == 0:
            print("Number of Correct Matches:  ", acounter,"\n")

            logger.info("Number of Correct Matches:  " + str(acounter) + " " + time.ctime())

            if len(dict2) > 0:
                print("The following ", len(dict2),
                      "entries are erroneous entries in the index.txt file and are not matched"
                      " by any actual files in the objects folder:")

                logger.info("The following " + str(len(dict2)) + " entries are erroneous entries in the index.txt file and are"
                            " not matched by any actual files in the objects folder:" + " " + time.ctime())

                for kk, vv in dict2.items():
                    print(kk, ': ', vv)

                    logger.info(kk + ': ' + vv + time.ctime())

            return

        else:
            dictLoop(dict1, dict2, acounter)


def test():
    # load values from index via turtle

    if os.path.getsize(myIndex) == 0:
        print("index.txt file is empty - any file in objects backup directory has not been serialized...\n"
              "Matches/count of correct entries are therefore = 0 ")
        return

    else:
        objectsDict = {}
        with open(myIndex, 'rb') as readf:
            indexDict = pickle.load(readf)
        readf.close()

        # Create a new DICT of files in object the Key being the full file path and the values being the filename
        #  ie. Hash value of file
        for thisdirpath, dirnames, filenames in os.walk(myObjects):
            for specificFile in filenames:
                fPath = os.path.join(myObjects, specificFile)

                objectsDict[fPath] = specificFile

        # Now we loop in objects dictionary that we created and compare its values to the index dict to find the matching ones and
        # count them. We then delete the ones that match from both dicts - this would have to be a recursive loop dictLoop below
        # AFTER finishing recursive loop:
        # We Check the files in objects dir that have the wrong name - ie hash doesn't match content and list them.

        counter = 0
        print("The Objects folder has ", len(objectsDict), " files stored in it\nThe index file has ",
              len(indexDict), " entries\n\n")

        dictLoop(objectsDict, indexDict, counter)
        checktwo(myObjects)


# ======================================================================================================================
# GET -  restore that file into the current directory (even if it was in a subdirectory originally) or display the first
# 50 matches prompting the user for selection of one.
# ======================================================================================================================


def get(file_patten, objects, index):

    found_files = []

    # iterate through objects and the corresponding dict
    for path, subdirs, files in os.walk(objects):

        for name in files:
            source = os.path.join(path, name)

            for path_key, hash_value in index.items():

                # check hash in index and object folder
                if name == hash_value:
                    file_dir, file_name = os.path.split(path_key)

                    # check to see if filename or pattern in the index
                    if file_patten == file_name:
                        found_files.append((source, path_key, hash_value, file_name))

                    elif file_patten in file_name:
                        found_files.append((source, path_key, hash_value, file_name))

    if not found_files:
        print("No matching files found")

    # call recover function on matches
    recover(found_files)


def recover(found_list):

    # if one file found access tuple in list, copy file to cwd and rename.
    if len(found_list) == 1:
        abs_path_archive = found_list[0][0]
        current_dir = os.getcwd()
        file_hash = found_list[0][2]
        file_name = found_list[0][3]

        # check to see if file already exists
        if os.path.exists(file_name):
            overwrite = input(file_name + " already exists in current directory, do you want to overwrite it? (y/n): ")

            while overwrite not in ["y", "n"]:
                overwrite = input("Invalid response. -- " + file_name + " already exists, do you want to "
                                                                        "overwrite it? (y/n): ")

            if overwrite == "n":
                print("File not overwritten")
                exit(1)
            else:
                print("File overwritten")

        shutil.copy2(abs_path_archive, current_dir)
        os.rename(file_hash, file_name)
        print("\n" + file_name + " successfully recovered to current working directory")

    elif len(found_list) > 1:
        print("Multiple matches found. Please select number corresponding to file you wish to restore:\n")

        # display file name and path for user to select one.
        i = 0
        numbers = []
        for archive, path, file, hash in found_list:
            print(str(i) + " -- " + path)
            numbers.append(i)
            i += 1

        user_input = int(input("\nNumber: "))

        # validate user selection.
        while user_input not in numbers:
            user_input = int(input("Invalid response, select number corresponding to file you wish to restore: "))

        # extract users selection from tuple list.
        abs_path_archive = found_list[user_input][0]
        current_dir = os.getcwd()
        file_hash = found_list[user_input][2]
        file_name = found_list[user_input][3]

        # check to see if file already exists
        if os.path.exists(file_name):
            overwrite = input(file_name + " already exists in current directory, do you want to overwrite it? (y/n): ")

            while overwrite not in ["y", "n"]:
                overwrite = input("Invalid response. -- " + file_name + " already exists, do you want to "
                                                                        "overwrite it? (y/n): ")

            if overwrite == "n":
                print("File not overwritten")
                exit(1)
            else:
                print("File overwritten")

        # copy file to cwd then rename.
        shutil.copy2(abs_path_archive, current_dir)
        os.rename(file_hash, file_name)
        print("\n" + file_name + " successfully recovered to current working directory")


# ======================================================================================================================
# RESTORE -  restores everything in the archive into the named destination directory.
# ======================================================================================================================


def restore(destination, index):

    # call restore function to either destinationDir or current working dir.
    if destination and os.path.isdir(destination):
        destination = destination

    elif destination == "":
        destination = os.getcwd()

    else:
        raise OSError("Destination directory does not exists:")

    # iterate through objects folder extracting file name and path, copy to destinationDir.
    for path, subdirs, files in os.walk(myObjects):

        for name in files:
            source = os.path.join(path, name)

            if not os.path.isfile(os.path.join(destination, name)):
                shutil.copy2(source, destination)
            else:
                print(destination + "already exists")
                continue

    # iterate through objects and the corresponding dict
    for objects in os.listdir(destination):

        for path_key, hash_value in index.items():

            # if hash matches index file hash_value, split corresponding path_key into file_dir and file_name.
            if objects == hash_value:
                file_dir, file_name = os.path.split(path_key)

                # generate absolute paths for old and new files then rename old with new.
                old = os.path.join(destination, objects)
                new = os.path.join(destination, file_name)

                if os.path.isfile(old):
                    os.rename(old, new)

                # remove first slash from file_dir absolute path and join with destination dir then creates new folders
                # in destination dir.
                new_dir = os.path.join(destination, file_dir[1:])

                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)

                # check that files haven't already been restored to
                full_file = os.path.join(new_dir, file_name)
                if os.path.isfile(full_file):
                    print("File already exists:\n" + full_file + "\n")
                    os.remove(full_file)

                # check to see new dir and file are present and not already restored.
                if os.path.exists(new_dir) and os.path.isfile(new) and not os.path.isfile(os.path.join(new_dir, file_name)):
                    shutil.move(new, new_dir)

    print("\nArchive restored\n")


# ======================================================================================================================
# INIT VERIFICATION
# ======================================================================================================================


def checkinitfirst():
    try:
        if os.path.exists(myObjects) and os.path.isdir(myObjects) and os.path.exists(myIndex) and os.path.isfile(myIndex):
            return True
    except ValueError:
        print("Must create Archive directory first before using init command")
        exit(1)


# ======================================================================================================================
# INDEX FILE CHECK
# ======================================================================================================================


def load_index_file():
    try:
        index_file = pickle.load(open(myIndex, "rb"))
    except IOError:
        print("Error: can't find file or read data")
        exit(1)

    return index_file


# ======================================================================================================================
# COMMAND LINE ARGUMENTS
# ======================================================================================================================


if len(sys.argv) == 1:
    print("\nUsage: mybackup <function>...\n"
          "init - initialise the archive directory\n"
          "store  - add the specified directory to the archive\n"
          "list  - show what files are in the archive\n"
          "test - check that the objects folder isn't damaged\n"
          "list - show what files are in the archive\n"
          "get - recover a single file\n"
          "restore - recover a copy of everything the archive")
    sys.exit("\nInvalid usage - see commands above\n")

elif sys.argv[1] == "init":

    if len(sys.argv) == 2:
        initializedir()

    else:
        sys.argv("Usage: mybackup init -- initialise the archive directory ")

elif sys.argv[1] == "store":

    if len(sys.argv) == 2 and checkinitfirst():
        file_logger()
        mysource()

    elif not checkinitfirst():
        sys.exit("Must create Archive directory first before using store command")

    else:
        sys.exit("Usage: mybackup store")

elif sys.argv[1] == "list":

    if 2 <= len(sys.argv) <= 3 and checkinitfirst():

        if len(sys.argv) == 2:
            user_pattern = ""
            thislist(user_pattern, myObjects, load_index_file())

        else:
            thislist(sys.argv[2], myObjects, load_index_file())

    elif not checkinitfirst():
        sys.exit("Must create Archive directory first before using list command")

    else:
        sys.exit("Usage: mybackup list -- lists archive contents. If no pattern specified displays entire archive")

elif sys.argv[1] == "test":

    if len(sys.argv) == 2 and checkinitfirst():
        file_logger()
        test()

    elif not checkinitfirst():
        sys.exit("Must create Archive directory first before using test command")

    else:
        sys.exit("Usage: mybackup test -- check that the objects folder isn't damaged")

elif sys.argv[1] == "get":

    if len(sys.argv) == 3 and checkinitfirst():
        get(sys.argv[2], myObjects, load_index_file())

    elif not checkinitfirst():
        sys.exit("Must create Archive directory first before using get command")

    else:
        sys.exit("Usage: mybackup get <filename-or-pattern> -- recovers single file from archive")

elif sys.argv[1] == "restore":

    if 2 <= len(sys.argv) <= 3 and checkinitfirst():
        restore_dir = ""

        if len(sys.argv) == 3:
            restore_dir = sys.argv[2]

        restore(restore_dir, load_index_file())

    elif not checkinitfirst():
        sys.exit("Must create Archive directory first before using restore command")

    else:
        sys.exit("Usage: mybackup restore <destinationDir> -- restores everything in the archive to <destinationDir>\n"
                 "if argument empty restores to current working directory ")
else:
    print("Usage: mybackup <function>...\n"
          "init - initialise the archive directory\n"
          "store - add the specified directory to the archive\n"
          "list - show what files are in the archive\n"
          "test - check that the objects folder isn't damaged\n"
          "list - show what files are in the archive\n"
          "get - recover a single file\n"
          "restore - recover a copy of everything the archive\n")
    sys.exit("Invalid usage - see commands above")
