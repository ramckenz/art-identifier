# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 12:59:37 2019

@author: Robert McKenzie
"""

import multiprocessing as mp
import requests
import socket
import sys
import os
import time
import random

from io import BytesIO
from PIL import Image

import imagestatsengine as ise
import raidatabaseloader as rdl
import raidentifier


"""
Searches data in the RAI data format for metadata values. These may include
width, height, title, artist, filename, URL, etc.
data: Input data, in string form.
query: desired value, in string form. Examples are "artist" and "url".
"""
def get_metadata_val(data, query):
    metadata = data[:data.find("%")].split("\n")
    query = query.upper()
    
    for line in metadata:
        if not line.find(query) == -1:
            val = line.split()[1:]
            
            #In case the value is a string that contains spaces, like a long artist or title name.
            strval = ""
            for word in val:
                strval = strval + word + " "
            try:
                #if the value is a number like height or width, we want an int.
                return int(strval.strip())
            except:
                return strval.strip()
    
    return None

def get_all_metadata(data):
    return data[:data.find("%")]

"""
Takes image data in RAI data format and returns a python PIL Image object.
data: RAI data format data.
"""
def get_img_from_post(data):
    width = get_metadata_val(data, "width")
    height = get_metadata_val(data, "height")
    data_pix = data[data.find("%") + 1:].split("%")
    
    
    im = Image.new("RGB",(width, height))
    count = 0
    for cy in range(height):
        for cx in range(width):
            pix = data_pix[count].split(",")
            r = int(pix[0])
            g = int(pix[1])
            b = int(pix[2])
            #I had to do this backwards for some reason.
            #Maybe figure it out at some point.
            im.putpixel((cx, cy), (r,g,b))
            count += 1
    #im.show()
    return im

"""
Class used to send requests from the server to the request handler. It contains
the settings of the request (request type, data type, etc.), as well as a "history"
of the request as it's sent from process to process and an error field, both for
testing and debugging purposes.

data: RAI format data.
data_type: data type, usually found using get_metadata_val. Currently either "IMG_DATA" or "URL"
req_type: request type, usually found using get_metadata_val. Currently either "ADD" or "IDENTIFY"
req_id: request ID, so the client can retrieve the results of the request once they're available.
"""
class Post_request:
    def __init__(self, data, data_type, req_type, req_id):
        self.data = data
        self.data_type = data_type
        self.req_type = req_type
        self.req_id = req_id
        self.history = "Request " + str(req_id) + ": " + req_type + " request with " + data_type + " data.\n"
        self.error = ""

"""
Class used to send responses from the reponse handler to the server. It contains the
original Post_request object as well as the result in string form. The get_age is
also available so that responses can be "timed out" if clients stop requesting them.

req: original post request.
result: result
birthday: time at which response was created.

