# Class Definition for ActGrader Client
#

import os, sys
import pathlib
import requests

from os.path import join
from pathlib import Path
from requests import Response
from typing import NoReturn, Union


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


    def join_endpoint(self, url: Union[str, pathlib.Path], endpoint: str) -> pathlib.Path:
        """
        Adds api endpoint to the base URL and returns the concatenation as a 
        Pathlike (PosixPath) object. This method also handles URLs as strings
        or Paths. Raises a TypeError if the URL is neither string nor Path.

        Parameters
        ----------
        url : str or Path
            The base url hosting the ACT Grader

        endpont : str
            A specifed api endpoint

        Returns
        -------
        Path
            The base URL concatenated with the endpoint
            Ex: https://grader.com/api/download/marked_answers
        """

        # @TODO Replace Path calls with urllib or something b/c Path is only
        # appropriate for INTERNAL pathing, not http addresses. 
        if isinstance(url, str):
            url = join(url, endpoint)  
        elif isinstance(url, pathlib.PurePath):
            url = url / endpoint
        else:
            raise TypeError("The URL must be a string or a valid Path object.")

        if not isinstance(endpoint, str):
            raise TypeError("The endpoint must be a string.")

        return url

    

    # @TODO write this unit test
    def upload_image(self,
                        path: Union[str, Path], 
                        url: Union[str, Path]=None, 
                        oauth: str=None 
    ) -> Tuple[Response, Union[str, None]]:
        """
        
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
        http response

        str | None
            The URI
        """
        endpoint = self.__endpoints['upload_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth

        # @TODO Replace Path calls with urllib or something b/c Path is only
        # appropriate for INTERNAL pathing, not http addresses.    
        if isinstance(url, str):
            # url = Path(url) / endpoint
            url = join(url, endpoint)
        elif isinstance(url, pathlib.PurePath):
            url = url / endpoint
        else:
            raise TypeError("The URL must be a string or a valid Path object.")
        print(url)
            
        with open(path, 'rb') as f:
            img_data = f.read()
            files = {'file': ("aOriginal.jpg", img_data)}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            return response, response.json()['uri']
        else:
            return response, None


    # @TODO write this unit test
    def process_image(self, 
                        url: str=None, 
                        oauth: str=None, 
                        uri: str=None
    ) -> Tuple[Response, Union[str, None]]:
        """
        Triggers image processing on the server, which 
        (1) Extracts the marked answers and writes them to a json file.
        (2) Generates a confirmation image.

        This method does not download the generated files. Use the download methods 
        to do that.
 
        Parameters
        ----------
        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        uri : str
            The resource's unique identifier on the server

        Returns
        -------
        http response

        str | None
            The URI
        """
        endpoint = self.__endpoints['process_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri
        
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
                                url: str=None, 
                                oauth: str=None, 
                                uri: str=None
    ) -> Tuple[Response, Union[str, None]]:
        """
        Overwrites the json file of marked answers on the remote server. 

        Intended to be used when the computer vision engine has made a mistake
        and a marked answer needs to be corrected. 
        
 
        Parameters
        ----------
        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        uri : str
            The resource's unique identifier on the server

        path : str | Path
            path/to/marked/answers.json

        Returns
        -------
        http response

        str | None
            The URI
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




    # @TODO write this unit test
    def download_marked_answers(self, 
                                path: Union[str, Path]=None,
                                url: str=None, 
                                oauth: str=None, 
                                uri: str=None
    ) -> Tuple[Response, Union[str, None]]:
        """
        Downloads marked answers as a json file
  
        Parameters
        ----------
        path : str
            path/to/download/directory/answers.json

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        uri : str
            The resource's unique identifier on the server

        Returns
        -------
        http response

        str | None
            The destination file path
        """
        endpoint = self.__endpoints['download_marked_answers']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri
        
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
        else:
            return response, None




        pass

    
    # @TODO write this unit test
    def download_confirmation_image(self, 
                                    path: Union[str, Path],
                                    url: str=None, 
                                    oauth: str=None, 
                                    uri: str=None
    ) -> Tuple[Response, Union[str, None]]:
        """
   
        Parameters
        ----------
        path : str
            path/to/download/directory/image.jpg

        url : str
            The Grader's URL. If None, tries to read from self.url

        oauth : str

        uri : str
            The resource's unique identifier on the server

        Returns
        -------
        http response

        str | None
            The marked answers as json
        """
        endpoint = self.__endpoints['download_confirmation_image']

        if url is None:
            url = self.url
        if oauth is None:
            oauth = self.oauth
        if uri is None:
            uri = self.uri
        
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
        else:
            return response, None




