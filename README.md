# MediStream: Medical Document Processing System

## What Is This Project?

Imagine a hospital receives hundreds of patient documents every day. These documents contain
information about what medications a patient is taking, their medical history, dates of events,
dosages, and much more. Right now, a human specialist reads each document, manually extracts
this information, looks up drug codes, maps conditions to international classification systems,
and then types everything into a structured spreadsheet or database. This process is slow,
expensive, and prone to human error.

MediStream automates this entire workflow. You upload a document, and the system reads it,
understands it, looks up the correct medical codes, arranges everything in chronological order,
and produces a clean, standards-compliant XML file and a formatted Excel workbook. All of this
happens in seconds, without a human typing anything.

## Who Is This For?

This system is intended for clinical research organizations, pharmacovigilance teams, hospital
data departments, Insurance processing units and clinical trial coordinators who deal with unstructured medical documents
and need to produce structured, coded outputs in standardized formats. 

You do not need to be a programmer to use MediStream once it is running. You only need a web
browser and a document to upload.


## What Happens to Your Document?

When you upload a document, it goes through five stages automatically.

Stage one is extraction. The system reads the document, whether it is a scanned image, a PDF,
or a text file, and identifies every medication and medical history event mentioned. It also
resolves ambiguous dates. For example, if the document says "started 6 months ago", the system
calculates the actual calendar date and records it properly.

Stage two is coding. The system takes every medication name it found and looks up its official
generic name and chemical composition. It also maps every medical history event to its correct
position in the MedDRA international medical terminology hierarchy, which is the global standard
used by regulatory agencies like the FDA and EMA.

Stage three is timeline building. The system arranges all extracted events in chronological
order, from the earliest to the most recent, including when medications were started and stopped,
and when medical conditions began or resolved.

Stage four is output generation. The system writes a structured XML file and a formatted Excel
workbook containing all the extracted and coded information, organized into logical sheets.

Stage five is quality review. A second AI pass reads both the original document and the
generated XML side by side and checks for any discrepancies, missed items, or hallucinated
information that was not actually in the source document. It flags any issues it finds.


## What You Will Need Before Starting

You need three things before you can run MediStream.

The first is Docker. Docker is a free program that packages software so it runs the same way
on any computer, regardless of the operating system. Think of it as a self-contained box that
contains everything the application needs to run. You do not need to install Python or any other
programming language manually. Docker handles all of that.

Download Docker Desktop from https://www.docker.com/products/docker-desktop and install it
like any normal application. Once installed, open Docker Desktop and leave it running in the
background. You will know it is running when you see the Docker whale icon in your taskbar or
menu bar.

The second thing you need is a Gemini API key. This is the key that gives MediStream access to
Google's Gemini 1.5 Pro language model, which is the AI that reads and understands your
documents. To get one, go to https://aistudio.google.com, sign in with a Google account, and
click "Get API key". Copy the key and keep it somewhere safe. 

The third thing you need is a LangSmith API key. LangSmith is an observability platform that
records what the AI is doing at each step, which is useful for auditing and debugging. Go to
https://smith.langchain.com, create a free account, and generate an API key from the settings
page. This is optional but strongly recommended for any clinical use where audit trails matter.



## Setting Up the Project Step by Step

### Step 1: Open a Terminal

A terminal is a text-based window where you type commands to control your computer. Do not be
intimidated by this. You will only need to type a handful of commands, and they are provided
exactly as you need to type them.

On Windows: Press the Windows key, type "Command Prompt" or "PowerShell", and press Enter.

On Mac: Press Command and Space together, type "Terminal", and press Enter.

On Linux: You likely already know how to open a terminal.

### Step 2: Navigate to the Project Folder

In your terminal, you need to move into the MediStream project folder. The command for this is
"cd" which stands for "change directory".

If you placed the folder on your Desktop, type the following and press Enter.

On Mac or Linux:

    cd ~/Desktop/medistream

On Windows:

    cd C:\Users\YourName\Desktop\medistream

Replace "YourName" with your actual Windows username. If the folder has a different name like
"medistream-main" because you downloaded it from GitHub, use that name instead.

If you are not sure where the folder is, you can drag and drop the folder directly into the
terminal window after typing "cd " with a space, and the path will fill in automatically. Then
press Enter.

### Step 3: Create the Configuration File

MediStream needs to know your API keys. These are stored in a file called ".env" which lives
inside the project folder. This file is never uploaded anywhere, it stays on your computer.

In your terminal, type the following command to create the file. On Mac or Linux:

    touch .env

On Windows PowerShell:

    New-Item .env -ItemType File

Now open the .env file in any text editor. On Windows you can use Notepad. On Mac you can use
TextEdit. Or you can use any code editor like VS Code or Notepad++.

Paste the following into the file, replacing the placeholder values with your actual keys:

    GEMINI_API_KEY=paste_your_gemini_key_here
    LANGCHAIN_API_KEY=paste_your_langsmith_key_here
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_PROJECT=medistream
    OPENFDA_API_KEY=

The OPENFDA_API_KEY line can be left blank. OpenFDA is a public drug database and does not
require a key for basic usage. If you have one, add it after the equals sign.

Save the file and close the text editor.

### Step 4: Build the Application

This step tells Docker to read the project files and prepare the application. It downloads all
the required software libraries and packages everything together. You only need to do this once,
or again if the project files change.

In your terminal, make sure you are still inside the medistream project folder, then type:

    docker build -t medistream .

Do not forget the dot at the end. It tells Docker to look in the current folder.

This process will take between two and five minutes depending on your internet connection. You
will see lines of text scrolling as Docker downloads and installs everything. When it is done,
you will see a message saying the build was successful.

### Step 5: Start the Application

