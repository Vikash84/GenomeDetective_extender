# GenomeDetective extender

_to do: write some documentation..._

Quick how-to:

- Use [conda](https://conda.io/docs/index.html)

- You need a folder named `results/` in which you have the output files of [Genome Detective](http://www.genomedetective.com/app/typingtool/virus/)
    - filenames as `[run_id]_[sample_id]_[extension]`, e.g. "3_1_results.csv"
    - extensions are: "results.csv" for the 'assigned' contigs,
    "discovery.csv" for the 'discovered' contigs and "results.xml" for the XML files.

- You also need a folder named `tmp/` to store intermediate files

`conda env create -n genomedetective -f envs/GD_parsed.yaml`

`source activate genomedetective`

`Snakemake -p`

Or open a Jupyter Notebook and play with the `.ipynb` files in the `bin/` directory.

-----

## Currently, the following files are created:

1. A CSV file derived from the XML (for easier reading/use in spreadsheets). This file contains:
    - the run ID (number)
    - the sample ID (number/code)
    - the total number of reads for that sample
    - the number of "low quality reads", i.e. those discarded by trimmomatic
    - the number of "non viral reads", i.e. those not recognised by DIAMOND as viral (against the UniRef90 + HIV from UniRef50 database)
    - the number of viral reads (by DIAMOND)
    - total runtime in seconds
    
2. A report table (as CSV) that combines results from the CSV and XML output files. This file summarises in 23 columns all information that may be interesting in comparing the assignments by Genome Detective to the (validated) qPCR results. (_Note that some fields still have to be filled in manually!_)

3. Heatmaps of the reported viruses ('virome comparison tool')