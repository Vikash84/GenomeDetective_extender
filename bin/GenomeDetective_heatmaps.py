
# coding: utf-8

# # Genome Detective heatmap creation script
# 
# Author: Sam Nooij  
# Date: 2018-05-22
# Developed in Jupyter notebook
# 
# Input:
# 1. parsed XML file (e.g. "tmp/GenomeDetective_results.csv") as generated by bin/GenomeDetective_XML_parser.py
# 2. result CSV files as generated by [GenomeDetective](http://www.genomedetective.com/app/typingtool/virus/)
#     a. Assignments
#     b. Discoveries
# 
# Output: table in csv format, providing:
# - run_id
# - sample_id
# - taxon
# - total_reads
# - viral_reads 
# - coverage%
# - contigs
# - number_of_reads
# - fraction_of_total_reads
# - percentage_of_total
# - fraction_of_viral_reads
# - percentage_of_viral
# 
# Interactive (HTML) heatmaps of:
# - assigned taxa
# - discovered taxa
# - assigned and discovered taxa (together in the same map)
# 
# Required python packages:
#  - pandas
#  - bokeh
#  
# For automatic use in snakemake. The corresponding snakemake rule should provide the input:
#  - the parsed XML file ("tmp/GenomeDetective_results.csv")
#  - a list of CSV files (their names, as strings; e.g. [ "1_a_results.csv", "1_b_results.csv" ]; also for the discovery)
#  - a name for the output files


#Import all required libraries---------------------------------
import numpy as np
import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.io import output_notebook
from sys import argv


#Set parameters------------------------------------------------
#You may set the colour by passing an argument to this script
if len(argv) > 1:
    COLOUR = list(str(argv[1]))
#If you don't, the default (brown) is used
else:
    COLOUR = ["#6b2d18"] #Selected from coffee beans: http://s.eatthis-cdn.com/media/images/ext/851818315/coffee-beans.jpg

ASSIGNMENTS = snakemake.input['assignments']
DISCOVERIES = snakemake.input['discoveries']
PARSED_XML = snakemake.input['parsed_xml']
MAP_A = snakemake.output['heatmap_a']
MAP_D = snakemake.output['heatmap_d']
MAP_AD = snakemake.output['heatmap_ad']
OUTPUT_FILE = snakemake.output['data_table']


#Functions for parsing, dataframe building and heatmap creation
def pull_sample_name(filename):
    """
    The sample and run IDs are in the filename, e.g.:
    "3_10_results.xml"
    where the 3 is the run ID, and the 10 is the sample ID
    """
    error_msg = """
Expected underscores in the filename with the sample ID, e.g.
3_1_results.xml
Please provide sample names in this format.
    """
    
    assert filename.count('_') >= 2,         "%s" % error_msg
        
    run_id = filename.split('/')[-1].split('_')[0]
    
    if filename.count('_') > 2:
        sample_id = '_'.join(filename.split('/')[-1].split('_')[1:-1])
    else:
        sample_id = filename.split('/')[-1].split('_')[1]
    
    return run_id, sample_id

def create_concatenated_dataframe(csv_list):
    """
    Input: a list of Genome Detective output CSV files,
          e.g. ["3_1_results.csv", "4_D_results.csv"]
    Output: One concatenated dataframe of all the input files
    """
    csv_list = sorted(csv_list)
    
        
    #Step 2: open the files as dataframe, remove "Contigs" column and add sample IDs
    df_list = []
    for results_file in csv_list:
        results_df = pd.read_csv(results_file)
        results_df = results_df.drop("Contigs", axis = 1) #remove unnecessary (and long!) column
        run_id, sample_id = pull_sample_name(results_file)
        results_df["run_id"] = run_id
        results_df["sample_id"] = sample_id
        df_list.append(results_df)

    #Step 3: concatenate the dataframes
    super_df = pd.concat(df_list, ignore_index=True)
    
    return(super_df)

def calculate_fractions(dataframe):
    """
    Input: Dataframe with columns "number_of_reads",
        "total_reads", and "viral_reads"
    Output: Dataframe with fractiond and percentages
    """
    dataframe = dataframe.assign(fraction_of_total_reads = lambda dataframe:
                          dataframe["Mapped # Reads"] / dataframe["total_reads"])

    dataframe = dataframe.assign(fraction_of_viral_reads = lambda dataframe:
                          dataframe["Mapped # Reads"] / dataframe["viral_reads"])

    dataframe = dataframe.assign(percentage_of_total_reads = lambda dataframe:
                          dataframe["fraction_of_total_reads"] * 100)

    dataframe = dataframe.assign(percentage_of_viral_reads = lambda dataframe:
                          dataframe["fraction_of_viral_reads"] * 100)

    return(dataframe)

