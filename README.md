# Prerequisite
Python: Install python https://www.python.org/downloads/

# Validate that python and pip is installed
# For windows, make sure to set the environment PATH to the python bin, if not already.
# usually, C:\Users\[User]\AppData\Local\Python\bin
python --version
pip --version

# Other libraries
pip install streamlit
pip install pandas
pip install git+https://github.com/mariostoev/finviz@master

# To run the executable
python -m streamlit run app.py 
