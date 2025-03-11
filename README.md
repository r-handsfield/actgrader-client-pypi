# ACT Grader Client
Client for interfacing with the ACT Grader API

## Summary
The **GraderClient** sends HTTP Requests to the Grader Service (**Grader**) to trigger the different stages of a grading process: 

1. Upload an **Answer Sheet Image** to the Grader
2. Process the Answer Sheet and create the output files:
        - The list of answers marked on the sheet (**Marked Answers**)
        - A **Confirmation Image** showing which bubbles were identified by the Grader. The Confirmation Image is used to check the Grader's accuracy and make corrections when necessary.
3. Download the Marked Answers (as a json file)
4. Download the Confirmation Image (as a file)


To accomplish the 4 grading actions, the GraderClient requires 3 pieces of information (url, oauth, uri) and provides 4 methods (upload_image, process_image, download_marked_answers, download_confirmation_image).

### Attributes
- URL: The url to the grader service. Ex: https://some_act_grader_service.com
- OAuth: An OAuth2 token, used for security purposes.
- URI: The unique address of the answer sheet, marked answers, and confirmation image on the grader service (Grader).

### Methods
- `upload_image(path)`: Uploads the answer sheet to the Grader
- `process_image(uri)`: Identifies the filled bubbles on the answer sheet and creates the Marked Answers and Confirmation Image files. 
- `download_marked_answers(filepath, uri)`: Downloads the marked answers to the specified `filepath`. The `filepath` must end in a json extension. Ex. `C:\\Desktop\marked_answers.json` 
- `download_confirmation_image(filepath, uri)`: Downloads the confirmation image to the specified `filepath`. The `filepath` must end in a jpg extension. Ex. `C:\\Desktop\confirmation_image.jpg` 

### Creating the GraderClient Object
The GraderClient requires a url and an oath token during creation. They do not need to be explicitly passed to the object's methods. 

Uploading an image returns a URI; explicitly assigning that URI to the GraderClient object makes the other method calls simpler:

```python
gc = GraderClient(my_url, my_oauth)
response, uri = gc.upload_image('my_answer_sheet.jpg')
gc.uri = uri

_, _ = gc.process_image()

_, _ = gc.download_marked_answers('my_answers.json)

```


## Example Code
```python
from graderclient import GraderClient

url = "https://some_act_grader_service.com"
oauth = "h5Kafh-egN3HyfEjpbKfg2VU"

gc = GraderClient(url, oauth)

upload_response, uri = gc.upload_image("my_image.jpg")

gc.uri = uri

process_response, uri = gc.process_image()

download_ma_response, path = gc.download_marked_answers("./answers.json")

download_ci_response, path = gc.download_confirmation_image("./confrmation.jpg")
```


