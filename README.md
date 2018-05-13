# Authors: Viren Mody, Guillermo Rojas Hernandez

## Course Project Description:
Open-source projects available through online code repository websites such as GitHub provide software engineers with a rich reference for potential projects.  Oftentimes, the code repository will not only include the source code, but will also include the build and pipeline configuration so that developers can build the project or library.  This project will be analyzing the build configuration files for the popular automation tool Jenkins, in order to get information on how software engineering projects are built today.

For this project, formulating questions and even choosing questions from the example list was not a simple task and required some investigation. In order to formulate these questions, we started  by understanding  what a Jenkinsfile is and then we had to sift through the all the details of the pipeline syntax in the Jenkins documentation in order to start formulating some questions. Next, we performed a variety of search queries on GitHub’s web search interface for repositories containing actual Jenkinsfiles that we could examine to spark more wonderings about DevOps pipelines.


Configuration Instructions
--- 
Please follow these steps:  

### Machine/Environment
* Windows
* Ubuntu

### Initial Setup/ Configuration

* Install Python Interpreter 3.6.3
* Install Pycharm Professional 2018.1
* If Pycharm states that project_utils is ‘unresolved’, replace:
  + import project_utils 
  + with
  + from src import project_utils
* If that does not work, please go into File > Setting > Search for “Project Structure”
  + Click on the project folder which should be ‘[LOCAL_PATH]\Guillermo_Rojas_Hernandez_Viren_Mody_CourseProject\’ and then click on the “Sources” button above to add the project folder as a source folder.


### Libraries/API

* Install GitPython (pip install gitpython)
* Install unidiff (pip install unidiff)
* Install pandas (pip install pandas)
* (If Using Ubuntu: Install matplotlib 'using sudo apt-get install python3-matplotlib')
* Install github3.py (pip install --pre github3.py)
* Install urllib3 (pip install urllib3)
  
### Update Variables
* GITHUB_USERNAME (Optional)
* GITHUB_ACCESS_TOKEN (Optional)
* CLONED_REPOS_DIR_PATH (location of where you want the cloned repositories to be downloaded)


### Analysis Report
  
* Output analysis will be located at ‘/src/*.csv
* Various CSV files with different questions will be available

