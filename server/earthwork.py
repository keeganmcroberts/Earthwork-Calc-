import pandas as pd 
import numpy as np
import time 

pd.set_option('mode.chained_assignment', None) # turned off SetWithCopyWarning exception, not advisable but temporary 

df = pd.read_csv("C:/Users/kmcroberts/Development/code/Anaconda/Rev A/EG pile points_example.csv")

# Group the DataFrame into rows of 15
grouped_df = df.groupby(df.index // 15)

grouped_piles= []

start = time.time()

#Iterate through each group for calculations
for group_index, each_group in grouped_df:


    #variable parameters which will eventually be dynamic based on user inputs. Will have to make these pieces of useState which can be submit through a form on the front end. 
    low_tolerance = 4
    high_tolerance = 6
    step = 0.5
    starting_reveal = 4
    pitch = 19.5
    slope_tolerance = .08
    slope_change = .013


    # Calculating Ground Slope; added shifted columns of northing and easting to access values in previous cells
    each_group['n -1'] = each_group['n'].shift(1)
    each_group['z -1'] = each_group['z'].shift(1)
    each_group['Ground Slope'] = (each_group['z'] - each_group['z -1']) / (each_group['n -1'] - each_group['n']) 
    # Exclude Ground Slope for end Piles, set value to NA
    each_group.loc[each_group.index[0], 'Ground Slope'] = 'N/A'
    each_group.loc[each_group.index[-1], 'Ground Slope'] = 'N/A'

    
    # Add Column for Distance from Pile North
    each_group['Distance From Pile North'] = (each_group['n -1']) - (each_group['n'])
    each_group.loc[each_group.index[0], 'Distance From Pile North'] = 0

    
    #*****************************************************************************************************************************************
    # Starting Reveal for Tracker1 Pile1, used to calculate TOP Elevation. Constant for now but needs to change for each successive Tracker to optimize the Pile Reveal based on variable params and csv values. 
    each_group.loc[each_group.index[0], 'Pile Reveal'] = 4
    each_group.loc[each_group.index[-1], 'Pile Reveal'] = each_group.loc[each_group.index[0], 'Pile Reveal']


    # Adding column for Top of Pile Elevation for Pile1 and Pile15
    each_group.loc[each_group.index[0], 'TOP Elevation'] = each_group['z'].iloc[0] + each_group['Pile Reveal'].iloc[0]
    each_group.loc[each_group.index[-1], 'TOP Elevation'] = each_group['z'].iloc[-1] + each_group['Pile Reveal'].iloc[0]


    # Column for Table Slope Piles1and15
    each_group.loc[each_group.index[0], 'Table Slope'] = (each_group['TOP Elevation'].iloc[-1] - each_group['TOP Elevation'].iloc[0]) /( each_group['n'].iloc[0] - each_group['n'].iloc[-1])
    each_group.loc[each_group.index[-1], 'Table Slope'] = (each_group['TOP Elevation'].iloc[-1] - each_group['TOP Elevation'].iloc[0]) /( each_group['n'].iloc[0] - each_group['n'].iloc[-1])


    #conditional for calculating Table Slope for Piles2-14; slope change is a constant for now until we implement user interactive functionality
    for i in range(13):
        if each_group['Ground Slope'].iloc[i + 1] > each_group['Table Slope'].iloc[i] + slope_change:
            each_group['Table Slope'].iloc[i + 1] = each_group['Table Slope'].iloc[i] + slope_change
        elif each_group['Ground Slope'].iloc[i + 1] < each_group['Table Slope'].iloc[i] - slope_change:
            each_group['Table Slope'].iloc[i + 1] = each_group['Table Slope'].iloc[i] - slope_change
        else:
            each_group['Table Slope'].iloc[i + 1] = each_group['Ground Slope'].iloc[i + 1]


    #column for Top of Pile Elevation Piles2-14
    for i in range(13):
        each_group['TOP Elevation'].iloc[i + 1] = each_group['TOP Elevation'].iloc[i] + each_group['Distance From Pile North'].iloc[i +1] * each_group['Table Slope'].iloc[i +1]
    

    #column for Pile Reveal Piles2-14
    for i in range(13):
        each_group['Pile Reveal'].iloc[i + 1] = each_group['TOP Elevation'].iloc[i + 1] - each_group['z'].iloc[i + 1]


    #Delta Column conditional 
    for i in range(15):
        each_group.loc[each_group.index[i], 'Delta'] = 'SAFE'
        if each_group['Pile Reveal'].iloc[i] < high_tolerance and each_group['Pile Reveal'].iloc[i] >= low_tolerance:
            each_group.loc[each_group.index[i], 'Delta'] = "SAFE"
        elif each_group['Pile Reveal'].iloc[i] > high_tolerance:
            each_group.loc[each_group.index[i], 'Delta'] = each_group['Pile Reveal'].iloc[i] - high_tolerance
        elif each_group['Pile Reveal'].iloc[i] < low_tolerance:
            each_group.loc[each_group.index[i], 'Delta'] = each_group['Pile Reveal'].iloc[i] - low_tolerance

    
    #CUT AND FILL POINTS


    #cut
    for i in range (15):
        if each_group['Pile Reveal'].iloc[i] < low_tolerance:
            each_group['Cut'].iloc[i] = (low_tolerance - each_group['Pile Reveal'].iloc[i]) * each_group['Distance From Pile North'].iloc[i + 1] * (pitch / 27)
        else:
            each_group.loc[each_group.index[i], 'Cut'] = 0


    #fill
    for i in range (15):
        if each_group['Pile Reveal'].iloc[i] > high_tolerance:
            each_group['Fill'].iloc[i] = (each_group['Pile Reveal'].iloc[i] - high_tolerance) * each_group['Distance From Pile North'].iloc[i + 1] * (pitch / 27)
        else:
            each_group.loc[each_group.index[i], 'Fill'] = 0


    #Area
    each_group['Area'] = np.nan
    for i in range(15):
            if each_group['Delta'].iloc[i] != "SAFE":
                if each_group['Delta'].iloc[i] != 0:  # Avoid dividing by zero
                    each_group['Area'].iloc[i] = (each_group['Cut'].iloc[i] + each_group['Fill'].iloc[i]) / abs(each_group['Delta'].iloc[i])
                else:
                    each_group['Area'].iloc[i] = 0
            else:
                each_group.loc[each_group.index[i], "Area"] = 0


    #Table Cut
    each_group['Table Cut'] = 0
    for i in range(15):
        each_group['Table Cut'] += each_group['Cut'].iloc[i]


    #Table Fill
    each_group['Table Fill'] = 0
    for i in range(15):
        each_group['Table Fill'] += each_group['Fill'].iloc[i]


    #Table Area
    each_group['Table Area'] = 0
    for i in range(15):
        each_group['Table Area'] += each_group['Area'].iloc[i]


    #Table Volume
    each_group['Table Volume'] = each_group['Table Cut'] + each_group['Table Fill']


    #Old Grade
    each_group['Old Grade'] = each_group['z']
    for i in range(15):
        each_group['Old Grade'].iloc[i] = each_group['z'].iloc[i]


    #New Grade
    each_group['New Grade'] = 0
    for i in range(15):
        if each_group['Delta'].iloc[i] == "SAFE":
            each_group['New Grade'].iloc[i] = each_group['Old Grade'].iloc[i]
        else:
            each_group['New Grade'].iloc[i] =  each_group['Old Grade'].iloc[i] + each_group['Delta'].iloc[i]


    #Top of Pile
    each_group['TOP'] = each_group['TOP Elevation']

    #True Reveal
    each_group['True Reveal'] = round(each_group['TOP'] - each_group['New Grade'], 1)


#******************************************************************************************************************************************************************
# Re-calculating Pile reveal and subsequent columns to account for table volumn and cut/fill
    def optimize():
     low_volume =  each_group.loc[each_group.index[-1], 'Table Volume']
     pile_reveal = {}
    #  print('low volume:', low_volume)
    #  print("pile reveal", pile_reveal)
    
     
     if each_group.loc[each_group.index[0], 'Table Volume'] > 0:
       
        
        if each_group.loc[each_group.index[0], 'Pile Reveal'] < high_tolerance:
            # print ('start', each_group.loc[each_group.index[0], 'Pile Reveal'])
            each_group.loc[each_group.index[0], 'Pile Reveal'] += step
            # print ('increment', each_group.loc[each_group.index[0], 'Pile Reveal'])
            each_group.loc[each_group.index[-1], 'Pile Reveal'] = each_group.loc[each_group.index[0], 'Pile Reveal']
        




            # Adding column for Top of Pile Elevation for Pile1 and Pile15
            each_group.loc[each_group.index[0], 'TOP Elevation'] = each_group['z'].iloc[0] + each_group['Pile Reveal'].iloc[0]
            each_group.loc[each_group.index[-1], 'TOP Elevation'] = each_group['z'].iloc[-1] + each_group['Pile Reveal'].iloc[0]


            # Column for Table Slope Piles1and15
            each_group.loc[each_group.index[0], 'Table Slope'] = (each_group['TOP Elevation'].iloc[-1] - each_group['TOP Elevation'].iloc[0]) /( each_group['n'].iloc[0] - each_group['n'].iloc[-1])
            each_group.loc[each_group.index[-1], 'Table Slope'] = (each_group['TOP Elevation'].iloc[-1] - each_group['TOP Elevation'].iloc[0]) /( each_group['n'].iloc[0] - each_group['n'].iloc[-1])


            #conditional for calculating Table Slope for Piles2-14; slope change is a constant for now until we implement user interactive functionality
            for i in range(13):
                if each_group['Ground Slope'].iloc[i + 1] > each_group['Table Slope'].iloc[i] + slope_change:
                    each_group['Table Slope'].iloc[i + 1] = each_group['Table Slope'].iloc[i] + slope_change
                elif each_group['Ground Slope'].iloc[i + 1] < each_group['Table Slope'].iloc[i] - slope_change:
                    each_group['Table Slope'].iloc[i + 1] = each_group['Table Slope'].iloc[i] - slope_change
                else:
                    each_group['Table Slope'].iloc[i + 1] = each_group['Ground Slope'].iloc[i + 1]


            #column for Top of Pile Elevation Piles2-14
            for i in range(13):
                each_group['TOP Elevation'].iloc[i + 1] = each_group['TOP Elevation'].iloc[i] + each_group['Distance From Pile North'].iloc[i +1] * each_group['Table Slope'].iloc[i +1]
            

            #column for Pile Reveal Piles2-14
            for i in range(13):
                each_group['Pile Reveal'].iloc[i + 1] = each_group['TOP Elevation'].iloc[i + 1] - each_group['z'].iloc[i + 1]


            #Delta Column conditional 
            for i in range(15):
                each_group.loc[each_group.index[i], 'Delta'] = 'SAFE'
                if each_group['Pile Reveal'].iloc[i] < high_tolerance and each_group['Pile Reveal'].iloc[i] >= low_tolerance:
                    each_group.loc[each_group.index[i], 'Delta'] = "SAFE"
                elif each_group['Pile Reveal'].iloc[i] > high_tolerance:
                    each_group.loc[each_group.index[i], 'Delta'] = each_group['Pile Reveal'].iloc[i] - high_tolerance
                elif each_group['Pile Reveal'].iloc[i] < low_tolerance:
                    each_group.loc[each_group.index[i], 'Delta'] = each_group['Pile Reveal'].iloc[i] - low_tolerance

            
        #     #CUT AND FILL POINTS


            #cut
            for i in range (15):
                if each_group['Pile Reveal'].iloc[i] < low_tolerance:
                    each_group['Cut'].iloc[i] = (low_tolerance - each_group['Pile Reveal'].iloc[i]) * each_group['Distance From Pile North'].iloc[i + 1] * (pitch / 27)
                else:
                    each_group.loc[each_group.index[i], 'Cut'] = 0


            #fill
            for i in range (15):
                if each_group['Pile Reveal'].iloc[i] > high_tolerance:
                    each_group['Fill'].iloc[i] = (each_group['Pile Reveal'].iloc[i] - high_tolerance) * each_group['Distance From Pile North'].iloc[i + 1] * (pitch / 27)
                else:
                    each_group.loc[each_group.index[i], 'Fill'] = 0


            #Area
            each_group['Area'] = np.nan
            for i in range(15):
                    if each_group['Delta'].iloc[i] != "SAFE":
                        if each_group['Delta'].iloc[i] != 0:  # Avoid dividing by zero
                            each_group['Area'].iloc[i] = (each_group['Cut'].iloc[i] + each_group['Fill'].iloc[i]) / abs(each_group['Delta'].iloc[i])
                        else:
                            each_group['Area'].iloc[i] = 0
                    else:
                        each_group.loc[each_group.index[i], "Area"] = 0


            #Table Cut
            each_group['Table Cut'] = 0
            for i in range(15):
                each_group['Table Cut'] += each_group['Cut'].iloc[i]


            #Table Fill
            each_group['Table Fill'] = 0
            for i in range(15):
                each_group['Table Fill'] += each_group['Fill'].iloc[i]


            #Table Area
            each_group['Table Area'] = 0
            for i in range(15):
                each_group['Table Area'] += each_group['Area'].iloc[i]


            #Table Volume
            



            #Old Grade
            each_group['Old Grade'] = each_group['z']
            for i in range(15):
                each_group['Old Grade'].iloc[i] = each_group['z'].iloc[i]


            #New Grade
            each_group['New Grade'] = 0
            for i in range(15):
                if each_group['Delta'].iloc[i] == "SAFE":
                    each_group['New Grade'].iloc[i] = each_group['Old Grade'].iloc[i]
                else:
                    each_group['New Grade'].iloc[i] =  each_group['Old Grade'].iloc[i] + each_group['Delta'].iloc[i]



            #Top of Pile
            each_group['TOP'] = each_group['TOP Elevation']

            #True Reveal
            each_group['True Reveal'] = round(each_group['TOP'] - each_group['New Grade'], 1)

            
            
            each_group['Table Volume'] = each_group['Table Cut'] + each_group['Table Fill']
            


            if each_group.loc[each_group.index[0], 'Table Volume'] <=  low_volume:
                low_volume = each_group.loc[each_group.index[0], 'Table Volume']
            
                optimize()
                #need to optmiize each group and call the recursive function ONLY next step of pile reveal table volume is lower than the one before 
       
    optimize()
    
    

    
   # reordering column order and excluding certain columns for visual clarity
    column_order = ['n', 'e', 'z', 'Ground Slope', 'Distance From Pile North', 'Table Slope', 
                'TOP Elevation', 'Pile Reveal', 'Delta','Cut', 'Fill',  'Area', 'Table Cut', 
                'Table Fill', 'Table Area', 'Table Volume', 'Old Grade', 'New Grade', 'TOP', 'True Reveal'] 

    # column_order = ['n', 'e', 'z', 'Ground Slope', 'Distance From Pile North', 'Table Slope', 
    #                 'TOP Elevation', 'Pile Reveal', 'Delta','Cut', 'Fill', 'Table Volume'] 

    each_group = each_group[column_order]


    #Add each group of Piles with new columns to the Grouped Piles list, which will hold all groups.
    grouped_piles.append(each_group)

    #********FOR STATEMENT ENDS**************


    #************OUTPUTS**************


Outputs = {}

##total rows of piles
number_of_rows = len(grouped_piles) * 15
Outputs["Total Rows"] = number_of_rows


#Total Cut
cut_column = 'Cut'
cut_sum = 0

for group in grouped_piles:
    column_sum = group[cut_column].sum()
    cut_sum += column_sum

    Outputs['Total Cut CUYD'] = cut_sum


#Total Fill
fill_column = 'Fill'
fill_sum = 0

for group in grouped_piles:
    column_sum = group[fill_column].sum()
    fill_sum += column_sum

    Outputs['Total Fill CUYD'] = fill_sum


#Total Disturbed Area
area_column = 'Area'
disturbed_area_sum = 0

for group in grouped_piles:
    column_sum = group[area_column].sum()
    disturbed_area_sum += column_sum

    Outputs['Total Disturbed Area SQYD'] = disturbed_area_sum


#Max Cut
max_cut = 0

for group in grouped_piles:
    max_value = group[cut_column].max()
   
    if max_value > max_cut:
        max_cut = max_value

Outputs['Max Cut CUYD'] = max_cut


#Max Fill
max_fill = 0

for group in grouped_piles:
    max_value = group[fill_column].max()
   
    if max_value > max_fill:
        max_fill = max_value

Outputs['Max Fill CUYD'] = max_fill


#Max Area
max_area = 0

for group in grouped_piles:
    max_value = group[area_column].max()
   
    if max_value > max_area:
        max_area = max_value

Outputs['Max Area CUYD'] = max_area

#Max Slope
max_slope = 0

for group in grouped_piles:
    max_value = group['Table Slope'].max()
   
    if max_value > max_slope:
        max_slope = max_value

Outputs['Max Slope'] = max_slope


#Min Slope
min_slope = 0

for group in grouped_piles:
    min_value = group['Table Slope'].min()
   
    if min_value < min_slope:
        min_slope = min_value

Outputs['Min Slope'] = min_slope


#Average Pile Reveal
overall_sum = 0

for group in grouped_piles:
    overall_sum += group['True Reveal'].sum()

overall_average = overall_sum / (number_of_rows)
Outputs['Average Pile Reveal LNFT'] = overall_average


end = time.time()



# Print an Individual Pile group
group_index_to_print = 543
    # selected_group = grouped_piles[group_index_to_print]
    # print(f"Selected Group {group_index_to_print}:")
    # print(selected_group)


#Print all the grouped Piles
for i, new_group_df in enumerate(grouped_piles):
    print(f"Group {i}:")
    print(new_group_df)
    print("\n")

print("Outputs", Outputs)

print("Execution time:", end - start, " seconds" )

