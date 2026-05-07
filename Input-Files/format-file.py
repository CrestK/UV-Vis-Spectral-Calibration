def write_absorbance(input_file, output_file): #input file is the spectrum text, output is where you want to write


    data = np.loadtxt(input_file, skiprows=2) # load the input data, skiping 2 rows because those are the headers
    Wavelength = data[:,0] #save an array as the wavelengths
    Absorbance = data[:,1] # save column 2 as absorbance


    with open(output_file, 'a+') as file: ## with, used a "context manager" this opens and closes it as needed https://www.geeksforgeeks.org/python/context-manager-in-python/
    #a+ is for read and append
    #open opens a file so we can save stuff to it
    # w is the write option, because we'll save
    # file is just the shorthand for the file
        file.seek(0) #sets the append to the start instead of the end


        readable = file.read() #open up the file to be read as a variable
        
        if "Absorbance =" not in readable: #check if the string: "Absorbance =" in in the file, if not add the parameter
            file.seek(0,2)
            print("Wrote to Absorbance")   # sanity check         
            # Write absorbance as single line
            file.write( f"\n Absorbance = {Absorbance.tolist()}\n") ## this writes to the textfile a line that is "Absorbance = [..,..,..] \n is newline , the scond one \n is so there is a space line in between
        
        else:
            print("Absorbance already present")








def write_wavelength(input_file, output_file):

    data = np.loadtxt(input_file, skiprows=2) # load the input data, skiping 2 rows because those are the headers
    Wavelength = data[:,0] #save an array as the wavelengths
    Absorbance = data[:,1] # save column 2 as absorbance


    
    with open(output_file, 'a+') as file: ## with, used a "context manager" this opens and closes it as needed https://www.geeksforgeeks.org/python/context-manager-in-python/
    #r+ is for read and write
    #open opens a file so we can save stuff to it
    # w is the write option, because we'll save
    # file is just the shorthand for the file
        file.seek(0)  #sets the append to the start instead of the end

        readable = file.read() #open up the file to be read as a variable
        
        if "Wavelength =" not in readable: #check if the string: "Wavelength =" in in the file, if not add the parameter
            
            file.seek(0,2)
            
            print("Wrote to Wavelength") # sanity check
            # Write wavelength as single line
            file.write(f"\n Wavelength = {Wavelength.tolist()}\n\n") ## this writes to the textfile a line that is "Wavelength = [..,..,..] \n is newline , the scond one \n is so there is a space line in between
        
        
        else:
            print("Wavelength already present")





# def write_peaks(input_file, output_file):


#     if isinstance(input_file, str):

#         data = np.loadtxt(input_file)

    
#         with open(output_file, 'a+') as file: 
#             file.seek(0)  
        
#             readable = file.read() 
            
#             if "Peaks =" not in readable:
                
#                 file.seek(0,2)
                
#                 print("Wrote to Peaks")
#                 file.write(f"\n Peaks = {data.tolist()}\n\n") 
            
            
#             else:
#                 print("Peaks already present")

def write_peaks(input_file, output_file):
    #check if input is a string (filename) or list/array 
    if isinstance(input_file, str): #if it's a file name/ str load it in as such
    
        data = np.loadtxt(input_file) #loading in the file that has the string name
        peaks = data.tolist() #make that input textfile as a list in python
    
    elif isinstance(input_file, list): #if it is a list (like in peaks=[2,34,34,34]) then just use that list, this is handled by the json library
        peaks = input_file
    
    else:
        print(f"Error: peaks must be a filename or array")
        return

    #appending to the output file Peaks = [...]
    with open(output_file, 'a+') as file: 
        file.seek(0)  
        readable = file.read() 
        
        if "Peaks =" not in readable:
            file.seek(0, 2)
            print("Wrote to Peaks")
            file.write(f"\nPeaks = {peaks}\n\n") 
        else:
            print("Peaks already present")











import sys #for system input
import numpy as np
import json #loading in arrays and converting them to python


parameters = {} # make a dictionary for all parameters


for arg in sys.argv[1:]: ## load as many arguments and map them to a key value.
    if '=' in arg:   #separate the inputs if they have key="value"
        key, value = arg.split('=') # key = key, value = "value"
        parameters[key] = value #write to the dictionary that key:value, this pairs the two in the dictionary


print("Parameters:")
print(parameters)
for key, value in parameters.items(): #printing the parameters in the terminal
    print(f"  {key} = {value}")



input_file = parameters['input'] #turning the input values in the terminal input into python variables
output_file = parameters['output']
peaks = parameters['peaks']

#this loads the input and if it starts with [ , then it's an input array.
if peaks.startswith('['):
    peaks = json.loads(peaks)  # Convert input array say"[334,32423,234]" to python list [334, 32423, 234]
    print(f"Parsed peaks as array: {peaks}")



    

write_absorbance(input_file, output_file)

write_wavelength(input_file, output_file)

write_peaks(peaks, output_file)












































