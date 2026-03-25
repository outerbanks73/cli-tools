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
    opts="--search --limit --list --json --ttml --timestamps --markdown --no-upload --no-color --quiet --verbose -o --output --completions -h --help --version"

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
        '1:Apple Podcasts URL or episode ID:' \\
        '--search[Search Apple Podcasts by topic or creator]:query:' \\
        '--limit[Number of search results]:count:' \\
        '--list[Print search results without interactive selection]' \\
        '--json[Output as JSON]' \\
        '--ttml[Output raw TTML XML]' \\
        '--timestamps[Include timestamps]' \\
        '--markdown[Output as Markdown]' \\
        '--no-upload[Disable shared library submission]' \\
        '--no-color[Disable colors]' \\
        '--quiet[Suppress progress and upload status messages]' \\
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
complete -c getscript -l search -d 'Search Apple Podcasts by topic or creator' -r
complete -c getscript -l limit -d 'Number of search results' -r
complete -c getscript -l list -d 'Print search results without interactive selection'
complete -c getscript -l json -d 'Output as JSON'
complete -c getscript -l ttml -d 'Output raw TTML XML'
complete -c getscript -l timestamps -d 'Include timestamps'
complete -c getscript -l markdown -d 'Output as Markdown'
complete -c getscript -l no-upload -d 'Disable shared library submission'
complete -c getscript -l no-color -d 'Disable colors'
complete -c getscript -l quiet -d 'Suppress progress and upload status messages'
complete -c getscript -l verbose -d 'Show detailed errors'
complete -c getscript -s o -l output -d 'Write to file' -r -F
complete -c getscript -l completions -d 'Generate shell completions' -r -fa 'bash zsh fish'
complete -c getscript -s h -l help -d 'Show help'
complete -c getscript -l version -d 'Show version'"""
