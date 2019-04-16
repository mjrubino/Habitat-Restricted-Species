# -*- coding: utf-8 -*-

"""

                        Habitat-Restricted-Species.py
        
    Use this to create boxplots of habitat protection status percentages
    for habitat restricted species. Habitat restricted species are those
    whose proportion of habitat area within range area is in the lower 5th
    percentile for all GAP species (including subspecies). The Python script
    SB-Range-vs-Habitat.py must be run in order to generate a CSV file - 
    "SpeciesRangevsHabitat.csv". The file is utilized by this script to
    collect species' total habitat area, scientific and common names.
    
    This script accesses the GAP Analytic database to gather protection
    status measures based on the GAP Protected Areas Database (PAD). This
    database is currently (April 2019) only available on a local server
    instance.

    
    This uses the sciencebasepy package to access a CSV file (IUCN_Gap.csv)
    containing IUCN category data for GAP species available on ScienceBase.

    

    Package dependancies:
        sciencebasepy
        re
        pyodbc
        pandas
        numpy
        datetime (for calculating processing time)
        StringIO
        Seaborn
        datetime


@author: mjrubino
10 April 2019

"""

##############################################################################

import sciencebasepy, pyodbc, re
import pandas as pd
import numpy as np
from datetime import datetime
from io import StringIO
import seaborn as sns
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', 10)

analysisDir = 'C:/Data/USGS Analyses/'
workDir = analysisDir + 'Habitat-Restricted-Species/'

# ****** Static Range vs Habitat CSV File **********
#  Run SB-Range-vs-Habitat.py script to generate this file for a species list
HabRangeCSV = workDir + 'SpeciesRangevsHabitat.csv'

starttime = datetime.now()
timestamp = starttime.strftime('%Y-%m-%d')
#############################################################################################
########################## DB CONNECTION LOCAL FUNCTIONS ####################################
#############################################################################################


## --------------Cursor and Database Connections--------------------

def ConnectToDB(connectionStr):
    '''
    (str) -> cursor, connection

    Provides a cursor within and a connection to the database

    Argument:
    connectionStr -- The SQL Server compatible connection string
        for connecting to a database
    '''
    try:
        con = pyodbc.connect(connectionStr)
    except:
        connectionStr = connectionStr.replace('11.0', '10.0')
        con = pyodbc.connect(connectionStr)

    return con.cursor(), con

## ----------------Database Connection----------------------

def ConnectAnalyticDB():
    '''
    Returns a cursor and connection within the GAP analytic database.
    '''
    # Database connection parameters
    dbConStr = """DRIVER=SQL Server Native Client 11.0;
                    SERVER=CHUCK\SQL2014;
                    UID=;
                    PWD=;
                    TRUSTED_CONNECTION=Yes;
                    DATABASE=GAP_AnalyticDB;"""

    return ConnectToDB(dbConStr)


#############################################################################################
#############################################################################################
#############################################################################################

'''
    Connect to ScienceBase to pull down a species list with
    IUCN conservation status information in it.
    This uses the ScienceBase item for species habitat maps
    and searches for a CSV file with species info in it.
    The habitat map item has a unique id (527d0a83e4b0850ea0518326).
    If this changes, the code will need to be re-written.

'''
print('-'*50)
print('\n--> Connecting to ScienceBase to gather species IUCN criteria ...')

sb = sciencebasepy.SbSession()
habmapItem = sb.get_item("527d0a83e4b0850ea0518326")
# Make a regular expression variable for the IUCN csv file name pattern
fnp = 'IUCN_Gap.+'
for file in habmapItem["files"]:
    # Search for the file name pattern in the hab map item files dictionary
    fnMatch = re.search(fnp, file['name'])
    if fnMatch != None:
        try:
            dfGapIUCN = pd.read_csv(StringIO(sb.get(file["url"])))
            dfGapIUCN = dfGapIUCN.replace(np.nan, '', regex=True)
        except:
            print('!! Could not find a CSV file name match !!')

# Get the Range-Habitat csv file as a dataframe
print('\n--> Loading Habitat in Range CSV ...')
dfHabRng = pd.read_csv(HabRangeCSV)

# Pull out only a few necessary columns
dfHabInRng = dfHabRng[['SpeciesCode','ScientificName','CommonName','AreaRange_km2','AreaHab_km2']]

# Calculate the amount of habitat in range
dfHabInRng['PropHabOfRange'] = dfHabInRng['AreaHab_km2'] / dfHabInRng['AreaRange_km2']

