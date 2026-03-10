"""Shell completion script generation."""


def generate(shell: str) -> str:
    """Generate completion script for the given shell."""
    generators = {
        "bash": _bash,
        "zsh": _zsh,
        "fish": _fish,
    }
    gen = generators.get(shell)
    if gen is None:
        raise ValueError(f"Unsupported shell: {shell}. Choose from: bash, zsh, fish")
    return gen()


def _bash() -> str:
    return """\
_getscript() {
    local cur opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    opts="--search --apple --limit --list --json --ttml --timestamps --markdown --proxy --cookies --no-color --quiet --verbose -o --output --completions -h --help --version"

    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _getscript getscript"""


def _zsh() -> str:
    return """\
#compdef getscript

_getscript() {
    _arguments \\
        '1:url or id:' \\
        '--search[Search for content by topic or creator]:query:' \\
        '--apple[Search Apple Podcasts instead of YouTube]' \\
        '--limit[Number of search results]:count:' \\
        '--list[Print search results without interactive selection]' \\
        '--json[Output as JSON]' \\
        '--ttml[Output raw TTML XML (Apple only)]' \\
        '--timestamps[Include timestamps]' \\
        '--markdown[Output as Markdown]' \\
        '--proxy[Proxy URL for YouTube requests]:url:' \\
        '--cookies[Netscape cookie file for YouTube auth]:cookie file:_files' \\
        '--no-color[Disable colors]' \\
        '--quiet[Suppress progress output]' \\
        '--verbose[Show detailed errors]' \\
        {-o,--output}'[Write to file]:output file:_files' \\
        '--completions[Generate shell completions]:shell:(bash zsh fish)' \\
        {-h,--help}'[Show help]' \\
        '--version[Show version]'
}

_getscript "$@"
"""


def _fish() -> str:
    return """\
complete -c getscript -l search -d 'Search for content by topic or creator' -r
complete -c getscript -l apple -d 'Search Apple Podcasts instead of YouTube'
complete -c getscript -l limit -d 'Number of search results' -r
complete -c getscript -l list -d 'Print search results without interactive selection'
complete -c getscript -l json -d 'Output as JSON'
complete -c getscript -l ttml -d 'Output raw TTML XML (Apple only)'
complete -c getscript -l timestamps -d 'Include timestamps'
complete -c getscript -l markdown -d 'Output as Markdown'
complete -c getscript -l proxy -d 'Proxy URL for YouTube requests' -r
complete -c getscript -l cookies -d 'Netscape cookie file for YouTube auth' -r -F
complete -c getscript -l no-color -d 'Disable colors'
complete -c getscript -l quiet -d 'Suppress progress output'
complete -c getscript -l verbose -d 'Show detailed errors'
complete -c getscript -s o -l output -d 'Write to file' -r -F
complete -c getscript -l completions -d 'Generate shell completions' -r -fa 'bash zsh fish'
complete -c getscript -s h -l help -d 'Show help'
complete -c getscript -l version -d 'Show version'"""
