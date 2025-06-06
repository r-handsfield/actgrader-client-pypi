# Class Definition for ActGrader Client
#

import os, sys
import pathlib
import requests

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
            If the string is a string beginning with a full http prefix.
        """
        if url is None:
            raise ValueError("The URL is currently None. Try passing the URL explicitly.")
        elif not isinstance(url, str):
            raise TypeError("The URL must be a string.")
        elif url[0:7] == 'http://' or url[0:8] == 'https://':
            pass
        else:
            raise ValueError(f"The URL {url} does not appear to have a properly formed 'http://' or 'https://' prefix")

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
        
        if not (ext[1:] in ('jpg', 'jpeg', 'png', 'tif', 'tiff')):
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


    def validate_path(self, 
            path: Union[str, Path],
            extension: str
        ) -> bool:
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

        with open(path, 'rb') as f:
            img_data = f.read()
            files = {'file': ("aOriginal.jpg", img_data)}
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