# Calculate the lowest 5th percentile of proportions
print('\n--> Getting species whose habitat in range is in lowest 5th percentile ...')
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
'''
    Manual removal of species from the list

'''
print('\n--> Removing exotic species from the list ...')
# First, set the index to SpeciesCode to make dropping rows easier
dfAllLow5_IUCN.set_index('SpeciesCode', inplace=True)
# Two of these species are exotics. Remove them from the analysis
# Drop the Monk Parakeet - Myiopsitta monachus and Cane Toad - Rhinella marinus
dfAllLow5_IUCN.drop(['bMOPAx','aCANEx'], inplace=True)

# Two other species have problems with their RATs. File management issues from
# the early days of model processing have persisted. Until these species' outputs
# are fixed, they will need to be removed manually
# They are Cliff Swallow and North American Racer (bCLSWx & rNARAx)
dfAllLow5_IUCN.drop(['bCLSWx','rNARAx'], inplace=True)

# Pull out the species codes which are the row index
hrSpp = dfAllLow5_IUCN.index

# Select species that are of conservation concern based on IUCN categories
cclst = ['VU', 'EN', 'NT', 'DD', 'CR', 'EW']
select={'iucnCategory':cclst}
dfCC = dfAllLow5_IUCN[dfAllLow5_IUCN[list(select)].isin(select).all(axis=1)]

# Make a dataframe of subspecies using the species code
ss = np.where(hrSpp.str[5:]!='x')
dfss = dfAllLow5_IUCN.iloc[ss]

'''

    Get the habitat protection percentages for each species using the
    GAP Analytic database and the species list gathered above.


'''

sppStr = ""

for spp in hrSpp:
    
    # Build the species list that will be passed to the SQL
    if spp != hrSpp[-1]:
        sppStr = sppStr + "tblTaxa.strUC = '" + spp + "' OR "
    else:
        sppStr = sppStr + "tblTaxa.strUC = '" + spp + "'"

# Build an SQL statement that uses the Boundary, PAD-US,
# and Taxa tables to return cell counts for each PAD status
# for each species/subspecies in the passed list
#
print ("+"*50)
print ("\n Querying the Analytical DB to Calculate Species' Protection Percentages ....")


sql = """WITH 
boundary AS 
	(SELECT padus1_4.gap_sts, lu_boundary.value
	FROM   padus1_4
	INNER JOIN lu_boundary ON padus1_4.revoid = lu_boundary.padus1_4
	),

species AS
	(SELECT	lu_boundary_species.boundary, 
		tblTaxa.strUC, 
		tblTaxa.strScientificName, 
		tblTaxa.strCommonName, 
		lu_boundary_species.count
	FROM	lu_boundary_species
	INNER JOIN tblTaxa ON lu_boundary_species.species_cd = tblTaxa.strUC
	WHERE {0}
	)

SELECT	species.strUC as SppCode, 
	species.strCommonName as ComName, 
	species.strScientificName as SciName,  
	boundary.gap_sts as PADStatus, 
   sum(species.count) * 0.0009 as km2  
FROM	boundary
INNER JOIN species ON boundary.value = species.boundary 
WHERE boundary.gap_sts < 4
GROUP BY strUC, strScientificName, strCommonName, gap_sts
ORDER By strUC, gap_sts"""

## Connect to the Analytic Database
cur, conn = ConnectAnalyticDB()
strSQL = sql.format(sppStr)
dfSelect = pd.read_sql(strSQL, conn)

# Make a series that is the area sum (status 1-3 only) for each spp code
sAreaSum = dfSelect.groupby(['SppCode'])['km2'].sum()
# Make it a dataframe
dfSum = pd.DataFrame(sAreaSum)
# Round these numbers to 3 decimals to prevent strange math latter
dfSum = dfSum.round(3)
# Rename PADCount column to AreaSum1-3 and reset the index
dfSum.rename(columns={'km2':'AreaSum1-3'}, inplace=True)
dfSum = dfSum.reset_index()

# Merge this dataframe with the dfHabInRng dataframe made from the CSV
# file compiled for range and habitat areas in order to get the total
# habitat amount for each species. This will be used to calculate the 
# appropriate amount of habitat on GAP status 4 lands - that is, all
# the habitat that IS NOT ON GAP status 1, 2, or 3 lands
# First, pull out only the necessary columns from the dfHabInRng dataframe
dfHabTotal = dfHabInRng[['SpeciesCode','CommonName','ScientificName', 'AreaHab_km2']]
# Round the total habitat area numbers to 3 decimals for latter math
dfHabTotal['AreaHab_km2'] = dfHabTotal['AreaHab_km2'].round(3)
dfMerge1 = pd.merge(left=dfSum,right=dfHabTotal,how='left',
                   left_on='SppCode',right_on='SpeciesCode')

