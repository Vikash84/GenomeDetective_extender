
# coding: utf-8

# # Genome Detective output conversion to CAMI profiling
# 
# Author: Sam Nooij  
# Date: 2018-05-24
# Developed with Jupyter notebook
# 
# Input: 
# - sample ID
# - taxon
# - number of reads
# - total reads
# 
#     - These data (for both the assignments and the discoveries) can be derived from: the "bokeh input", output by `GenomeDetective_heatmaps.py`
# 
# - NCBI taxonomy DB (through ETE toolkit, see [this tutorial](http://etetoolkit.org/docs/2.3/tutorial/tutorial_ncbitaxonomy.html))
# 
# Output: table in [CAMI profiling format](https://github.com/bioboxes/rfc/blob/60263f34c57bc4137deeceec4c68a7f9f810f6a5/data-format/profiling.mkd)
# 
# Required python packages:
#  - pandas
#  - ete3
#  
# For automatic use in snakemake. The corresponding snakemake rule should provide the input:
#  - the parsed report file ("results/GenomeDetective_results.csv")
#  - a list of names for the output (e.g. ["results/3_1_GenomeDetective_CAMI-profiling.tsv", ...])
#  
#   ** Remember that an output has to be generated for each sample, separately! **


#Import required python libraries-------------------------------
import pandas as pd         #dataframe and csv export
from ete3 import NCBITaxa   #work with NCBI taxonomy


#Set variables--------------------------------------------------
DATA_TABLE = snakemake.input[0]
PROFILE = snakemake.output[0] #one at a time
SAMPLE = snakemake.wildcards.sample #sample ID can also be obtained from the Snakefile
#Extract the sample ID from the file name:
# split on '/': remove folder name, then extract the string
# until '_Genome', which should extract "_GenomeDetective_CAMI-profiling.tsv"

#Define functions-----------------------------------------------
def create_CAMI_profile(data_file, sample_id):
    """
    CSV Parser for converting information to the CAMI profiling
    format.
    
    Input: csv file with the required information, sample ID
        and the name of the file to write to
    Output: header and contents of the CAMI profile file
        (see format linked above)
    """
    dataframe = pd.read_csv(data_file)
    subset = dataframe[dataframe["sample"] == sample_id]
    taxa = subset["Assignment"]
    total_percentages = subset["percentage_of_total_reads"]
    ncbi = NCBITaxa()
    
    rank_list_list = [] #save all taxonomies to find the longest
    #I use the longest, because virus taxonomy is diverse...
    output_list = [] #stores the CAMI profiles as strings
    
    for name in taxa:
        #remove names that have some addition in brackets,
        # like " (segment 1)"
        if ' (' in name:
            ncbi_name = name[:name.index(' (')]
        else:
            ncbi_name = name
            
        taxon_and_id = ncbi.get_name_translator([ncbi_name])
        #ncbi.get_name_translator() returns a dictionary { 'taxon' : [id]}
        taxid = taxon_and_id[ncbi_name]
        #taxid is a list with one number
        taxid_nr = taxid[0]

        rank_dict = ncbi.get_rank(taxid)
        #ncbi.get_rank() requires a list of IDs, and returns a dictionary:
        # {id: 'rank'}
        rank = rank_dict[taxid_nr]

        tax_path_dict = ncbi.get_lineage_translator(taxid)#[taxid_nr]
        #ncbi.get_lineage_translator() requires a list of IDs, and returns
        # a dictionary {leaf_id: [root_id, node_id, leaf_id]}
        tax_path = tax_path_dict[taxid_nr][1:]

        tax_path_sn = []
        #with a for-loop you can translate the taxids in the list
        # 'tax_path' to their corresponding scientific names (sn)
        for t in tax_path:
            tax_path_sn.append(ncbi.get_taxid_translator([t])[t])

        rank_list = []
        #Making this list requires using a for-loop;
        # using the function on a list makes an UNORDERED dictionary
        #Also, since the path differs between branches, I will look
        # for the longest using a list of lists
        for taxid in tax_path:
            rank_dict = ncbi.get_rank([taxid])
            rank = rank_dict[taxid]
            rank_list.append(rank)

        rank_list_list.append(rank_list)    

        tax_path_string = '|'.join(map(str, tax_path))
        tax_path_sn_string = '|'.join(tax_path_sn)
        
        percentage = subset.loc[subset["Assignment"] == name]["percentage_of_total_reads"].values[0]
        
        output_line = "%s\t%s\t%s\t%s\t%s" % (taxid_nr, rank, tax_path_string, tax_path_sn_string, percentage)
        
        output_list.append(output_line)
        
    longest_taxonomy = '|'.join(max(rank_list_list, key = len))
    
    #Read the specification for details about this header:
    #https://github.com/bioboxes/rfc/blob/60263f34c57bc4137deeceec4c68a7f9f810f6a5/data-format/profiling.mkd
    header = """# Taxonomic Profiling Output
@SampleID:%s
@Version:0.9.3
@Ranks:%s\t#the longest path in this sample: virus taxonomy is messy
@TaxonomyID:ncbi-taxonomy_2018-05-25
@@TAXID\tRANK\tTAXPATH\tTAXPATHSN\tPERCENTAGE
""" % (sample_id, longest_taxonomy)
    
    return(header, output_list)


#Script execution------------------------------------------------
if __name__ == "__main__":
    header, output_list = create_CAMI_profile(data_file = DATA_TABLE, sample_id = SAMPLE)
    
    with open(PROFILE, 'w') as output_table:
        output_table.write(header)
        output_table.write('\n'.join(output_list))