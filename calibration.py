#!/usr/bin/env python
# coding: utf-8

# ## Load Libraries


import json
import sys
from scipy.signal import find_peaks
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
import time


#runtime
start_time = time.time()


# ## Parameters and Parameter loading

parameters = {} # make a dictionary for all parameters
data = {}

for arg in sys.argv[1:]: ## load as many arguments and map them to a key value.
    if '=' in arg: #separate the inputs if they have key="value"
        key, value = arg.split('=') # key = key, value = "value"
        parameters[key] = value #write to the dictionary that key:value, this pairs the two in the dictionary

input_file = parameters.get('input', './Input-Files/in-out.txt') #turning the input values in the terminal input into python variables
peaks = parameters.get('peaks', './Peaks/reference_peaks.txt') #gives default ./Peaks/reference_peaks.txt'
output_filename = parameters.get('output_filename', './output.txt')




#Load reference peaks(from file or string(json))
if peaks.startswith('['):
    reference_peaks = np.array(json.loads(peaks))
else:
    reference_peaks = np.array(np.loadtxt(peaks))



# Load spectral data from input file as data dictionary
with open(input_file, 'r') as file:
    for line in file:
        if '=' in line and '[' in line:
            key, value = line.split('=', 1)
            data[key.strip()] = json.loads(value.strip())

plt.plot(data['Absorbance'])
plt.xlabel("Pixel #")
plt.ylabel("Absorbance")


# ## Peak Finding


fit_peaks, properties = find_peaks(data['Absorbance'], 
                               height=0.01,      # minimum height
                               prominence=0.01,        # how much peak stands out
                               distance=3)  # minimum distance between peaks

fit_peaks, np.array(data['Wavelength'])[fit_peaks]



wavelength = np.array(data['Wavelength']) #ideal check
absorb = np.array(data['Absorbance']) #absorbance



print(f"Found {len(fit_peaks)} peaks in spectrum")
print(f"There are {len(reference_peaks)} reference peaks")


# ### Checking Where the fit peaks occur


plt.plot(data['Absorbance'], label= "Absorbance")
plt.plot(fit_peaks, absorb[fit_peaks], "x", label = "Peak")
plt.xlabel("Pixel #")
plt.ylabel("Absorbance")
plt.legend()
plt.savefig("./Figures/peaks.png")
plt.close()

# ## Calibration

# ### Determine if we should do linear or cubic



def determine_polynomial_degree(number_of_peaks):
    if number_of_peaks >= 5:
        return 3  #Cubic fit
    else:
        return 1  #Linear fit


# #### Evaluating a fit


def evaluate_fit(pixel_positions, reference_wavelengths, deg):
    #fitting our polynomial
    #the degree of fit, either linear (1) or cubic (3)
    if len(pixel_positions) < deg + 1:
        return np.inf, None, None, np.inf  #not enough points for this level of polynomial

    coeffs = np.polyfit(pixel_positions, reference_wavelengths, deg=deg)

    # Do the fit, get the wavelengths
    if deg == 3:
        d, c, b, a = coeffs
        fitted_wavelengths = d * pixel_positions**3 + c * pixel_positions**2 + b * pixel_positions + a
    elif deg == 1:
        b, a = coeffs
        fitted_wavelengths = b * pixel_positions + a

    #rms error, residuals, highest error
    residuals = reference_wavelengths - fitted_wavelengths
    rms_error = np.sqrt(np.mean(residuals**2))
    max_abs_error = np.max(np.abs(residuals))

    return rms_error, coeffs, residuals, max_abs_error



def validate_peak_pairing(pixel_positions, reference_wavelengths, coeffs, deg, max_pixel):   
    #Checking if wavelength increases with pixel number
    pixel_order = np.argsort(pixel_positions) #sort order should increase [0,1,2,3...]
    wavelength_order = np.argsort(reference_wavelengths) #sort order should increase [0,1,2,3...]

    if not np.array_equal(pixel_order, wavelength_order):
        return False #if the ordering isn't the same don't try to match

    #check for if the dispersion(nm/pixel) makes sense
    #sorting the pixel and wavelength, in order
    sorted_pixels = np.sort(pixel_positions)
    sorted_wavelengths = np.sort(reference_wavelengths)

    # Calculate dispersion between consecutive peaks
    dispersions = np.diff(sorted_wavelengths) / np.diff(sorted_pixels) #difference from previous value, starts at i=1, wavelength(nm)/pixel

    #minimum and maximum dispersion allowed
    min_dispersion = 0.05  # nm/pixel
    max_dispersion = 2.0   # nm/pixel

    if np.any(dispersions < min_dispersion) or np.any(dispersions > max_dispersion): #check if its above or below the min and max allowed
        return False


    #Does the wavelength range make sense? Checking
    pixel_array_check = np.array([0, max_pixel])  # Check at endpoints

    if deg == 3:
        d, c, b, a = coeffs
        wl_check = d * pixel_array_check**3 + c * pixel_array_check**2 + b * pixel_array_check + a
    else:
        b, a = coeffs
        wl_check = b * pixel_array_check + a

    #Checking if the range is in the uv-vis 1400nm range
    if np.any(wl_check < 100) or np.any(wl_check > 1300):
        return False



    if deg == 3: #see if the cubic term for cube is super large, reject easily if it's too large.
        d, c, b, a = coeffs
        #
        if abs(d) > 1e-4: 
            return False


    pixel_array_check = np.linspace(0, max_pixel, 100)  #Sample 100 points
    wl_forward_check = np.polyval(coeffs, pixel_array_check) #get the wavelength

    # Check if wavelengths are increasing
    if not np.all(np.diff(wl_forward_check) > 0):  # If any decrease, reject, this prevents crazy cubic wrap around
        return False

    return True