# Drop the extra species code column, add a status column which will be
# all status 4, and calculate the area of status 4 habitat
dfMerge1.drop('SpeciesCode', axis=1, inplace=True)
dfMerge1['PADStatus'] = '4'
dfMerge1['km2'] = dfMerge1['AreaHab_km2'] - dfMerge1['AreaSum1-3']
# Now rearrange and rename some columns to prepare for appending with SQL dataframe
dfMerge1.rename(columns={'CommonName':'ComName', 'ScientificName':'SciName'},inplace=True)
dfAppend = dfMerge1.drop(['AreaHab_km2','AreaSum1-3'], axis=1)
# Append with the SQL CSV dataframe dfSelect then calculate a total habitat area in km2
dfHabStatus = dfSelect.append(dfAppend, sort=False, ignore_index=True)
dfHabStatus['Total_km2'] = dfHabStatus['km2'].groupby(dfHabStatus['SppCode']).transform('sum')

# Calculate the percentage each status is relative to the total area for the species
dfHabStatus['PADPercent'] = (dfHabStatus['km2']/dfHabStatus['Total_km2'])*100
# Pivot the dataframe on PAD status to get them into columns
dfPivot = dfHabStatus.pivot_table(values='PADPercent',
                           index=['SppCode','ComName','SciName'],
                           columns=['PADStatus'])
# Rename the PAD status columns
dfPivot.rename(columns={'1':'Status 1','2':'Status 2',
                        '3':'Status 3','4':'Status 4'}, inplace=True)

# Calculate the percentage  status 1 and 2 combined
dfPivot['Status 1 & 2'] = dfPivot['Status 1'] + dfPivot['Status 2']
# Reset the index to a new dataframe
dfSppPAD = dfPivot.reset_index()
# Reorder columns
dfSppPAD = dfSppPAD[['SppCode','SciName','ComName',
                   'Status 1','Status 2','Status 1 & 2',
                   'Status 3','Status 4']]
# Make another dataframe of PAD status percentages just for the 19 species
# whose IUCN category attributes them as species of conservation concern
dfCCStatus = pd.merge(left=dfCC, left_on='SpeciesCode',
                      right=dfSppPAD, right_on='SppCode',
                      how='inner',left_index=True,right_index=False)
dfCCStatus = dfCCStatus[['SppCode','SciName','ComName',
                   'Status 1','Status 2','Status 1 & 2',
                   'Status 3','Status 4']]

'''

    Start manipulating the dataframe and
    plotting boxplots using the Seaborn package

'''
print('\n--> Plotting species habitat protection percentage by GAP status ...')
dfmelt3 = dfSppPAD.melt(id_vars = 'SppCode',
                  value_vars = ['Status 1 & 2',
                                'Status 3','Status 4'],
                  var_name = 'GAP Protection Status',
                  value_name = 'Percent Habitat Protected')
# A version WITHOUT combined Status 1 & 2 percentages
dfmelt4 = dfCCStatus.melt(id_vars = 'SppCode',
                  value_vars = ['Status 1','Status 2',
                                'Status 3','Status 4'],
                  var_name = 'GAP Protection Status',
                  value_name = 'Percent Habitat Protected')


fig1, ax1 = plt.subplots(figsize=(9,8))
# Make a color palette for each GAP status category
cp = {'Status 1':'#66cc00','Status 2':'#007b0c',
      'Status 1 & 2':'#4b5e26',
      'Status 3':'#aab256','Status 4':'#B5c6c9'}
# Subset the color palette for only Status 1&2, 3, and 4
cp3 = {k:cp[k] for k in ('Status 1 & 2','Status 3','Status 4') if k in cp}
# Subset the color palette for all statuses EXCEPT 1&2
cp4 = {k:cp[k] for k in ('Status 1','Status 2','Status 3','Status 4') if k in cp}

# Plot percent habitat protected by GAP status for ALL species in the lowest 5th percentile
a1 = sns.boxplot(data = dfmelt3,
                x = 'GAP Protection Status',
                y = 'Percent Habitat Protected',
                width=0.35,
                palette=cp3,
                ax=ax1)
a1.set_title('Habitat Protection by GAP Status for 82 Habitat Restricted Species', fontsize=12)


dfmelt4 = dfSppPAD.melt(id_vars = 'SppCode',
                  value_vars = ['Status 1','Status 2',
                                'Status 3','Status 4'],
                  var_name = 'GAP Protection Status',
                  value_name = 'Percent Habitat Protected')

# Plot protection by status ONLY for species of conservation concern from IUCN
fig2, ax2 = plt.subplots(figsize=(9,8))
a2 = sns.boxplot(data = dfmelt4,
                x = 'GAP Protection Status',
                y = 'Percent Habitat Protected',
                width=0.35,
                palette=cp4,
                ax=ax2)
a2.set_title('Habitat Protection by GAP Status for 19 Habitat Restricted Species of Conservation Concern', fontsize=12)


endtime = datetime.now()
delta = endtime - starttime
print("+"*35)
print("Processing time: " + str(delta))
print("+"*35)



