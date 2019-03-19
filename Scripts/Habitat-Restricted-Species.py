# -*- coding: utf-8 -*-

"""

                        Habitat-Restricted-Species.py
        
    Use this to create a CSV file of species' (including subspecies)
    HUC12 range sizes - in km2 and number of HUCs - and the proportion
    that range relative to the totatl CONUS area. The identified range
    includes both breeding and non-breeding and summer and winter
    seasons. It DOES NOT INCLUDE any migratory portions of a species'
    range nor does it include any historic and/or extirpated portions
    that may have been delineated.
    Additionally, the script will calculate "range" (extent really) based
    on HABITAT as oppossed to HUC 12 range. This uses the habitat maps
    with NoData and 1,2, and/or 3s and calculates as sum as well as
    proportion relative to the CONUS land cover (excluding 0s). Note
    that total CONUS land cover area could exclude water. The script
    sets variables for both water included and water excluded cell
    counts - cntLC and cntLCnoW respectively.
    
    This uses the sciencebasepy package and local functions to download
    and unzip GAP range and habitat species data from ScienceBase.
    
    It also requires a text file of 12-digit range HUCs (HUC12s.txt)
    that contains data on each HUC's areal extent for calculating total
    and proportional area of range extent.
    
    OUTPUT CSV FILE NAME: SpeciesRangevsHabitat.csv
    
    The final CSV file will contain the following fields:
    SpeciesCode
    ScientificName
    CommonName
    AreaRange_km2
    nHUCS
    Prop_CONUS
    AreaHab_km2
    PropHab_CONUS
    LogAreaRange
    LogAreaHabitat
    

    Package dependancies:
        sciencebasepy
        glob
        zipfile
        pandas
        simpledbf
        numpy
        datetime (for calculating processing time)
        StringIO
        BytesIO
        Seaborn
        requests
        datetime


@author: mjrubino
13 March 2019

"""

##############################################################################

import os, sys, shutil, sciencebasepy
import pandas as pd
import numpy as np
from datetime import datetime
from io import StringIO


analysisDir = 'C:/Data/USGS Analyses/'
workDir = analysisDir + 'Habitat-Restricted-Species/'
tempDir = workDir + 'downloadtemp/'
# ****** Static Range vs Habitat CSV File **********
#  Run SB-Range-vs-Habitat.py script to generate this file for a species list
CSVfile = workDir + 'SpeciesRangevsHabitat.csv'

starttime = datetime.now()
timestamp = starttime.strftime('%Y-%m-%d')


# Make temporary directory for downloads
#  remove it if it already exists
if os.path.exists(tempDir):
    shutil.rmtree(tempDir)
    os.mkdir(tempDir)
else:
    os.mkdir(tempDir)


'''
    Function to write an error log if a species' ScienceBase
    range or habitat file connection cannot be made
'''
log = workDir + 'Species-Data-Access-Error-Log.txt'
def Log(content):
    with open(log, 'a') as logDoc:
        logDoc.write(content + '\n')

# STATIC VARIABLES
CONUSArea = 8103534.7   # 12-Digit HUC CONUS total area in km2
nHUCs = 82717.0         # Number of 12-digit HUCS in CONUS
cntLC = 9000763993.0    # Cell count of CONUS landcover excluding 0s
cntLCnoW = 8501572144.0 # Cell count of CONUS landcover excluding 0s and water


# Get the Range-Habitat csv file as a dataframe
dfRngHab = pd.read_csv(CSVfile)

# Pull out only a few necessary columns
dfHabInRng = dfRngHab[['SpeciesCode','ScientificName','CommonName','AreaRange_km2','AreaHab_km2']]

# Calculate the amount of habitat in range
dfHabInRng['PropHabOfRange'] = dfHabInRng['AreaHab_km2'] / dfHabInRng['AreaRange_km2']

# Calculate the lowest 5th percentile of proportions
props = dfHabInRng['PropHabOfRange']
low5 = np.percentile(props, 5, interpolation='lower')




















# Export to CSV
print('*'*85)
print('\nExporting to CSV: SpeciesRangevsHabitat.csv\n')
dfMaster.to_csv(workDir + "SpeciesRangevsHabitat.csv")


endtime = datetime.now()
delta = endtime - starttime
print("+"*35)
print("Processing time: " + str(delta))
print("+"*35)