#figure out the maximum number of peaks and we work down from there
n_detected = len(fit_peaks)
n_reference = len(reference_peaks)
max_peaks = min(n_detected, n_reference)
min_peaks = 3  #needed for at least linear regression


#our parameters that we will get
best_rms = np.inf
best_coeffs = None
best_deg = None
best_ref_peaks = None
best_n_peaks = 0
best_max_error = np.inf
best_residuals = None
best_combo = None

n_peaks = max_peaks


deg = determine_polynomial_degree(n_peaks) #determines the degree of our fit

combinations_tested = 0
combinations_valid = 0






# ### Testing Every single combo for the best one.

# legacy for non dynamic number of peaks
# for peak_combo in combinations(range(n_detected), n_peaks):
#     pixel_positions = fit_peaks[list(peak_combo)]

#     for ref_combo in combinations(range(n_reference), n_peaks):
#         ref_wavelengths = reference_peaks[list(ref_combo)]
#         rms_error, coeffs, residuals, max_error = evaluate_fit(pixel_positions, ref_wavelengths, deg)
#         combinations_tested += 1

#         #Does this pass validation?
#         is_valid = validate_peak_pairing(pixel_positions, ref_wavelengths, coeffs, deg, len(data['Absorbance'])-4)

#         if not is_valid:
#             continue  #skip combination, it's not valid

#         combinations_valid += 1

#         if rms_error < best_rms: #we only take the best of the best, if worse, nah reject it.
#             best_rms = rms_error
#             best_combo = (list(peak_combo), list(ref_combo))
#             best_coeffs = coeffs
#             best_ref_peaks = ref_wavelengths
#             best_max_error = max_error
#             best_residuals = residuals




#testing errant fits

# fit_peaks = np.array([ 139,  500,  574,  679,  795, 1019, 1154, 1308, 1489])
# fit_peaks = np.array([1019, 1154, 1308, 1489,1500,1510])



# iteratively running fits
for n_peaks in range(max_peaks, min_peaks - 1, -1):  # Try max_peaks, then subtract one, so on and so forth

    deg = determine_polynomial_degree(n_peaks)

    combinations_tested = 0
    combinations_valid = 0

    for peak_combo in combinations(range(n_detected), n_peaks):
        pixel_positions = fit_peaks[list(peak_combo)]

        for ref_combo in combinations(range(n_reference), n_peaks):
            ref_wavelengths = reference_peaks[list(ref_combo)]
            rms_error, coeffs, residuals, max_error = evaluate_fit(pixel_positions, ref_wavelengths, deg)
            combinations_tested += 1
            
            #check validation of fit
            is_valid = validate_peak_pairing(pixel_positions, ref_wavelengths, coeffs, deg,len(data['Absorbance'])-4)

            if not is_valid:
                continue

            combinations_valid += 1
            #update if newer combination is better
            if rms_error < best_rms:
                best_rms = rms_error
                best_combo = (list(peak_combo), list(ref_combo))
                best_coeffs = coeffs
                best_ref_peaks = ref_wavelengths
                best_max_error = max_error
                best_residuals = residuals
                best_n_peaks = n_peaks

    #end if there is a good fit with larger peaks
    if best_rms < 1.0:  # If rms is decent, stop
        print(f"Found good fit with {n_peaks} peaks")
        break

    print(f"Tried {n_peaks} peaks: {combinations_valid}/{combinations_tested} valid combinations")


# #### Print output


print(f"Tested {combinations_tested} combinations ({combinations_valid} valid)")
if combinations_valid > 0:
    print(f"RMS: {best_rms:.6} nm, Max error: {best_max_error:.6} nm")
else:
    print(f"No valid combinations found!")


# ### Applicable Function



#convert coeffiecents to wavelengths
def apply_calibration(coefficients, pixel_array):

    return np.polyval(coefficients, pixel_array)




pixel_arr = range(len(data['Absorbance'])) #make an index of length of absorbance so we have one calibrated wavelength per every pixel


calibrated = apply_calibration(best_coeffs, pixel_arr)

# making and saving figure
plt.plot(calibrated,data['Absorbance'],linewidth=2, label =" calibrated")
plt.plot(wavelength, absorb,linestyle='-', linewidth=1,label ="reference")
plt.plot(calibrated[fit_peaks], absorb[fit_peaks], "x", label = "Peak")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Absorbance")
plt.legend()
plt.savefig("./Figures/Calibration.png")

best_coeffs


# ## Saving the  Coefficient Data

np.savetxt('coeffs.txt', best_coeffs)




#run time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Runtime: {elapsed_time:.4} seconds")



## Output File
from datetime import datetime


with open(output_filename, 'w') as f:
    # Input parameters
    
    f.write(f"Date-Time Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write("Input:\n")
    f.write(f"Input file: {input_file}\n")
    f.write(f"Input Absorbance: {data['Absorbance']}\n")
    f.write(f"Input Absorbance: {data['Wavelength']}\n")
    f.write(f"Reference peaks (nm): {reference_peaks}\n")
    

    # Calibration results
    f.write(f"Number of Peaks Used: {best_n_peaks}\n")
    f.write(f"Polynomial degree: {best_deg}\n")
    f.write(f"rms error: {best_rms:.4} nm\n")
    f.write(f"Max error: {best_max_error:.4} nm\n\n")
    
    f.write("Fit coefficients:\n")
    for i, coef in enumerate(best_coeffs):
        f.write(f"  coeff[{i}]: {coef}\n")
    f.write("\n")
    
    #Runtime
    f.write("Runtime=")
    f.write(f"{elapsed_time} seconds\n")
    
    f.write("Residuals (nm)=")
    for i, res in enumerate(best_residuals):
        f.write(f"  Peak {i+1}: {res} ,")
