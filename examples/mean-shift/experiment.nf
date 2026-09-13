nextflow.enable.dsl=2

params.input = "${projectDir}/data.tsv"

process PAIRED_MEAN {
    input:
    path input_data

    output:
    path "result.json"

    script:
    """
    python3 ${projectDir}/analysis.py ${input_data} > result.json
    """
}

workflow {
    input_ch = Channel.fromPath(params.input, checkIfExists: true)
    PAIRED_MEAN(input_ch)
}
