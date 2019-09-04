# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 13:37:29 2019

@author: gabew
"""

import os
import csv

# A list of the local checksum files
local_list_file_names = [#'carter_hash_tiff_only.csv',
                         'cdi_store_02_hash_tiff_only.csv',
                         'cdi_store_04_hash_tiff_only.csv',
                         'cdi_store_05_hash_tiff_only.csv',
                         'cdi_store_06_hash_tiff_only.csv',
                         'cdi_store_07_hash_tiff_only.csv',
                         'cdi_store_08_masters_hash_tiff_only.csv',
                         'cdi_store_08_project_hash_tiff_only.csv',
                         'cdi_store_10_hash_tiff_only.csv', 
                         'cdi_store_11_hash_tiff_only.csv', 
                         'cdi_store_12_hash_tiff_only.csv', 
                         'cdi_store_13_hash_tiff_only.csv',
                         'lib_store_08_checkme_hash_tiff_only.csv',
                         'mjp_hash_tiff_only.csv']    

# This function checks if a given file is a tif
# It also removes non ascii characters from any names
# It returns the (potentially modified) file name if it is a tif
#   and None if the file is not a tif
def check_filename(filename, verbose=True):
    
    if len(filename) < 5:
        if verbose:
            print("Error: File path too short")
            print(filename)
        return None
    
    if filename[-4:] != ".tif" and filename[-4:] != ".TIF":
        if verbose:
            print("Error: Files must be a .tif or .TIF")
            print(filename)
        return None
    
    filename = filename[:-4] + ".tif"
    filename = filename.replace("\\", "/")
    filename = "".join(i for i in filename if ord(i)<128)
    
    return filename
    
# This function parses the data from the BDR checksum CSV file
# It returns a dictionary: bdr_checksums
#   The keys are checksums and the values are the BDR numbers
def get_bdr_checksums():
    print("Reading BDR Checksums")
    bdr_checksums = dict()
    with open('BDR_Checksums/checksum_data_3.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        collisions = 0
        for row in csv_reader:
            if line_count == 0: pass
            else:
                checksum = row[4].upper()
                bdr_number = row[0]
                if checksum not in bdr_checksums:
                    bdr_checksums[checksum] = [bdr_number]                   
                else:
                    bdr_checksums[checksum].append(bdr_number)
                    collisions += 1
            line_count += 1
        print("Processed %s lines. %s collisions." % (line_count, collisions))  
    return bdr_checksums

# This function parses the data from the file system checksum files listed above
# Only files that are found in the file system are listed
# It takes a folder structure dictionary
# It returns two dictionaries
#   local_checksums_fwd has checksums as keys and lists of files with that checksum as values
#   local_checksums_bdw has a key for each file name with its checksum as value
def get_local_checksums(folder_structures):
    print("\nReading Local Checksums")
    
    file_checksums = dict()
    line_count = 0
    for file_name in local_list_file_names:
        with open("Local_Checksums/"+file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                
                if line_count < 2: 
                    pass
                elif row[0][0] == ';' : 
                        pass
                else:
                    
                    row_string = ""
                    for piece in row:
                        row_string += piece
                    checksum = row_string[-32:].upper()
                    filename = check_filename(row_string[17:-33])
                    
                    if filename is not None:
                        file_checksums[filename] = checksum
                        
                line_count += 1
       
    local_checksums_fwd = dict()
    local_checksums_bwd = dict()
    
    found = 0
    total = 0
    for topdir in folder_structures:
        for directory in folder_structures[topdir]:
            for filepath in folder_structures[topdir][directory]['tifs']:
                total += 1
                if filepath in file_checksums:
                    found += 1
                    
                    checksum = file_checksums[filepath]
                    if checksum not in local_checksums_fwd:
                        local_checksums_fwd[checksum] = [filepath]                   
                    else:
                        local_checksums_fwd[checksum].append(filepath)
                else:
                    checksum = None
                    
                local_checksums_bwd[filepath] = checksum                    
                    
    print("Found %s of %s" % (found, total))
    
    return local_checksums_fwd, local_checksums_bwd

# This function reads the file system and generates a dictionary to speed up future operations
# The "keep" flag determines whether the dictionary is re-generated or read from the previous version saved in folder_structure.csv
# It returns a dictionary: folder_structures
#   The keys are the top level directories (eg CDI_STORE_#) and the values are dictionaries
#   The keys of these dictionaries are folder paths and the values are dictionaries
#   These dictionaries have the following key-value pairs
#   'error' - 1 if an error was encountered while analyzing the directory otherwise 0
#   'super_dir'- 1 if the directory contains directories that contain tifs otherwise 0
#   'total_files' - The number of files in the directory not counting files in sub-directories
#   'total_tifs' - The number of tifs in the directory not counting tifs in sub-directories
#   'tifs' - A list of all the tifs in the directory
# For each top level directory the dictionary is saved to a folder_structure.csv file
def get_folder_structures(verbose=False, keep=True):
    print("\nGetting folder structure")
   
    folder_structures = dict()
    
    for indir in os.listdir('Results'):
        print("\nWorking on " + indir)    
    
        folder_structures[indir] = dict()

        if os.path.isfile("Results/" + indir + "/folder_structure.csv") and keep:
            print("folder_structure.csv exists: reading")
            
            line_count = 0
            with open("Results/" + indir + "/folder_structure.csv") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    if line_count < 1: 
                        pass
                    else:
                        directory = row[0]
                        
                        folder_structures[indir][directory] = dict()
                        folder_structures[indir][directory]['error'] = int(row[1])
                        folder_structures[indir][directory]['super_dir'] = int(row[2])
                        folder_structures[indir][directory]['total_files'] = int(row[3])
                        folder_structures[indir][directory]['total_tifs'] = int(row[4])
                        folder_structures[indir][directory]['tifs'] = row[5:]
                        
                    line_count += 1
            
        else:
            print("folder_structure.csv does not exist: analyzing directories")
                        
            for root, dirs, files in os.walk('//files.brown.edu/DFS/Library_DPS/' + indir, topdown=False):
                        
                root = root[34:]
                root = root.replace("\\", "/")
                            
                if verbose: print("".join(i for i in root if ord(i)<128))
                
                folder_structures[indir][root] = dict()
                folder_structures[indir][root]['error'] = 0
                folder_structures[indir][root]['super_dir'] = 0
                folder_structures[indir][root]['total_files'] = 0
                folder_structures[indir][root]['total_tifs'] = 0
                folder_structures[indir][root]['tifs'] = []
                    
                if root[0:25] != "CDI_STORE_10/Photo_Shoots" :
                    
                    for directory in dirs:
                        dirpath = root + "/" + directory
                        if dirpath in folder_structures[indir]:
                            if folder_structures[indir][dirpath]['total_tifs'] > 0 :
                                folder_structures[indir][root]['super_dir'] = 1
                            folder_structures[indir][root]['error'] = folder_structures[indir][root]['error'] or folder_structures[indir][dirpath]['error']
            
                        else:
                            print("Error: Sub-directory not already scanned")
                            print(dirpath)
                            folder_structures[indir][root]['error'] = 1
                    
                    for file in files:
                        folder_structures[indir][root]['total_files'] += 1
                        filepath = check_filename(root + "/" + file, False)
                        if filepath is not None:
                            folder_structures[indir][root]['total_tifs'] += 1
                            folder_structures[indir][root]['tifs'].append(filepath)
                    
                    if verbose: print("Dir contains %s files %s tifs" % (folder_structures[indir][root]['total_files'], folder_structures[indir][root]['total_tifs']))   
                
            print("Writing results")
            with open("Results/" + indir + "/folder_structure.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(["Directory", "Error", "Contains Directories", "Total Files", "Total Tifs", "Tifs"])      
                for directory in folder_structures[indir]:
                    row = ["".join(i for i in directory if ord(i)<128), folder_structures[indir][directory]['error'], folder_structures[indir][directory]['super_dir'], folder_structures[indir][directory]['total_files'], folder_structures[indir][directory]['total_tifs']] + folder_structures[indir][directory]['tifs']
                    writer.writerow(row)        
            
    return folder_structures
    
# This function generates two files for each top level directory that list collisions between local files and the BDR
# directories_injested.csv lists every directory that contains injested tifs, how many files it contains, and other information
# directories_injested_files.csv lists every tif in each directory that contains injested tifs, and other information
def analyze_dir_bdr_collisions(folder_structures, local_checksums, bdr_checksums):    
    print("\nAnalyzing directories for bdr collisions")
    
    for indir in os.listdir('Results'):

        with open('Results/' + indir + '/directories_injested.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(["Directory", "Error", "Contains Directories", "Total Files", "Total Tifs", "Injested Tifs", "Percent Injested"])        
            
            dirs_injested = []
            
            for directory in folder_structures[indir]:
                injested = 0
                for filepath in folder_structures[indir][directory]['tifs']:
                    if filepath in local_checksums:
                        checksum = local_checksums[filepath]
                        if checksum is not None and checksum in bdr_checksums:
                            injested += 1
                    else:
                        print("Error: File not found")
                        print(filepath)                        
                        folder_structures[indir][directory]['error'] = True
                if injested > 0:
                    dirs_injested.append((injested / folder_structures[indir][directory]['total_tifs'], injested, directory))
                    
            dirs_injested.sort(reverse=True)
            
            for percent_injested, injested, directory in dirs_injested:
                row = [directory, "Yes" if folder_structures[indir][directory]['error'] else " ", "Yes" if folder_structures[indir][directory]['super_dir'] else " ", folder_structures[indir][directory]['total_files'], folder_structures[indir][directory]['total_tifs'], injested, "%02f%%" % (percent_injested*100)]
                writer.writerow(row)      
    
        with open('Results/' + indir + '/directories_injested_files.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(["File", "Injested", "Instances", "BDR Numbers"])    
            
            for percent_injested, injested, directory in dirs_injested:
                row = [""]
                writer.writerow(row)    
                
                for filepath in folder_structures[indir][directory]['tifs']:
                    if filepath in local_checksums:
                        checksum = local_checksums[filepath]
                        if checksum is not None:
                            if checksum in bdr_checksums:
                                row = [filepath, "Yes", len(bdr_checksums[checksum])] + bdr_checksums[checksum]
                            else:
                                row = [filepath, "No"]
                        else:
                            row = [filepath, "Error"]
                    else:
                        print("Error: File not found")
                        print(filepath)   
                        row = [filepath, "Error"]
                    writer.writerow(row)             
                    
# This function generates two files for each top level directory that list duplicate tifs within the fily system
# directories_with_duplicates.csv lists every directory that contains duplicate tifs, how many files it contains, and other information
# directories_with_duplicates_files.csv lists every tif in each directory that contains duplicate tifs, and other information
def analyze_dir_local_collisions(folder_structures, local_checksums_fwd, local_checksums_bwd):   
    print("\nAnalyzing directories for local collisions")
    
    for indir in os.listdir('Results'):

        dirs_with_dups = []
        
        for directory in folder_structures[indir]:
            dups = 0
            for filepath in folder_structures[indir][directory]['tifs']:
                if filepath in local_checksums_bwd:
                    checksum = local_checksums_bwd[filepath]
                    if checksum is not None:
                        if len(local_checksums_fwd[checksum]) > 1:
                            dups += 1
                else:
                    print("Error: File not found")
                    print(filepath)                        
                    folder_structures[indir][directory]['error'] = True
            if dups > 0:
                dirs_with_dups.append((dups / folder_structures[indir][directory]['total_tifs'], dups, directory))
                
        dirs_with_dups.sort(reverse=True)    
        
        with open('Results/' + indir + '/directories_with_duplicates.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(["Directory", "Error", "Contains Directories", "Total Files", "Total Tifs", "Duplicate Tifs", "Percent Duplicates"])        
            
            for percent_dup, dups, directory in dirs_with_dups:
                row = [directory, "Yes" if folder_structures[indir][directory]['error'] else " ", "Yes" if folder_structures[indir][directory]['super_dir'] else " ", folder_structures[indir][directory]['total_files'], folder_structures[indir][directory]['total_tifs'], dups, "%02f%%" % (percent_dup*100)]
                writer.writerow(row)
            
        with open('Results/' + indir + '/directories_with_duplicates_files.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(["File", "Duplicate", "Matches", "Matching Files"])    
            
            for percent_dup, dups, directory in dirs_with_dups:
                row = [""]
                writer.writerow(row)    
                
                for filepath in folder_structures[indir][directory]['tifs']:
                    if filepath in local_checksums_bwd:
                        checksum = local_checksums_bwd[filepath]
                        if checksum is not None:
                            if len(local_checksums_fwd[checksum]) > 1:
                                matches = []
                                for i in local_checksums_fwd[checksum]:
                                    if i != filepath: matches.append(i)
                                row = [filepath, "Yes", len(matches)] + matches
                            else:
                                row = [filepath, "No"]
                        else:
                            row = [filepath, "Error"]
                    else:
                        print("Error: File not found")
                        print(filepath)  
                        row = [filepath, "Error"]
                    writer.writerow(row)             

# This function removes tif "artifacts" from the file system
# These files start with "._" and have a small file size (less than 1 MB)
def move_tiff_artifacts(indir=""): 
    for root, dirs, files in os.walk('//files.brown.edu/DFS/Library_DPS/' + indir, topdown=False):
        for filename in files:
            if filename[-4:] == ".tif" or filename[-4:] == ".TIF":
                if filename[0:2] == '._' :
                
                    full_filepath = root + "/" + filename
                    
                    if os.path.getsize(full_filepath) < 1024*1024 :
                        
                        new_root = '//files.brown.edu/DFS/Library_DPS/MOVED' + root[33:]
                        
                        if not os.path.isdir(new_root):
                            os.makedirs(new_root)
                    
                        os.rename(full_filepath, new_root + "/" + filename)
                    
                    else:
                        print("FILE TOO BIG")
                        print(full_filepath)
                        
# This function removes empty directories from the file system   
# "._.DS_Store" and ".DS_Store" files are ignored
def move_empty_dirs():
    for indir in os.listdir('Results'):
        print("\nWorking on " + indir) 
        moved = 0
        
        for root, dirs, files in os.walk('//files.brown.edu/DFS/Library_DPS/' + indir, topdown=False):
            
            if len(dirs) == 0 :
                empty = True
                
                for filename in files :
                    if (filename != "._.DS_Store") and (filename != ".DS_Store") :
                        empty = False
                        break
                
                if empty :
                    new_root = '//files.brown.edu/DFS/Library_DPS/MOVED' + root[33:]
                    if not os.path.isdir(new_root):
                        os.makedirs(new_root)
                    
                    for filename in files :
                        os.rename(root + "/" + filename, new_root + "/" + filename)
                    
                    os.rmdir(root)                
                    moved += 1
                    
        print("Moved %s empty directories" % moved)
            
# This is a helper function for move_duplicate_directories below
def move_duplicate_directories_helper(local_checksums, folder_structures, folder_dir_hashes):
        
    for topdir in os.listdir('Results'):
        for dir_to_move in folder_dir_hashes[topdir]:
            if folder_structures[topdir][dir_to_move]['error'] == 0:
                if len(folder_dir_hashes[topdir][dir_to_move]) == len(folder_structures[topdir][dir_to_move]['tifs']):
                                    
                    for topdir2 in os.listdir('Results'):
                        for dir_to_compare in folder_dir_hashes[topdir2]:
                            
                            if dir_to_move != dir_to_compare:
                                if set(folder_dir_hashes[topdir][dir_to_move]).issubset(set(folder_dir_hashes[topdir2][dir_to_compare])):                                                         
                                    
                                    if os.path.isdir('//files.brown.edu/DFS/Library_DPS/' + dir_to_move) and os.path.isdir('//files.brown.edu/DFS/Library_DPS/' + dir_to_compare) :
                                        root = '//files.brown.edu/DFS/Library_DPS/' + dir_to_move
                                        
                                        
                                        print("".join(i for i in dir_to_move if ord(i)<128))
                                        print("Contains %s files %s tifs" % (folder_structures[topdir][dir_to_move]['total_files'], folder_structures[topdir][dir_to_move]['total_tifs']))   
                                        
                                        print("".join(i for i in dir_to_compare if ord(i)<128))                                        
                                        print("Contains %s files %s tifs" % (folder_structures[topdir2][dir_to_compare]['total_files'], folder_structures[topdir2][dir_to_compare]['total_tifs']))   
                                        
                                        gtg = True
                                        for file in os.listdir(root):
                                            if file[-4:] != ".tif" and file[-4:] != ".TIF":
                                                if file != "._.DS_Store" and file != ".DS_Store" :
                                                    if not os.path.isfile('//files.brown.edu/DFS/Library_DPS/' + dir_to_compare + '/' + file):
                                                        gtg = False
                                                        break
                                        if gtg:

                                            while True:
                                                proceed = True
                                                break
                                                char = input("Proceed? Y/N/Q \n")
                                                if (char == 'Y') or (char == 'y') :
                                                    proceed = True
                                                    break
                                                if (char == 'N') or (char == 'n') :
                                                    proceed = False
                                                    break
                                                if (char == 'Q') or (char == 'q') :
                                                    return None, None
                                                
                                            if proceed :
                                                print("Moving")
                                                new_root = '//files.brown.edu/DFS/Library_DPS/MOVED/' + dir_to_move
                                                
                                                if not os.path.isdir(new_root):
                                                    os.makedirs(new_root)
                                                
                                                for filename in os.listdir(root) :
                                                    os.rename(root + "/" + filename, new_root + "/" + filename)
                                                
                                                os.rmdir(root)    
                                                                                                
                                                del folder_structures[topdir][dir_to_move]
                                                del folder_dir_hashes[topdir][dir_to_move]
                                                
                                                with open("Results/" + topdir + "/folder_structure.csv", 'w', newline='') as csvfile:
                                                    writer = csv.writer(csvfile, delimiter=',')
                                                    writer.writerow(["Directory", "Error", "Contains Directories", "Total Files", "Total Tifs", "Tifs"])   
                                                    folder_structure = folder_structures[topdir]
                                                    for directory in folder_structure:
                                                        row = ["".join(i for i in directory if ord(i)<128), folder_structure[directory]['error'], folder_structure[directory]['super_dir'], folder_structure[directory]['total_files'], folder_structure[directory]['total_tifs']] + folder_structure[directory]['tifs']
                                                        writer.writerow(row)                                                   
                                                
                                                return folder_structures, folder_dir_hashes
                                        else:
                                            print("Not valid\n")
    return None, None
        
# This function removes all directories that are sub-sets or duplicates of other folders
# If a directory contains only duplicate tifs but those dupliactes are spread accross multiple other directories, it is not removed
# If a directory contains files besides tifs, files with the same names must exist in the other directory for it to be removed
#   with the exception of "._.DS_Store" and ".DS_Store" files, which are ignored
def move_duplicate_directories(local_checksums, folder_structures):   
    print("\nMoving Duplicate Directories")
    folder_dir_hashes = dict()
    for topdir in folder_structures:
        folder_dir_hashes[topdir] = dict()
        for directory in folder_structures[topdir]:
            if len(folder_structures[topdir][directory]['tifs']) > 0:
                folder_dir_hashes[topdir][directory] = []
                for filepath in folder_structures[topdir][directory]['tifs']:
                    if filepath in local_checksums:
                        if local_checksums[filepath] is None:
                            del folder_dir_hashes[topdir][directory]
                            break
                        else:
                            folder_dir_hashes[topdir][directory].append(local_checksums[filepath])  
        
    while True :
        print("\n")
        folder_structures, folder_dir_hashes = move_duplicate_directories_helper(local_checksums, folder_structures, folder_dir_hashes)
        if folder_structures is None : return
       
   

# This function removes all directories that contain only injested tifs
# If the folder contains files besides tifs they are left behind in the directory
def move_injested_directories(folder_structures, local_checksums):
    print("\nMoving Injested Directories")
    
    for indir in os.listdir('Results'):
        print("\nWorking on " + indir)    

        moved = 0        
        for directory in folder_structures[indir]:
            injested = 0
            for filepath in folder_structures[indir][directory]['tifs']:
                if filepath in local_checksums:
                    checksum = local_checksums[filepath]
                    if checksum is not None and checksum in bdr_checksums:
                        injested += 1
                else:
                    print("Error: File not found")
                    print(filepath)                        
            if injested > 0 and injested == len(folder_structures[indir][directory]['tifs']):
                moved += 1
                
                if not os.path.isdir('//files.brown.edu/DFS/Library_DPS/MOVED/' + directory):
                    os.makedirs('//files.brown.edu/DFS/Library_DPS/MOVED/' + directory)
                
                for filepath in folder_structures[indir][directory]['tifs']:
                    old_filepath = '//files.brown.edu/DFS/Library_DPS/' + filepath
                    new_filepath = '//files.brown.edu/DFS/Library_DPS/MOVED/' + filepath
                    
                    if os.path.isfile(old_filepath):
                        os.rename(old_filepath, new_filepath)                
            
        print("Moved %s directories" % moved)
        
    

if __name__ == '__main__':    

    # Get BDR checksums
    bdr_checksums = get_bdr_checksums()
    
    # Get the folder structure
    # Force re-generation in case changes were made
    folder_structures = get_folder_structures(False, False)
    
    # Get local checksums
    local_checksums_fwd, local_checksums_bwd = get_local_checksums(folder_structures)
    
    
    
    # Comment or uncomment lines below to change the behavior of the script.
    # To avoid unexpected behavior, don't uncomment move_injested_directories and move_duplicate_directories simultaneously, and do not change the order of the lines
    
    # Generate bdr collision csv file
    analyze_dir_bdr_collisions(folder_structures, local_checksums_bwd, bdr_checksums) 
    
    # Generate local collision csv file
    analyze_dir_local_collisions(folder_structures, local_checksums_fwd, local_checksums_bwd)
    
    # Move injested directories
#    move_injested_directories(folder_structures, local_checksums_bwd)

    # Move duplicate directories
#    move_duplicate_directories(local_checksums_bwd, folder_structures)    
    
    # Move empty directories
#    move_empty_dirs()

