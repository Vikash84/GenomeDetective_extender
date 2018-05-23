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

`Snakemake -p tmp/bokeh_input.csv`

Or open a Jupyter Notebook and play with the `.ipynb` files in the `bin/` directory.