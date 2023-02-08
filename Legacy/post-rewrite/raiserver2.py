# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 14:17:32 2019

@author: Robert
"""

import multiprocessing as mp
import requests
import socket
import sys
import time

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
                strval = strval + word
            try:
                #if the value is a number like height or width, we want an int.
                return int(strval)
            except:
                return strval
    
    return None

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
Receives post requests from the server and processes them or passes them to the
database manager to be added to the database.
"""
def run_request_handler(database, handler_id, request_pipe, identify_response_pipe, db_add_pipe, shell_pipe):
    running = True
    
    while running:
        if request_pipe[1].poll(3): #poll lasts 3 seconds in case a shell command is sent.
            req = request_pipe[1].recv()
            if req.data_type == "URL":
                try:
                    response = requests.get(req.data)
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
                print(req.error)
                
            if req.error == "":
                im_stat = ise.get_image_stats(img)
                
                if req.req_type == "IDENTIFY":
                    result = raidentifier.find_closest_match(database, im_stat, 15, multiprocess = False)
                    req.history = req.history + "Identified by handler " + str(handler_id) + ".\n"
                    identify_response_pipe[0].send(Post_response(req, result[0]))
                elif req.req_type == "ADD":
                    req.history = req.history + "ADD request sent to database manager by handler " + str(handler_id) + ".\n"
                    db_add_pipe[0].send((req, im_stat))
                else:
                    req.error = req.error + "Error! Request type field not understood.\n"
                    identify_response_pipe[0].send(Post_response(req, None))
            else:
                identify_response_pipe[0].send(Post_response(req, None))
        
        if shell_pipe[1].poll(0.01):
            command = shell_pipe[1].recv()
            if command.text == "stop":
                running = False

def run_response_handler(identify_response_pipe, db_response_pipe, server_response_pipe, shell_pipe):
    running = True
    
    while running:
        if identify_response_pipe[1].poll(.01):
            res = identify_response_pipe[1].recv()
            server_response_pipe[0].send(res)
        
        if db_response_pipe[1].poll(0.1):
            res = db_response_pipe[1].recv()
            server_response_pipe[0].send(res)
        
        if shell_pipe[1].poll(0.01):
            command = shell_pipe[1].recv()
            if command.text == "stop":
                running = False
        
        
    

class Database_manager:
    def __init__(self, database):
        self.db = database
    
    def add_stat(self, im_stat):
        self.db.append(im_stat)
        
    def save_to_file(file):
        return #do this eventually

    """
    Runs the database manager process. It takes requests from db_add_pipe to
    add items to the database, then sends confirmation through the db_response_pipe.
    """
def run_database_manager(database, db_add_pipe, db_response_pipe, shell_pipe):
    dbm = Database_manager(database)
    running = True
    
    while running:
        if db_add_pipe[1].poll(3):
            req = db_add_pipe[1].recv() #[0]: post request, [1]: image stats.
            title = get_metadata_val(req[0].data, "title")
            artist = get_metadata_val(req[0].data, "artist")
            metadata_str = ""
            if title:
                metadata_str = metadata_str + "Title: " + title + "\n"
            if artist:
                metadata_str = metadata_str + "Artist: " + artist + "\n"
            req[1][0] = metadata_str + "!"
            print(req[1])
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(dbm.db[3])
            dbm.add_stat(req[1])
            
            print("db add success on req id " + str(req[0].req_id))
            res = Post_response(req[0], "SUCCESS")
            db_response_pipe[0].send(res)
        
        if shell_pipe[1].poll(0.01):
            command = shell_pipe[1].recv()
            if command.text == "stop":
                running = False

    """
    Starts the server process. This function takes GET and POST requests and
    sends post requests to other processes through the pipe.
    database: database the server is running on. May not be necessary, consider removing.
    port: port the server will run on.
    req_pipe: pipe to send Post_request objects through.
    """
    #Maybe put the socket outside this function, so other processes can access it?