"""
class Post_response:
    def __init__(self, req, result):
        self.req = req
        self.result = result
        self.birthday = time.time()
        
    def get_age(self):
        return time.time() - self.birthday

"""
Function meant to be spawned as a process. It starts up and runs the server,
taking in HTTP requests and passing them along to the database interface as needed.
It also takes responses from the database interface and delivers them to clients when
requested.
port: Port to run the server on.
request_pipe: Pipe for this process to use for sending requests to the DB interface.
response_pipe: Pipe through which this process receives responses from the DB interface.
shell_pipe: Pipe through which this process receives commands from the shell.
"""
def run_server(port, request_pipe, response_pipe, shell_pipe):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.settimeout(3.0) #Every 3 seconds of inactivity, raise an exception so the shell pipe can be checked.
    serverSocket.bind(('', port))
    serverSocket.listen(10)
    
    cur_post_id = 0
    
    #All requests that have been "solved" by the server and are awaiting being sent back.
    avail_responses = []
    
    running = True
    while running:
        try:
            connectionSocket, addr = serverSocket.accept()
            connectionSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 21)
            
            message = connectionSocket.recv(1024)
            message = message.decode()
            msg_split = message.split(" ")
            
            if msg_split[0] == "GET":
                try:
                    request = msg_split[1][1:]
                    if request == "newid":
                        #print(str(addr) + " requests new ID. Assigning ID " + str(cur_post_id))
                        connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                        connectionSocket.send("Content-Type: text/html\n\n".encode())
                        connectionSocket.send(str(cur_post_id).encode())
                        cur_post_id += 1
                        
                    elif request[:2] == "id":
                        id_requested = request[2:]
                        #print(str(addr) + " requests response with ID " + id_requested)
                        response = Post_response(None, None)
                        for i in range(len(avail_responses)):
                            res = avail_responses[i]
                            #print(str(res.req.req_id))
                            #res.req.req_id is in fact stored as an int.
                            if str(res.req.req_id) == id_requested:
                                response = res
                                avail_responses.remove(res)
                        if response.req == None:
                            while response_pipe[1].poll(0.01):
                                new_response = response_pipe[1].recv()
                                #print(str(new_response.req.req_id))
                                if str(new_response.req.req_id) == id_requested:
                                    response = new_response
                                else:
                                    avail_responses.append(new_response)
                        
                        if not response.req.error == "":
                            print("ERROR on request with ID " + str(response.req.req_id) + ": " + response.req.error)
                            connectionSocket.send("Error: Unable to process.".encode())
                        elif response.req == None:
                            print("No response yet with ID " + id_requested + ". Sending 404")
                            connectionSocket.send("HTTP/1.x 404 Not Found\r\n".encode())
                        elif response.result.upper() == "SUCCESS":
                            connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                            connectionSocket.send("Content-Type: text/html\n\n".encode())
                            connectionSocket.send("Success!\n".encode())
                        else:
                            connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                            connectionSocket.send("Content-Type: text/html\n\n".encode())
                            connectionSocket.send(response.result.encode())
                    
                    elif request == "test.html":
                        file = open(request)
                        response = file.read()
                        connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                        connectionSocket.send("Content-Type: text/html\n\n".encode())
                        try:
                            for i in range(len(response)):
                                connectionSocket.send(response[i].encode())
                        except:
                            print("Error sending response to ", addr)
                    
                    else:
                        connectionSocket.send("HTTP/1.x 404 Not Found\r\n".encode())
                
                except:
                    connectionSocket.send("HTTP/1.x 404 Not Found\n".encode())
                    
            elif msg_split[0] == "POST":
                connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                connectionSocket.send("Content-Type: text/html\n\n".encode())
                try:
                    data = message.split("METADATA:")[1]
                    if not (data[-3:] == "!!!"):
                        gram = connectionSocket.recv(4096).decode()
                    else:
                        gram = ""
                except:
                    data = ""
                    gram = ""
                    
                data += gram
                
                if not (data[-3:] == "!!!"):
                    while not gram[-3:] == "!!!":
                        try:
                            gram = connectionSocket.recv(4096).decode()
                            data += gram
                        except IndexError as e:
                            print(e)
                            print(gram)
                data = data[:-3]
                data_type = get_metadata_val(data, "data_type").upper() #IMG_DATA or URL
                req_type = get_metadata_val(data, "request_type").upper() #ADD or IDENTIFY
                req_id = get_metadata_val(data, "request_id")
                
                request = Post_request(data, data_type, req_type, req_id)
                request_pipe[0].send(request)
                
            connectionSocket.close()
        except:
            pass
        
        if shell_pipe[1].poll(0.0001):
            command = shell_pipe[1].recv()
            if command.command == "exit":
                running = False

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(letters) for i in range(stringLength))

"""
Class that facilitates use of the database by the database interface. It can be
called to access the database, save the database, or add stats to the database.
"""
class Database_manager:
    def __init__(self, database):
        self.db = database
        
    def add_stat(self, im_stat):
        self.db.append(im_stat)
        
    def save_to_file(self, filename, verbose = True):
        temp_name = "TEMP_DB_SAVE_" + randomString() + ".txt"
        temp_file = open(temp_name, "w+")
        if verbose:
            print("Writing save file...")
        for stat in db:
            temp_file.write(stat[0] + "!\n%")
            temp_file.write(ise.stats_to_string(stat[1:]) + "\n\n")
        temp_file.close()
        try:
            if verbose:
                print("Validating...")
            val_file = open(temp_name, "r")
            rdl.load_data_file(val_file)
            if verbose:
                print("Validated. Finalizing save...")
        except:
            if verbose:
                print("Failed. Aborted save.")
            return False
        
        try:
            os.remove("./" + filename)
        except:
            pass
        os.rename("./" + temp_name, "./" + filename)
        return True
        
    def find_closest_match(self, im_stat, depth = 15, multiprocess = True):
        result = raidentifier.find_closest_match(self.db, im_stat, depth, multiprocess)
        return result[0]
    
def run_database_interface(database, request_pipe, response_pipe, shell_pipe):
    dbm = Database_manager(database)
    running = True
    
    while running:
        if request_pipe[1].poll(3):
            req = request_pipe[1].recv()
            req.data_type = req.data_type.strip()
            req.req_type = req.req_type.strip()
            if req.data_type == "URL":
                try:
                    response = requests.get(req.data.split("%")[1])
                    img = Image.open(BytesIO(response.content))
                except:
                    req.error = req.error + "Error! Unable to get image from URL\n"
            elif req.data_type == "IMG_DATA":
                try:
                    img = get_img_from_post(req.data)
                except:
                    req.error = req.error + "Error! Unable to read image data.\n"
            else:
                req.error = req.error + "Error! Data type " + req.data_type + " not understood.\n"
            #img.show()
                
            if req.error == "":
                im_stat = ise.get_image_stats(img)
                result = ""
                if req.req_type == "IDENTIFY":
                    try:
                        result = dbm.find_closest_match(im_stat)
                        req.history = req.history + "Identified by DB interface.\n"
                    except:
                        req.error = req.error + "Error! Couldn't identify.\n"
                elif req.req_type == "ADD":
                    try:
                        #Get available metadata from the RAI data and put it in the statistics.
                        metadata_str = ""
                        title = get_metadata_val(req.data, "title")
                        artist = get_metadata_val(req.data, "artist")
                        if title:
                            metadata_str = metadata_str + "TITLE " + title + "\n"
                        if artist:
                            metadata_str = metadata_str + "ARTIST " + artist + "\n"
                        if req.data_type == "URL":
                            metadata_str = metadata_str + "URL " + req.data.split("%")[1] + "\n"
                        
                        im_stat[0] = metadata_str
                        #print(im_stat)
                        dbm.add_stat(im_stat)
                        result = "SUCCESS"
                        req.history = req.history + "Added to database."
                    except:
                        req.error = req.error + "Error! Couldn't add to database." 
                
                if not req.error == "":
                    print(req.error)
                response = Post_response(req, result)
                #print("finished post response")
                response_pipe[0].send(response)
                #print("sent response to server.")
                
        if shell_pipe[1].poll(0.0001):
            command = shell_pipe[1].recv()
            if command.command == "exit":
                running = False
            elif command.command == "savedb":
                shell_pipe[0].send(dbm.save_to_file(command.args[0]))

class Shell_command:
    def __init__(self, command, args = []):
        self.command = command
        self.args = args
       
def run_shell(server_shell_pipe, dbi_shell_pipe, db_filename):
    running = True
    print("RAI server now running. Type 'help' for server commands.")
    
    helpfile = open("raishellhelp.txt", "r")
    helpText = helpfile.read()
    
    while running:
        inp = input("RAI shell$ ")
        inpsplit = inp.split(" ")
        try:
            args = inpsplit[1:]
        except:
            args = []
        if inp == "help":
            print(helpText)
            
        elif inp == "exit":
            print("Shutting down...")
            exitCommand = Shell_command("exit")
            server_shell_pipe[0].send(exitCommand)
            dbi_shell_pipe[0].send(exitCommand)
            running = False
            
        elif inpsplit[0] == "savedb":
            if len(args) == 0:
                args.append(db_filename)
            saveCommand = Shell_command("savedb", args = args)
            dbi_shell_pipe[0].send(saveCommand)
            time.sleep(3.1)
            if(dbi_shell_pipe[1].recv() == True):
                print("Save success.")
            else:
                print("Save failed.")
        
                
if __name__ == "__main__":
    args = sys.argv
    try:
        port = int(sys.argv[1])
        dbfilename = sys.argv[2]
    except:
        print("Error in arguments. Proper format: python raiserver3.py [port] [database file name]")
        sys.exit()
    
    print("Starting server...")
    
    try:
        dbfile = open(dbfilename, "r")
        db = rdl.load_data_file(dbfile)
        dbfile.close()
    except:
        print("Couldn't load provided database file. Exiting.")
        sys.exit()
    
    port = 6500
    try:
        port = int(sys.argv[1])
    except:
        port = 6500
    
    request_pipe = mp.Pipe()
    response_pipe = mp.Pipe()
    server_shell_pipe = mp.Pipe()
    dbi_shell_pipe = mp.Pipe()
    
    server_proc = mp.Process(target = run_server, args = (port, request_pipe, response_pipe, server_shell_pipe))
    dbi_proc = mp.Process(target = run_database_interface, args = (db, request_pipe, response_pipe, dbi_shell_pipe))
    
    server_proc.start()
    dbi_proc.start()
    
    run_shell(server_shell_pipe, dbi_shell_pipe, dbfilename)
    
    server_proc.join()
    print("Server process joined.")
    dbi_proc.join()
    print("Database interface process joined.")