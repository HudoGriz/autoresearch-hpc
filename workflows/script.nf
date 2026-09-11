// Migration adapter for legacy scripts. Native workflows declare task inputs.
// Arbitrary shell dependencies cannot be inferred, so caching is disabled here.
params.arh_script = null
params.arh_project = null

def shellQuote(value) { "'" + value.toString().replace("'", "'\"'\"'") + "'" }

process LEGACY_SCRIPT {
    cache false
    script:
    """
    cd ${shellQuote(params.arh_project)}
    bash ${shellQuote(params.arh_script)}
    """
}

workflow { LEGACY_SCRIPT() }
