# notehub-dev.bashrc
# For development env only
export PYTHONPATH=/workarea/notehub/src

notehub() {
    GH_TOKEN=${GH_ENTERPRISE_TOKEN} GH_HOST=${GH_HOST_ENTERPRISE} python3.13 -m notehub "$@"
}
