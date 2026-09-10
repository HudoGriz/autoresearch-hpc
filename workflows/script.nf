// Migration adapter for legacy scripts. Native workflows declare task inputs.
// Arbitrary shell dependencies cannot be inferred, so caching is disabled here.
params.dl_script = null
params.dl_project = null

def shellQuote(value) { "'" + value.toString().replace("'", "'\"'\"'") + "'" }

process LEGACY_SCRIPT {
    cache false
    script:
    """
    cd ${shellQuote(params.dl_project)}
    bash ${shellQuote(params.dl_script)}
    """
}

workflow { LEGACY_SCRIPT() }
