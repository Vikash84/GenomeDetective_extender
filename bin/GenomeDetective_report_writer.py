
# coding: utf-8

# # Genome Detective report writer script
# 
# Author: Sam Nooij  
# Date: 2018-05-18
# Developed in Jupyter notebook
# 
# Input:
# 1. parsed XML file (e.g. "tmp/GenomeDetective_results.csv") as generated by bin/GenomeDetective_XML_parser.py
# 2. result CSV files as generated by [GenomeDetective](http://www.genomedetective.com/app/typingtool/virus/)
# 
# Output: table in csv format, providing:
# - run_id
# - sample_id
# - total_reads
# - low_quality_reads
# - non_viral_reads
# - viral_reads 
# - pcr_result
# - ct_value 
# - ngs_results
# - coverage%
# - contigs
# - number_of_reads
# - fraction_of_total_reads
# - percentage_of_total
# - fraction_of_viral_reads
# - percentage_of_viral
# - pcr_ngs_congruence
# - pcr_ngs_comments
# - human_virus_reads
# - plant_virus_reads
# - phage_reads
# - other_viral_reads
# - runtime
# 
# Required python packages:
#  - pandas
#  
# For automatic use in snakemake. The corresponding snakemake rule should provide the input:
#  - the parsed XML file ("tmp/GenomeDetective_results.csv")
#  - a list of CSV files (their names, as strings; e.g. [ "1_a_results.csv", "1_b_results.csv" ]
#  - a name for the output (e.g. "tmp/GenomeDetective-PCR_summary.csv")

###Import required python libraries------------------------
import pandas as pd         #dataframe and csv export

CSV_FILES = snakemake.input['csv']
PARSED_XML = snakemake.input['parsed_xml']
OUTPUT_FILE = snakemake.output[0]

###Parser functions-----------------------------------------
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
    
    return(run_id, sample_id)

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

def combine_tables(parsed_xml, csv_list):
    """
    Input: 1. parsed XML table, with the fields:
    run_id sample_id total_reads low_quality_reads non_viral_reads viral_reads runtime
           2. CSV results files, with the fields:
    Assignment # Contigs Mapped # Reads Coverage (%) Mapped depth <br/>of Coverage NT Identity (%) AA Identity (%) Contigs
    Output: one table with the fields:
    run_id sample_id total_reads low_quality_reads non_viral_reads viral_reads  pcr_result ct_value ngs_results coverage% contigs number_of_reads fraction_of_total_reads fraction_of_viral_reads pcr_ngs_congruence pcr_ngs_comments human_virus_reads plant_virus_reads phage_reads other_viral_reads runtime
    """
    xml_df = pd.read_csv(parsed_xml)
    csv_df = create_concatenated_dataframe(csv_list)
    csv_df["run_id"] = csv_df["run_id"].apply(int)
    #This column was read as strings and could not merge with
    # xml_df, because that contained integers...
        
    desired_columns =     {"run_id": "a","sample_id": "a","total_reads": "a",
     "low_quality_reads": "a","non_viral_reads": "a",
     "viral_reads": "a","pcr_result": "m", "ct_value": "m",
     "GD_assignment": "a","coverage%": "a",
     "contigs": "a","number_of_reads": "a",
     "fraction_of_total_reads": "c","fraction_of_viral_reads": "c",
     "pcr_ngs_congruence": "m", "pcr_ngs_comments": "m",
     "human_virus_reads": "m", "plant_virus_reads": "m",
     "phage_reads": "m", "other_viral_reads": "m","runtime": "a"}
    #a = available data (can copy), m = manual filling, c = calculate

    original_columns =     {
        "GD_assignment": "Assignment", "contigs": "# Contigs",
        "number_of_reads": "Mapped # Reads", "coverage%": "Coverage (%)",
    }
    report_df = xml_df
    empty = "fill me in"
    
    #First step: merge the 'a' part
    report_df = report_df.merge(csv_df, how = "right", on = ["run_id", "sample_id"])

    #Second step: fill in the gaps
    for key, value in desired_columns.items():
        if value == "m":
        #These have to be filled manually
            report_df[key] = empty

        elif value == "a":
        #These data are avaible and automatically filled in
            if key in report_df:
                pass
            else:
                #check if the column name is different
                if key in original_columns:
                    key = original_columns[key]
                #report it missing if it is still not there
                if key not in report_df:
                    print("%s is a missing column" % key)
                #If it is in the dataframe already, pass
                else:
                    pass
                
        elif value == "c":
        #These data have to be calculated with what is available
            if "total" in key:
                report_df = report_df.assign(
                    fraction_of_total_reads=lambda report_df:
                    report_df["Mapped # Reads"] / report_df.total_reads)
                #fraction = number / total_reads
                report_df = report_df.assign(
                    percentage_of_total=lambda report_df:
                    report_df.fraction_of_total_reads * 100)
                #percentage = fraction * 100
            elif "viral" in key:
                report_df = report_df.assign(
                    fraction_of_viral_reads=lambda report_df:
                    report_df["Mapped # Reads"] / report_df.viral_reads)
                #fraction = number / viral_reads
                report_df = report_df.assign(
                    percentage_of_viral=lambda report_df:
                    report_df.fraction_of_viral_reads * 100)
                #percentage = fraction * 100
                pass
            
            else:
                pass
    
    report_df = report_df.drop("Mapped depth <br/>of Coverage", axis = 1)
        
    for key, value in original_columns.items():
        report_df = report_df.rename(columns={value: key})
        
    return(report_df)

###Script execution-----------------------------------------
if __name__ == "__main__":
    #Parse/collect the results in a Pandas dataframe
    report_df = combine_tables(parsed_xml = PARSED_XML, csv_list = CSV_FILES)
    
    #Reorder the columns
    column_order = ["run_id", "sample_id",
                    "pcr_result", "ct_value", 
                    "GD_assignment", "coverage%", "contigs", 
                    "pcr_ngs_congruence", "pcr_ngs_comments",
                    "number_of_reads", "fraction_of_total_reads", 
                    "percentage_of_total", "fraction_of_viral_reads", 
                    "percentage_of_viral",
                    "total_reads", "low_quality_reads", 
                    "non_viral_reads", "viral_reads",
                    "human_virus_reads", "plant_virus_reads",
                    "phage_reads", "other_viral_reads", "runtime"]
    
    report_df = report_df[column_order]
    
    #And save it as a csv file
    report_df.to_csv(OUTPUT_FILE, index = False)
    
    print("""\nDone!
The results have been written to: %s""" % OUTPUT_FILE)