Now you will start the MediStream server. Type the following command:

On Mac or Linux:

    docker run --env-file .env -p 8000:8000 -v $(pwd)/outputs:/app/outputs medistream

On Windows PowerShell:

    docker run --env-file .env -p 8000:8000 -v ${PWD}/outputs:/app/outputs medistream

What this command does: it starts the MediStream container, loads your API keys from the .env
file, makes the application available on port 8000 of your computer, and connects the outputs
folder inside the container to a folder on your actual computer so that generated files are
saved where you can find them.

When you see a line that says "Uvicorn running on http://0.0.0.0:8000", the server is ready.
Leave this terminal window open. The server runs as long as this window is open.

### Step 6: Start the User Interface

Open a second terminal window. Navigate to the project folder again using the same cd command
from Step 2.

Now install the UI dependencies and start the Streamlit interface:

    pip install streamlit requests

Then run:

On Mac or Linux:

    MEDISTREAM_API_URL=http://localhost:8000 streamlit run ui/streamlit_app.py

On Windows PowerShell:

    $env:MEDISTREAM_API_URL="http://localhost:8000"; streamlit run ui/streamlit_app.py

A browser window will open automatically at http://localhost:8501. This is the MediStream
user interface.


## Using MediStream

Once the browser window is open, using the system is straightforward.

Click the "Browse files" button and select a medical document from your computer. Supported
formats are PDF, JPG, PNG, and TXT.

Click the "Run MediStream Pipeline" button.

A spinner will appear while the pipeline processes your document. Depending on the length of
the document and the speed of your internet connection, this typically takes between 15 and
60 seconds.

When processing is complete, the page will show you a summary including the reviewer verdict,
how many timeline events were created, and any validation issues that were detected.

You will then see two download buttons. Click "Download XML" to save the structured clinical
XML file. Click "Download Excel" to save the formatted workbook with separate sheets for
medications and medical history.

The downloaded files will go to your browser's default downloads folder, usually your Downloads
folder.


## Where Are the Generated Files Stored on the Server?

Every file the system generates is saved in the "outputs" folder inside the project directory
on your computer. The files are named with a timestamp so they never overwrite each other. For
example: medistream_20240615_143022.xml and medistream_20240615_143022.xlsx.

You can access these files directly from the outputs folder at any time, even after the
server is stopped.


## Using the API Without the User Interface

If you are a developer or want to integrate MediStream into another system, you can send
documents directly to the API without using the browser interface.

To process a document from the command line using curl:

    curl -X POST http://localhost:8000/process \
      -F "file=@/path/to/your/document.pdf"

Replace /path/to/your/document.pdf with the actual path to your file.

The API will return a JSON response that looks like this:

    {
      "status": "completed",
      "reviewer_verdict": "pass",
      "xml_path": "outputs/medistream_20240615_143022.xml",
      "xlsx_path": "outputs/medistream_20240615_143022.xlsx",
      "validation_issues": [],
      "timeline_event_count": 12
    }

To explore all available API endpoints and test them interactively, open your browser and go to:

    http://localhost:8000/docs

This page is automatically generated and lets you test every API endpoint directly from
the browser without writing any code.


## Monitoring What the AI Is Doing: LangSmith

If you provided a LangSmith API key, every run of the pipeline is automatically traced and
recorded. To view these traces:

Go to https://smith.langchain.com and sign in.

Click on the project named "medistream" in the left sidebar.

You will see a list of every pipeline run, with detailed breakdowns showing what each node
received as input, what it sent to the AI model, what the model returned, how long each step
took, and how many tokens were used. This is your audit trail.

If a run produced unexpected results, you can click on it in LangSmith, expand the individual
nodes, and see exactly what the AI was thinking at each step. This is invaluable for
troubleshooting or for demonstrating compliance to a regulator.


## Stopping the Application

To stop the server, go back to the first terminal window where the server is running and press
Control and C at the same time. The server will shut down.

To stop the Streamlit UI, go to the second terminal window and press Control and C.

To start everything again later, simply repeat Steps 5 and 6. You do not need to rebuild the
Docker image each time.


## Troubleshooting Common Problems

If the browser does not open automatically when you start Streamlit, open your browser manually
and go to http://localhost:8501.

If you see an error saying "port 8000 is already in use", it means something else on your
computer is using that port. You can change the port number. Replace both instances of 8000 in
the docker run command with 8001, and replace 8000 in the Streamlit start command with 8001.

If the pipeline fails with an error mentioning the Gemini API key, double-check that your
.env file has the correct key and that there are no extra spaces around the equals sign.

If the Docker build fails, make sure Docker Desktop is running. Look for the Docker whale icon
in your taskbar or menu bar and confirm it shows "Docker Desktop is running".

If you see a message saying "permission denied" when running a command on Mac or Linux,
try adding "sudo " at the beginning of the command and enter your computer password when asked.

If the reviewer verdict says "fail", it does not mean the pipeline crashed. It means the AI
reviewer found at least one discrepancy between the source document and the output. Check the
validation issues section for details. The XML and Excel files are still generated and
downloadable. You can review the flagged issues and decide whether they require manual
correction.


## Updating the System

If you receive an updated version of the project files, copy the new files into the project
folder, then rebuild the Docker image by running the build command from Step 4 again. You do
not need to change your .env file unless you are told to add new keys.


## A Note on Data Privacy

MediStream sends document content to Google's Gemini API for processing. Before using this
system with real patient data, ensure that your organization has appropriate data processing
agreements in place with Google and that usage complies with applicable regulations such as
HIPAA in the United States or GDPR in Europe. For a fully private deployment, the system can
be modified to use a locally hosted language model, which would require assistance from a
developer.
