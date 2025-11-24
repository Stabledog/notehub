#!/bin/bash
# notehub-dev.bashrc
# For development env only

_python() {
    [[ -n ${PythonVer} ]] && { echo "${PythonVer}"; return; }
    local runtime=/workarea/notehub/runtime.txt
    [[ -f $runtime ]] && {
        export PythonVer
        PythonVer="$(grep -E '^python-[0-9.]+$' $runtime | tr -d '-' )"
        echo "${PythonVer}"
        return
    }
    export PythonVer=python3.13
    echo "${PythonVer}"
}

notehub() {
    GH_TOKEN=${GH_ENTERPRISE_TOKEN} GH_HOST=${GH_HOST_ENTERPRISE} ${PythonVer} -m notehub "$@"
}