def run_server(database, port, request_pipe, server_response_pipe, shell_pipe):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', port))
    serverSocket.listen(10)
    
    cur_post_id = 0
    
    #All requests that have been "solved" by the server and are awaiting being sent back.
    avail_responses = []
    
    running = True
    
    while running:
        connectionSocket, addr = serverSocket.accept()
        connectionSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 21)
        
        message = connectionSocket.recv(1024)
        message = message.decode()
        msg_split = message.split(" ")
        
        if msg_split[0] == "GET":            
            print("Accepted GET request from IP" + str(addr) + "\n")
            try:
                request = msg_split[1][1:]
                print("Request: " + request)
                
                if request == "newid":
                    print("New ID requested")
                    connectionSocket.send("HTTP/1.x 200 OK\n".encode())
                    connectionSocket.send("Content-Type: text/html\n\n".encode())
                    connectionSocket.send(str(cur_post_id).encode())
                    cur_post_id += 1
                
                elif request[:2] == "id":
                    print("ID requested: " + request[2:])
                    response = Post_response(None, None)
                    for i in range(len(avail_responses)):
                        res = avail_responses[i]
                        print(str(res.req.req_id))
                        if str(res.req.req_id) == request[2:]:
                            response = res
                            avail_responses.remove(res)
                    if response.req == None:
                        while server_response_pipe[1].poll(0.01):
                            new_response = server_response_pipe[1].recv()
                            print(new_response.req.req_id)
                            if str(new_response.req.req_id) == request:
                                response = new_response
                            else:
                                avail_responses.append(new_response)
                                
                    if not response.req.error == "":
                        connectionSocket.send("Error: Unable to process.".encode())
                    elif response.req == None:
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
                    
                    for i in range(len(response)):
                        try:
                            connectionSocket.send(response[i].encode())
                        except:
                            print("Error sending response to ", addr)
                else:
                    connectionSocket.send("HTTP/1.x 404 Not Found\r\n".encode())

            except:
                connectionSocket.send("HTTP/1.x 404 Not Found\n".encode())
            
        elif msg_split[0] == "POST":
            print("Accepted POST request from IP" + str(addr) + "\n")
            connectionSocket.send("HTTP/1.x 200 OK\n".encode())
            connectionSocket.send("Content-Type: text/html\n\n".encode())
            try:
                data = message.split("METADATA:")[1]
                gram = connectionSocket.recv(4096).decode()
                #print(data)
            except:
                data = ""
                gram = ""
            
            data += gram
            #print("Got first gram")
            while not gram[-3:] == "!!!":
                try:
                    gram = connectionSocket.recv(4096).decode()
                    data += gram
                    #print(gram)
                except IndexError as e:
                    print(e)
                    print(gram)
            data = data[:-3]
            data_type = get_metadata_val(data, "data_type").upper() #IMG_DATA or URL
            req_type = get_metadata_val(data, "request_type").upper() #ADD or IDENTIFY
            req_id = get_metadata_val(data, "request_id")
            
            print("Post request ID: " + str(req_id))
            
            request = Post_request(data, data_type, req_type, req_id)
            request_pipe[0].send(request)
            
            
        connectionSocket.close()
        
if __name__ == "__main__":
    dbfile = open("imstat.txt", "r")
    db = rdl.load_data_file(dbfile)
    
    request_pipe = mp.Pipe()
    db_add_pipe = mp.Pipe()
    db_response_pipe = mp.Pipe()
    identify_response_pipe = mp.Pipe()
    server_response_pipe = mp.Pipe()
    shell_pipe = mp.Pipe()
    
    server_proc = mp.Process(target = run_server, args = (db, 6501, request_pipe, server_response_pipe, shell_pipe))
    req_handler_proc = mp.Process(target = run_request_handler, args = (db, 0, request_pipe, identify_response_pipe, db_add_pipe, shell_pipe))
    db_manager_proc = mp.Process(target = run_database_manager, args = (db, db_add_pipe, db_response_pipe, shell_pipe))
    res_handler_proc = mp.Process(target = run_response_handler, args = (identify_response_pipe, db_response_pipe, server_response_pipe, shell_pipe))
    
    server_proc.start()
    req_handler_proc.start()
    db_manager_proc.start()
    res_handler_proc.start()

    server_proc.join()
    print("server process joined")
    req_handler_proc.join()
    print("request handler joined")
    db_manager_proc.join()
    print("database manager joined")
    res_handler_proc.join()
    print("response handler joined")
    