def create_heatmaps(dataframe):
    """
    Input: Dataframe with all required data:
        Taxon, number of reads, assigned/discovered
    Output: 3 heatmaps (assigned/discovered/both), as html files
            csv file with the data
    """
    
    def create_heatmap(subset_df, title, filename):
        samples = subset_df["sample"]
        assigned = subset_df["Assignment"]
        reads = subset_df["Mapped # Reads"]
        total_reads = subset_df["total_reads"]
        viral_reads = subset_df["viral_reads"]
        percent_of_total = subset_df["percentage_of_total_reads"]
        percent_of_viral = subset_df["percentage_of_viral_reads"]
        contigs = subset_df["# Contigs"]
        coverage = subset_df["Coverage (%)"]

        colors = len(reads) * COLOUR #multiply to make an equally long list
        
        max_load = max(percent_of_total)
        alphas = [ min( x / float(max_load), 0.9) + 0.1 for x in percent_of_total ]
        
        source = ColumnDataSource(
            data = dict(samples=samples, assigned=assigned,
                        reads=reads, total_reads=total_reads, viral_reads=viral_reads,
                        percent_of_total=percent_of_total, 
                        percent_of_viral=percent_of_viral,
                        contigs=contigs, coverage=coverage,
                        colors=colors, alphas=alphas)
        )
        
        TOOLS = "hover, save, pan, box_zoom, wheel_zoom, reset"

        p = figure(title = title,
                  #If desired, the sample can be displayed as "Run x, sample y"
                  # uncomment the next line if desired
                  #x_range = [ "Run %s, sample %s" % (x.split('_')[0], x.split('_')[1]) for x in list(sorted(set(samples))) ],
                  x_range = list(sorted(set(samples))),
                  y_range = list(reversed(sorted(set(assigned)))), #reverse to order 'from top to bottom'
                  x_axis_location = "above",
                  toolbar_location="right",
                  tools = TOOLS)

        if len(set(assigned)) > 25:
            p.plot_height = int(p.plot_height * 1.2)
        else:
            pass
        p.grid.grid_line_color = None
        p.axis.axis_line_color = None
        p.axis.major_tick_line_color = None
        if len(set(assigned)) > 15:
            p.axis.major_label_text_font_size = "10pt"
        else:
            p.axis.major_label_text_font_size = "12pt"
        p.axis.major_label_standoff = 0
        p.xaxis.major_label_orientation = np.pi/4
        p.title.text_color = COLOUR[0]
        p.title.text_font_size = "16pt"
        p.title.align = 'right'

        p.rect("samples", "assigned", 1, 1, source=source,
               color="colors", alpha="alphas", line_color=None)

        p.select_one(HoverTool).tooltips = [
            ('Sample', "@samples"),
            ('Taxon' , "@assigned"),
            ('Number of reads', "@reads"),
            ('Total reads', "@total_reads (@percent_of_total %)"),
            ('Estimated viral reads', "@viral_reads (@percent_of_viral %)"),
            ('Number of contigs', "@contigs"),
            ('Coverage', "@coverage %")
        ]

        output_file(filename, title=title)
        print("The heatmap %s has been created and written to: %s" % (title, filename))
        show(p)
        return(None)
    
    #Create an extra column that is the combination of run ID and sample ID:
    dataframe["sample"] = dataframe["run_id"].map(str) + '_' + dataframe["sample_id"].map(str)
    
    #Create heatmaps
    assignments = dataframe[dataframe.Assigned_Discovered == "Assigned"]
    create_heatmap(assignments, "GenomeDetective assignments", MAP_A)
    
    discoveries = dataframe[dataframe.Assigned_Discovered == "Discovered"]
    create_heatmap(discoveries, "GenomeDetective discoveries", MAP_D)
    
    create_heatmap(dataframe, "GenomeDetective assignments+discoveries", MAP_AD)
    
    return(None)


#Script execution----------------------------------------------
if __name__ == "__main__":
    #Prepare dataframes
    assignments = create_concatenated_dataframe(ASSIGNMENTS)
    assignments["Assigned_Discovered"] = "Assigned"

    discoveries = create_concatenated_dataframe(DISCOVERIES)
    discoveries["Assigned_Discovered"] = "Discovered"

    #Concatenate these two (assignments and discoveries)
    results_df = pd.concat([assignments, discoveries], ignore_index=True)
    results_df["run_id"] = results_df["run_id"].apply(int)
    
    xml_df = pd.read_csv(PARSED_XML)
    
    #Merge into one dataframe
    super_df = results_df.merge(xml_df, on = ["run_id", "sample_id"], how = "right")

    #Calculate fractions and percentages of total/viral reads
    super_df = calculate_fractions(super_df)

    #For easy use in the heatmaps, create a column that combines run_id + sample_id
    super_df["sample"] = super_df["run_id"].map(str) + '_' + super_df["sample_id"].map(str)
    
    create_heatmaps(super_df)
    
    super_df.to_csv(OUTPUT_FILE, index = False)
    print("The table with all the data on which the heatmaps are based has been written to %s" % OUTPUT_FILE)