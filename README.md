# Python-Tools



This repository contains a collection of Python scripts and tools for personal use, primarily for multimedia applications. It serves as a storage location for various projects.



\## Key Features \& Benefits



This repository currently includes two main projects:



\*   \*\*Fake Cam:\*\* A tool to broadcast an image or video as a virtual camera feed.

\*   \*\*Screen Recorder:\*\* A simple screen recording tool.



\## Prerequisites \& Dependencies



To run the scripts in this repository, you need Python 3.x installed. Each project has its own specific dependencies, which are listed in the respective `requirements.txt` files.



\## Installation \& Setup Instructions



1\.  \*\*Clone the repository:\*\*



&nbsp;   ```bash

&nbsp;   git clone https://github.com/marveljo25/Python-Tools.git

&nbsp;   cd Python-Tools

&nbsp;   ```



2\.  \*\*Set up a virtual environment (recommended):\*\*



&nbsp;   ```bash

&nbsp;   python3 -m venv venv

&nbsp;   source venv/bin/activate  # On Linux/macOS

&nbsp;   # venv\\Scripts\\activate  # On Windows

&nbsp;   ```



3\.  \*\*Install dependencies for each project:\*\*



&nbsp;   \*   \*\*Fake Cam:\*\*



&nbsp;       ```bash

&nbsp;       cd Fake Cam

&nbsp;       pip install -r requirements.txt

&nbsp;       cd ..

&nbsp;       ```



&nbsp;   \*   \*\*Screen Recorder:\*\*



&nbsp;       ```bash

&nbsp;       cd Screen Recorder

&nbsp;       #No requirements file currently, but dependencies are: mss, numpy, Pillow, imageio

&nbsp;       pip install mss numpy Pillow imageio

&nbsp;       cd ..

&nbsp;       ```



\## Usage Examples



\### Fake Cam



To use the Fake Cam tool, navigate to the `Fake Cam` directory and run `main.py`:



```bash

cd Fake Cam

python main.py

```



This will launch a GUI that allows you to select an image or video file and broadcast it as a virtual camera feed.



\### Screen Recorder



To use the Screen Recorder tool, navigate to the `Screen Recorder` directory and run `recorder.py`:



```bash

cd Screen Recorder

python recorder.py

```



This will start recording your screen and save the recording in segments to the `recordings` directory. Press `Ctrl+C` to stop the recording.



\## Project Structure



```

Python-Tools/

├── .gitignore

├── Fake Cam/

│   ├── main.py

│   ├── requirements.txt

│   └── README.md

└── Screen Recorder/

&nbsp;   ├── recorder.py

```



\*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.

\*   `Fake Cam/`: Contains the files for the Fake Cam project.

&nbsp;   \*   `main.py`: The main application file for the Fake Cam tool.

&nbsp;   \*   `requirements.txt`: Lists the Python packages required by the Fake Cam tool.

&nbsp;   \*   `README.md`: Contains specific information about the Fake Cam project.

\*   `Screen Recorder/`: Contains the files for the Screen Recorder project.

&nbsp;   \*   `recorder.py`: The script for recording the screen.



\## Configuration Options



\### Screen Recorder



The `Screen Recorder/recorder.py` script has the following configurable options:



\*   `FPS`: Frames per second for the recording (default: 10).

\*   `SEGMENT\_DURATION`: Duration of each recording segment in seconds (default: 60).

\*   `RESOLUTION`: Resolution of the recording (default: 1280x720).

\*   `OUTPUT\_DIR`: Directory to save the recordings (default: "recordings").



You can modify these options directly in the `recorder.py` file.



\## Contributing Guidelines



Contributions are welcome! If you find a bug or have an idea for a new feature, please open an issue or submit a pull request.



1\.  Fork the repository.

2\.  Create a new branch for your feature or bug fix.

3\.  Make your changes.

4\.  Submit a pull request.



\## License Information



This project does not currently specify a license. All rights are reserved.



\## Acknowledgments



\*   This project utilizes the `pyvirtualcam` library for creating virtual camera devices.

\*   The Screen Recorder uses `mss` for screen capturing, `numpy` for image manipulation, `Pillow` for image processing, and `imageio` for video encoding.

