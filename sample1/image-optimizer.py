"""
The image-optimizer script parses a text file containing newline-separated image URLs and
sends a request for optimization to the user-specified RESTful API endpoint for 
processing. Upon completion, the modified image is saved to a locally-specified 
directory.

Usage:   python image-optimizer.py [textLocation] [saveImageLocation]
Example: python image-optimizer.py images.txt     ./tmp/
"""

import os, sys
import time
import argparse
import requests
import urllib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

###################
# Config Settings
###################

"""
User & Password are used as authentication 
for the image-optimizer service
"""
user = "sample_user_name"
password = "sample_password"

"""
The timeout setting specifies, in seconds, the 
upper bound for each API request. If this time is
exceeded, then the method call to the API endpoint
unblocks and returns false. 
"""
timeout = 10

"""
Specify the directory where logs are saved
"""
logPath = "./logs/"

####################
# Data Definitions
####################

####################
# Error Definitions
####################

class FileNotFoundException(Exception):
    pass
    
class FailedOptimizationStatusException(Exception):
    pass

#################
# Helper Methods
#################

def checkPath(path):
    if not os.path.exists(path):
        raise FileNotFoundException(path)
        
def createSavePathIfNotExist(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def optimizeImage(url, path):
    serviceUrl = 'sample_api_service_endpoint'
    
    try: 
        req = requests.post(serviceUrl, json = constructRequestBody(url), auth = (user, password), timeout = timeout)
        logging.info(req.text)
       
        if req.status_code == 200:
            json = req.json()
            token = json["data"][0]["token"]
            while checkRequestStatusNotComplete(token):
                time.sleep(timeout)
            retrieveModifiedImage(token, path)
        else:
            return False, url
    except requests.exceptions.Timeout as e:
        print("image-optimizer: post request timed out for {}".format(url))
        return False, url
    except FailedOptimizationStatusException as e:
        print("image-optimizer: failed to optimize image for token {}".format(str(e)))
        return False, url
    except Exception as e:
        print("image-optimizer: post request encountered other error [{}]".format(str(e)))
        return False, url
        
    return True, url
    
def checkRequestStatusNotComplete(token):
    serviceUrl = 'sample_api_service_endpoint' + token + '/status'
    
    try:
        req = requests.get(serviceUrl, auth = (user, password), timeout = timeout)
        logging.info(req.text)
        
        if req.status_code == 200:
            json = req.json()
            status = json["data"][0]["status"]
            if status == "complete":
                return False
            elif status == "failed":
                raise FailedOptimizationStatusException(token)
            else:
                return True
    except requests.exceptions.Timeout as e:
        print("image-optimizer: GET status request timed out for token {}".format(token))
        raise e
    except FailedOptimizationStatusException as e:
        raise e
    except Exception as e:
        print("image-optimizer: GET status request encountered other error [{}]".format(str(e)))
        raise Exception(e)
        
def retrieveModifiedImage(token, path):
    serviceUrl = 'sample_api_service_endpoint' + token
    
    try:
        req = requests.get(serviceUrl, auth = (user, password), timeout = timeout)
        logging.info(req.text)
        json = req.json()
        modifiedUrl = json["data"][0]["sampleAttribute"][0]["images"][0]["modifiedUrl"]
        fileName = path + modifiedUrl.split('/')[-1]
        urllib.request.urlretrieve(modifiedUrl, fileName)
    except requests.exceptions.Timeout as e:
        print("image-optimizer: GET request timed out for token {}".format(token))
        raise e
    except Exception as e:
        print("image-optimizer: GET request encountered other error [{}]".format(str(e)))
        raise Exception(e)
    
    
def constructRequestBody(url):
    return {"sampleId":77777, "items": [{"id": 123, "images":[{"imageId":987456, "imageUrl":url}]}]}

######################
# Program Entry Point
######################

def main():
    parser = argparse.ArgumentParser(description="Optimize a collection of images using a RESTful API service")
    parser.add_argument('fileLocation', metavar="fLoc", type=str, help="Specifies the directory of text file, relative to image-optimizer.py, containing images to optimize")
    parser.add_argument('saveLocation', metavar="sLoc", type=str, help="Specifies the directory, relative to image-optimizer.py, to store the optimized images")
    args = parser.parse_args()
    
    filePath = vars(args)["fileLocation"]
    savePath = vars(args)["saveLocation"]
    
    try:
        checkPath(filePath)
        createSavePathIfNotExist(savePath)
        createSavePathIfNotExist(logPath)
        
        fName = logPath + str(datetime.now()).replace(".", "-").replace(":", "-") + ".log"
        print("image-optimizer: optimization script is currently running")
        
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', filename = fName, level = logging.DEBUG)
        logging.info("Started logging")
        
        with open(filePath, 'r') as f:
            imageURLs = [line.rstrip() for line in f.readlines()]
        
        with ThreadPoolExecutor(max_workers = len(imageURLs)) as executor:
            futures = [executor.submit(optimizeImage, imageURL, savePath) for imageURL in imageURLs]
            
            for future in as_completed(futures):
                result = future.result()
                if result[0]:
                    print("image-optimizer: Finished processing image [{}]".format(result[1]))
                else:
                    print("image-optimizer: Unable to process image [{}]".format(result[1]))
        
        logging.info("Stopped logging")
    except FileNotFoundException as e:
        print("image-optimizer: Unable to find the file[{}]".format(str(e)))
        sys.exit(0)
    except Exception as e:
        print("image-optimizer: Caught unexpected error [{}]".format(str(e)))
        sys.exit(0)
    
if __name__ == "__main__":
    main()