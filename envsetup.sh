# Copyright 2024 Martin Burri
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# check preconditions
for tool in fzf exiv2 convert cksum md5sum ffmpeg; do
    [[ $(type -P $tool) ]] || >&2 echo "ERROR: $tool not installed!"
done

# Setup special prompt
export PS1="(pwf) $PS1"

# Add bin folder to PATH
export PATH="$(pwd)/bin/:$PATH"

# define global variables for pwf scripts
export PWF_ALLOWED_CHARACTERS='[:alnum:]äöüÄÖÜé~._-'

export PWF_HOME="$HOME/pictures/own_photos/"
[[ "$PWF_HOME" =~ ^[//$PWF_ALLOWED_CHARACTERS]*$ ]] || \
    >&2 echo "ERROR: PWF_HOME path contains illegal characters!"
# PWF_HOME can be considered save from now on...

export PWF_RAW_EXTENSIONS="NEF NRW CR2"
export PWF_JPG_EXTENSIONS="jpg JPG jpeg JPEG"

export PWF_RAW_REGEX='^.*\.(NEF|NRW|CR2)'  # can be used e.g. with [[ =~ ]]
export PWF_JPG_REGEX='^.*\.(jpg|JPG|jpeg|JPEG)'  # can be used e.g. with [[ =~ ]]

# Set up fzf environment:
export FZF_CTRL_T_COMMAND="find -L $PWF_HOME"
export FZF_ALT_C_COMMAND="find -L $PWF_HOME -type d"

# Set up fzf key bindings and fuzzy completion
eval "$(fzf --bash)"

# Define fzf path completion command
_fzf_compgen_path() {
    $FZF_CTRL_T_COMMAND
}

# Define fzf dir completion command
_fzf_compgen_dir() {
    $FZF_ALT_C_COMMAND
}

_pwf_err_exit() {
    >&2 echo "ERROR: $1"
    exit 1
}
export -f _pwf_err_exit

_pwf_is_event_dir() {
    [[ $(dirname "$1") =~ [0-9]{4} ]] && return 0 || return 1
}
export -f _pwf_is_event_dir

_pwf_print_fzf_info() {
    cat <<'EOF'
    Any path can be specified either by by normal means of bash (e.g. with tab
    completion) or by using the FZF tool. Type **<tab> to bring the FZF tool to 
    front where you can select the desired path much faster (see man fzf for 
    more details). Paths are automatically bound to the pwf folder structure,
    so this script can be used from anywhere whith consistent behavior.
EOF
}
export -f _pwf_print_fzf_info

# Enable fuzzy completion for pwf commands
alias ll >/dev/null 2>&1 || alias ll="ls -alF"
_fzf_setup_completion dir ll
_fzf_setup_completion dir pwf-check
_fzf_setup_completion path pwf-extract-previews
_fzf_setup_completion dir pwf-move-new-to-original
_fzf_setup_completion path pwf-protect
_fzf_setup_completion dir pwf-prepare-lab
_fzf_setup_completion dir pwf-statistics
_fzf_setup_completion path pwf-rename-by-date
_fzf_setup_completion dir pwf-cleanup
_fzf_setup_completion path pwf-downsize-image
_fzf_setup_completion path pwf-downsize-video
_fzf_setup_completion path pwf-link

