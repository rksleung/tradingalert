# Prerequisite
Python: Install python https://www.python.org/downloads/

To Validate that python and pip is installed, run the following on command prompt.

- python --version
- pip --version

For windows, make sure to set the environment PATH to the python bin, if not already.
usually, C:\Users\\{User}\AppData\Local\Python\bin


# Other libraries
- pip install streamlit
- pip install pandas
- pip install git+https://github.com/mariostoev/finviz@master

# To run the executable
python -m streamlit run app.py 

# To run the scheduler
python schedule.py "[finviz url]"
