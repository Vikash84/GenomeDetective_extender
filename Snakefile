"""
Author: Sam Nooij
Date: 2018-05-17

Pipeline to summarise and visualise output from Genome Detective (GD)
of multiple samples. It requires:
  - XML files (save as "[sample ID]_results.xml")
  - CSV files (save as "[sample ID]_results.csv")
  
Note: at the moment, 'discovery' assignments are ignored.
Note: for now, I assume the sample ID is a combination of
    run ID and sample ID. E.g. run 3, sample 1 makes a file
    "3_1_results.csv"

As a result, the pipeline creates:
  - summary table ("GD_summary.csv") that can be used to 
    report the results and compare to the PCR results. 
    It has the following fields:
      - run_id
      - sample_id
      - total_reads
      - low_quality_reads
      - non_viral_reads
      - viral_reads
      - pcr_result (EMPTY - fill in manually!)
      - ct_value (EMPTY - fill in manually!)
      - ngs_results (classifications/assignments by GD;
         you may want to add typing tool results manually)
      - coverage%
      - contigs
      - number_of_reads
      - fraction_total_reads
      - pcr_ngs_congruence (EMPTY - fill in manually!)
      - pcr_ngs_comments (EMPTY - fill in manually!)
  - CAMI profiling output (see also: https://github.com/bioboxes/rfc/blob/60263f34c57bc4137deeceec4c68a7f9f810f6a5/data-format/profiling.mkd)
  - heatmap + data tables (using Bokeh)
  
These results may be used to check the output, compare to PCR results
and to other pipeliens, and the heatmap may serve as 
'virome comparison tool'.      
"""

import glob

FOLDER = "results/"
XML = FOLDER + "*_results.xml"
CSV = FOLDER + "*_results.csv"
DISCOVERIES = FOLDER + "*_discovery.csv"

XML_FILES = glob.glob(XML)
CSV_FILES = glob.glob(CSV)
DISCOVERY_FILES = glob.glob(DISCOVERIES)

SAMPLES = [ file[8:file.index('_results.xml')] for file in XML_FILES ]

rule all:
    input:
        "tmp/bokeh_input.csv",
        "results/GenomeDetective-PCR_summary.csv",
        expand("results/{sample}_GenomeDetective_CAMI-profiling.tsv", sample = SAMPLES)
        
rule parse_xml:
    input:
        XML_FILES
    output:
        "tmp/GenomeDetective_results-xml.csv"
    script:
        "bin/GenomeDetective_XML_parser.py"

rule write_report:
    input:
        csv = CSV_FILES,
        parsed_xml = "tmp/GenomeDetective_results-xml.csv"
    output:
        "results/GenomeDetective-PCR_summary.csv"
    script:
        "bin/GenomeDetective_report_writer.py"
    
rule create_heatmaps:
    input:
        assignments=CSV_FILES,
        discoveries=DISCOVERY_FILES,
        parsed_xml="tmp/GenomeDetective_results-xml.csv"
    output:
        heatmap_a="results/GenomeDetective_heatmap_A.html",
        #assignments
        heatmap_d="results/GenomeDetective_heatmap_D.html",
        #discoveries
        heatmap_ad="results/GenomeDetective_heatmap_AD.html",
        #assignments + discoveries in one map
        data_table="tmp/bokeh_input.csv"
        #table on which heatmaps are based
    params:
        colour = "#[hex-code]"
    script:
        "bin/GenomeDetective_heatmaps.py"
    #shell:
    #    "python bin/GenomeDetective_heatmaps.py {params.colour}"
    #Uncomment this shell command if you want to change the colour of the heatmaps
    
rule convert_to_cami_profiling:
    input:
        "results/GenomeDetective-PCR_summary.csv"
    output:
        "results/{sample}_GenomeDetective_CAMI-profiling.tsv"
    script:
        "bin/GenomeDetective_to_CAMI-profiling.py"