# -*- coding: utf-8 -*-

"""

                        Habitat-Restricted-Species.py
        
    Use this to create a CSV file of species' (including subspecies)

    
    This uses the sciencebasepy package and local functions to download
    and unzip GAP range and habitat species data from ScienceBase.

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
CSVfile = workDir + 'SpeciesRangevsHabitat-fromJMP.csv'

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



'''
    Connect to ScienceBase to pull down a species list with
    IUCN conservation status information in it.
    This uses the ScienceBase item for species habitat maps
    and searches for a CSV file with species info in it.
    The habitat map item has a unique id (527d0a83e4b0850ea0518326)
    and the CSV file is named IUCN_Gap.csv. If
    either of these change, the code will need to be re-written.

'''
sb = sciencebasepy.SbSession()
habmapItem = sb.get_item("527d0a83e4b0850ea0518326")
# Get the CSV and make it a dataframe
for file in habmapItem["files"]:
    if file["name"] == "IUCN_Gap.csv":
        dfGapIUCN = pd.read_csv(StringIO(sb.get(file["url"])))
        dfGapIUCN = dfGapIUCN.replace(np.nan, '', regex=True)

# Get the Range-Habitat csv file as a dataframe
dfRngHab = pd.read_csv(CSVfile)

# Pull out only a few necessary columns
dfHabInRng = dfRngHab[['SpeciesCode','ScientificName','CommonName','AreaRange_km2','AreaHab_km2']]

# Calculate the amount of habitat in range
dfHabInRng['PropHabOfRange'] = dfHabInRng['AreaHab_km2'] / dfHabInRng['AreaRange_km2']

# Calculate the lowest 5th percentile of proportions
props = dfHabInRng['PropHabOfRange']
low5 = np.percentile(props, 5, interpolation='lower')
# Make a dataframe of the species < the lowest 5th percentile
dflow5 = dfHabInRng[dfHabInRng['PropHabOfRange']<=low5]

# Merge the lowest 5th percentile species df with the GAP IUCN df
# First, merge them to match full species only
# NOTE: IUCN does not assess subspecies therfore matches are only on full species
dfSppOnly_IUCN = pd.merge(left=dflow5, right=dfGapIUCN, how='inner',
                      left_on='SpeciesCode', right_on='gapSppCode')
# Now merge them keeping all records for species in the lowest 5th percentile
# that is, including all the subspecies from the GAP list
dfAllLow5_IUCN = pd.merge(left=dflow5, right=dfGapIUCN, how='left',
                      left_on='SpeciesCode', right_on='gapSppCode')




















# Export to CSV
print('*'*85)
print('\nExporting to CSV: SpeciesRangevsHabitat.csv\n')
dfMaster.to_csv(workDir + "SpeciesRangevsHabitat.csv")


endtime = datetime.now()
delta = endtime - starttime
print("+"*35)
print("Processing time: " + str(delta))
print("+"*35)



