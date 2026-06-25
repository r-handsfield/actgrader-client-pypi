# Class Definition for ActGrader Client
#
# This module builds to PyPI and should remain concurrent with
# /source/classes/client.py

import os, sys, _io
import pathlib
import requests
import warnings

from os.path import join
from pathlib import Path
from requests import Response
from typing import NoReturn, Union, Tuple



class GraderClient():
    """
    A client for accessing the Act Grader service. 

    Public Attributes
    -----------------
    url : str
        The remote url of the Grader service. Ex: https://actgrader.com

    oauth : str
        An OAuth2 token

    uri : str
        A unique string that allows the Grader to identify a specific answer
        sheet. 

    download_directory : str | Path
        The folder where the downloaded answers and confirmation image should go.

    Public Methods
    --------------
    __init__(url, oauth) -> NoReturn
        Constructs a GraderClient object. The url and OAuth2 token are required.

    upload_image(path) -> (Response, uri)
       Uploads an answer sheet image to the Grader, but does not initiate any
       scanning or processing. 

       Returns the HTTP Response and the URI to the answer sheet's directory.

    process_image(uri) -> (Response, uri)
        Processes the answer sheet and creates the confirmation image and 
        marked answers json, but does not download anything.

        Returns the HTTP Response and the URI to the answer sheet's directory.

    download_marked_answers(file_path, uri) -> (Response, filepath)
        Downloads the marked answers as a json file.

        Returns the HTTP Response and the path to the downloaded file.

    download_confirmation_image(file_path, uri) -> (Response, filepath)
        Downloads the confirmation image as a jpg file. 

        Returns the HTTP Response and the path to the downloaded file.

    update_marked_answers(path, uri) -> (Response, uri)
       Replaces the Grader's marked answers json with an updated json file.

       Returns the HTTP Response and the URI to the answer sheet's directory.

    """

    def __init__(self, url: str, oauth: str) -> NoReturn:
        """
        The GraderClient constructor.

        Parameters
        ----------
        url : str
            The remote url of the Grader service. Ex: https://actgrader.com

        oauth : str
            An OAuth2 token
        """
        self.validate_url(url)
        self.validate_oauth(oauth)

        self.url = url
        self.oauth = oauth
        self.uri = None
        self.download_directory = None

        self.__endpoints = {
            'upload_image':'api/upload/image',
            'process_image':'api/process/image',
            'download_marked_answers': 'api/download/marked_answers',
            'download_confirmation_image': 'api/download/confirmation_image',
            'update_marked_answers' : 'api/update/marked_answers'
        }


    def validate_url(self, url: str) -> bool:
        """
        Checks whether a URL string is valid and returns True if it is. If the
        string is invalid, one of the following errors is raised.

        Parameters
        ----------
        str : url
           A string representing the internet address of the actgrader api. The
           url must contain either 'http://' or 'https://' as a prefix.

        Raises
        ------
        TypeError       URL is not str type 
        ValueError      URL is None
        ValueError      Missing 'http://'
        ValueError      Missing 'https://'

        Returns
        -------
        bool
            True if the url is a string beginning with a full http prefix.
        """
        if url is None:
            raise ValueError("The URL is currently None. Try passing the URL explicitly.\n")

        elif not isinstance(url, str):
            raise TypeError("The URL must be a string.\n")

        elif url[0:7] != 'http://' and url[0:8] != 'https://':
            print('\n', url, url[0:8], url[0:8], '\n', sep='\n')
            raise ValueError(f"The URL {url} is missing a 'http://' or 'https://' prefix.\n")

        elif False:
            m = f"The URL {url} appears to be invalid. "
            m += "It must be of the following forms\n"
            m += "http://some.ip.address \n"
            m += "https://some.ip.address \n"
            m += "http://some.domain.com \n"
            m += "https://some.domain.com \n\n"
            raise ValueError(m)

        return True


    def validate_oauth(self, oauth: str) -> bool:
        """
        Checks whether an oauth string is valid and returns True if it is. If 
        the string is invalid, one of the following errors is raised.

        Parameters
        ----------
        str : url
           A string representing the internet address of the actgrader api. The
           url must contain either 'http://' or 'https://' as a prefix.

        Raises
        ------
        TypeError       OAuth is not str type 
        ValueError      OAuth is None

        Returns
        -------
        bool
            If the OAuth string is an str type.
        """
        if oauth is None:
            raise ValueError("The OAuth is currently None. Try passing it explicitly.")
        elif not isinstance(oauth, str):
            raise TypeError("The OAuth must be a string.")

        return True


    def validate_image_path(self, path: Union[str, Path]) -> bool:
        """
        Checks whether the image file exists and has a valid extension and 
        raises FileNotFoundErrors if it isn't.

        Extension must be one of jpg, jpeg, png, tif, tiff.

        Parameters
        ----------
        str | pathlib.PurePath
            The full path to the image file as string or posix path.

        Raises
        ------
        TypeError               The path is not a string or posix path
        FileNotFoundError       The file does not exist
        FileNotFoundError       The file has the wrong extension

        Returns
        -------
        bool
            True if the file exists and has a valid image extension.
        """
        if not(isinstance(path, str) or isinstance(path, pathlib.PurePath)):
            raise TypeError("The image path must be a string or posix path.")

        name, ext = os.path.splitext(path)
        
        if not (ext[1:] in ('jpg', 'jpeg', 'png', 'tif', 'tiff', 'heic')):
            raise FileNotFoundError("The image file must have a jpg, png, or tif extension.")
        elif not os.path.exists(path):
            raise FileNotFoundError(f"The image file {path} does not appear to exist.")

        return True


    def validate_uri(self, uri: str) -> bool:
        """
        Checks that the URI is of string type.

        A correct URI is returned by self.upload_image(), so don't mess with 
        it, and you won't have problems. 

        Parameters
        ----------
        uri : str
            A uniform resource identifier to an image stored on the grader 
            service server.

        Raises
        ------
        TypeError       If the URI is not a string

        Returns
        -------
        bool
            True if the URI is a string. 
        """
        if uri is None:
            raise ValueError("The URI is currently None. Try passing it explicitly.")
        elif not isinstance(uri, str):
            raise TypeError("The URI must be a string.")

        # Check that URI has proper schema - NOT IMPLEMENTED for security
        # reasons.

        return True


    def validate_path(self, path: Union[str, Path], extension: str) -> bool:
        """
        Checks that the directory exists and the destination path terminates 
        in the proper extension.

        The GraderClient contains methods to download files from the Grader 
        Service to a user-specified location. This validator ensures that the
        destination file can receive the data without errors.

        Parameters
        ----------
        path : str | pathlib.PurePath
            path/to/destination/location/file.ext

        extension: str
            The desired file extension WITHOUT the leading period.

            Ex: json, jpg, etc.  NOT  .json, .jpg, etc.

        Raises
        ------
        TypeError           If the path is not a string or Path object
        FileNotFoundError   If the directory does not exsist
        ValueError          If the specified file has the wrong extension

        Returns
        -------
        bool
            True if the path exists and terminates in a correct extension.
        """
        if not (isinstance(path, str) or isinstance(path, pathlib.PurePath)):
            raise TypeError(f"The path {path} must be a string or posix path.")

        directory = os.path.dirname(path)
        _, ext = os.path.splitext(path)
        ext = ext[1:]
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"The directory '{directory}' does not appear to exist.")

        if (ext == '') or (not ext == extension):
            raise ValueError(f"To properly receive data, the destination file must have a {extension} extension.")

        return True


    def validate_file_cursor(self, file_handle: _io.BufferedReader) -> bool:
        """
        When the GraderClient is used within certain application frameworks,
        (looking at you Flask) the framework might move the image's file cursor 
        to the final bit before passing it into `self.upload_image()`. 
        This method checks the cursor position, and if the cursor is not at 
        position 0, sends a Warning and returns False.

        This method operates on open files, so it should be used within an open
        file context:

        with open("path/to/my_file.ext", 'rb') as f:
            gc.validate_file_cursor(f)

        OR

        f = open("path/to/my_file.ext", 'rb')
        gc.validate_file_cursor(f)
        f.close()

        Parameters
        ----------
        file_handle : _io.BufferedReader
            A pointer to an open file being read as bytes. The file must be 
            opened with the 'rb' (read-bytes) argument.

        Warnings
        --------
        Warn        If the file's cursor is not at postion 0

        Returns
        -------
        bool
            True    If the file's cursor is at position 0
            False   If the file's cursor is NOT at position 0
        """
        
        if file_handle.tell() == 0:
            return True
        else:
            m = f"\nThe file cursor is at position {file_handle.tell()} when it should be at position 0.\n"
            m += "This can cause problems during processing. Try running file.seek(0) before\n"
            m += "passing the file to the GraderClient."
            warnings.warn(m)
            return False

    
   # @TODO write this unit test
    def verify_endpoint(self, endpoint: str=None, url: str=None):
        """
        Sends an HTTP GET request to the specified url and endpoint. If the 
        HTTP response is 200, the API service is running and the endpoint is 
        listening.

        If an endpoint is not specified, the '/api/upload/image' endpoint is requested.
   
        Parameters
        ----------
        endpoint : str | None
            A valid endpoint of the form '/api/operation/resource'. If the 
            endpoint is None, the endpoint '/api/upload/image' is verified.
            Refer to the API docs for a list of endpoints.

        url : str | None
            The Grader's URL. If None, tries to read from self.url

        Returns
        -------
        requests.Response | None
            An HTTP response; contains the status code and additional data. If 
            the API cannot be reached, and HTTP response cannot be creaated and
            None is returned.

        str 
            A human-readable message about the verification results.
        """
        if url is None:
            url = self.url

        self.validate_url(url)

        if endpoint is None:
            endpoint = self.__endpoints['upload_image']

        # validate endpoint -- @TODO write the validation method
        if endpoint[0] == '/': endpoint = endpoint[1:] # strip leading / if necessary

        if endpoint not in self.__endpoints.values():
            m = f"{endpoint} is not a valid ACT Grader endpoint. "
            m += "Refer to the API docs or pass 'endpoint=None'."
            raise ValueError(m)
        else:
            pass

        
        try:
            ### HTTP Request ###
            response = requests.get(self.join_endpoint(url, endpoint))

            if response.status_code == 200:
                message = f"The ACT Grader API is running at:  {url}\n"
                message +=f"   and listening at the endpoint:  {endpoint}\n"
            else:
                message = f"The ACT Grader API at {url + '/' + endpoint} does not appear to be running and returned an HTTP status code of {response.status_code}\n."
        except Exception as e:
            response = e
            message = f"Fatal Error: The ACT Grader API could not be reached at {url + '/' + endpoint}.\n\n"
            message += f"This could mean that \n  (1) The API is not running \n" 
            message += f"  (2) The URL or endpoint are incorrect.\n"
            message += f"  (3) A network error is preventing you from connecting to the API.\n"
            message += f"  (4) There are errors in the URL or endpoint. Check the spellings. \n\n"
            message += str(e)

            return e, message

        return response, message
 

    def join_endpoint(self, url: str, endpoint: str) -> str:
        """
        Adds api endpoint to the base URL and returns the concatenation as a 
        string. Raises a TypeError if the URL is not a string.

        Parameters
        ----------
        url : str 
            The base url hosting the ACT Grader

        endpoint : str
            A specifed api endpoint

        Returns
        -------
        Path
            The base URL concatenated with the endpoint
            Ex: https://grader.com/api/download/marked_answers
        """
        if isinstance(url, str):
            url = join(url, endpoint)  
        else:
            raise TypeError("The URL must be a string.")

        if not isinstance(endpoint, str):
            raise TypeError("The endpoint must be a string.")

        return url


    def upload_image(self,
                        path: Union[str, Path], 
                        url: str=None, 
                        oauth: str=None 
    ) -> Tuple[Response, Union[str, None]]:
        """
        Uploads an answer sheet image to the grader. There are no checks to 
        determine whether an image is a valid answer sheet. Uploading creates
        a new resource.
        
        Parameters
        ----------
        path : str | Path
            path/to/image.jpg
            The file must be jpg, jpeg, or png

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        Returns
        -------
        requests.Response
            An HTTP response; contains the status code and additional data.

        str | None
            The URI -- the address of the resource on the grader server.
            If the client or server encounters an error, None is returned.
        """
        self.validate_image_path(path)
        endpoint = self.__endpoints['upload_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth

        self.validate_url(url)
        self.validate_oauth(oauth)

        url = self.join_endpoint(url, endpoint)

        name_img = os.path.basename(path)

        with open(path, 'rb') as f:
            # if the image's cursor is not at zero for some dumb reason,
            # send a warning and reset the cursor
            if not self.validate_file_cursor(f):
                f.seek(0)

            img_data = f.read()
            files = {'file': (name_img, img_data)}

            ### HTTP Request ###
            response = requests.post(url, files=files)

        if response.status_code == 200:
            return response, response.json()['uri']
        else:
            return response, None


    def process_image(self, 
                        uri: str=None,
                        url: str=None, 
                        oauth: str=None 
    ) -> Tuple[Response, Union[str, None]]:
        """
        Triggers image processing on the server, which 
        (1) Extracts the marked answers and writes them to a json file.
        (2) Generates a confirmation image.

        This method does not download the generated files. Use the download methods 
        to do that.
 
        Parameters
        ----------
        uri : str
            The resource's unique identifier on the server

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        Returns
        -------
        requests.Response
            An HTTP response; contains the status code and additional data.

        str | None
            The URI -- the address of the resource on the grader server.
            If the client or server encounters an error, None is returned.
        """
        endpoint = self.__endpoints['process_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri

        self.validate_url(url)
        self.validate_oauth(oauth)
        self.validate_uri(uri)
        
        url = self.join_endpoint(url, endpoint)
        values = {'uri': uri}

        ### HTTP Request ###
        response = requests.post(url, data=values)

        
        if response.status_code == 200:
            return response, response.json()['uri']
        else:
            return response, None


    # @TODO write this unit test
    def update_marked_answers(self,
                                path: Union[str, Path], 
                                uri: str=None,
                                url: str=None, 
                                oauth: str=None 
    ) -> Tuple[Response, Union[str, None]]:
        """
        Overwrites the json file of marked answers on the remote server. 

        Intended to be used when the computer vision engine has made a mistake
        and a marked answer needs to be corrected. 
        
 
        Parameters
        ----------
        path : str | Path
            path/to/marked/answers.json

        uri : str
            The resource's unique identifier on the server

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        Returns
        -------
        requests.Response
            An HTTP response; contains the status code and additional data.

        str | None
            The URI -- the address of the resource on the grader server.
            If the client or server encounters an error, None is returned.
        """
        endpoint = self.__endpoints['update_marked_answers']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri
        
        url = self.join_endpoint(url, endpoint)
        values = {'uri': uri}

        with open(path, 'rb') as f:
            json_data = f.read()
            files = {'file': ("updated_answers.json", json_data)}

            ### HTTP Request ###
            response = requests.put(url, data=values, files=files)

        
        if response.status_code == 200:
            return response, response.json()['uri']
        else:
            return response, None


    def download_marked_answers(self, 
                                path: Union[str, Path],
                                uri: str=None,
                                url: str=None, 
                                oauth: str=None,
    ) -> Tuple[Response, Union[str, None]]:
        """
        Downloads marked answers as a json file.
  
        Parameters
        ----------
        path : str
            path/to/download/directory/answers.json

        uri : str
            The resource's unique identifier on the server

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        Returns
        -------
        requests.Response
            An HTTP response; contains the status code and additional data.

        str | None
            The destination file path.
            If the client or server encounters an error, None is returned.
        """
        endpoint = self.__endpoints['download_marked_answers']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri

        self.validate_path(path, 'json')
        self.validate_uri(uri)
        self.validate_url(url)
        self.validate_oauth(oauth)
        
        url = self.join_endpoint(url, endpoint)
        values = {'uri': uri}

        ### HTTP Request ###
        response = requests.post(url, data=values)

        
        if response.status_code == 200:
            if isinstance(response.content, bytes):
                with open(path, 'wb') as f:
                    f.write(response.content)
                return response, path
            else: 
                raise Warning("The http request returned a response, but it does not appear to contain a json file. Examine 'response.content' to determine what was actually returned.")
            return response, None
        elif response.status_code == 500:
            raise FileNotFoundError(f"The extracted answers could not be found at the URI {uri}. Verify that you are using the exact URI returned by `GraderClient.process_image()`.")
        else:
            return response, None




        pass

    
    # @TODO write this unit test
    def download_confirmation_image(self, 
                                    path: Union[str, Path],
                                    uri: str=None,
                                    url: str=None, 
                                    oauth: str=None
    ) -> Tuple[Response, Union[str, None]]:
        """
   
        Parameters
        ----------
        path : str
            path/to/download/directory/image.jpg

        uri : str
            The resource's unique identifier on the server

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        Returns
        -------
        requests.Response
            An HTTP response; contains the status code and additional data.

        str | None
            The marked answers as json. 
            If the client or server encounters an error, None is returned.
        """
        endpoint = self.__endpoints['download_confirmation_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri

        self.validate_path(path, 'jpg')
        self.validate_uri(uri)
        self.validate_oauth(oauth)
        self.validate_url(url)
        
        url = self.join_endpoint(url, endpoint)
        values = {'uri': uri}

        ### HTTP Request ###
        response = requests.post(url, data=values)
        
        if response.status_code == 200:
            if isinstance(response.content, bytes):
                with open(path, 'wb') as f:
                    f.write(response.content)
                return response, path
            else: 
                raise Warning("The http request returned a response, but it does not appear to contain an image file. Examine 'response.content' to determine what was actually returned.")
            return response, None
        elif response.status_code == 500:
            raise FileNotFoundError(f"The confirmation image could not be found at the URI {uri}. Verify that you are using the exact URI returned by `GraderClient.process_image()`.")
        else:
            return response, None


    