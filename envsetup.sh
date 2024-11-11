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

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
(cd $SCRIPT_DIR && python3 -m venv venv --prompt pwf)
. "$SCRIPT_DIR"/venv/bin/activate

# Add bin folder to PATH
export PATH="$SCRIPT_DIR/bin/:$PATH"
export PYTHONPATH="$SCRIPT_DIR/bin/:$PYTHONPATH"

# define global variables for pwf scripts
export PWF_ALLOWED_CHARACTERS='[:alnum:]äöüÄÖÜé~._-'
export PWF_ROOT_PATH="$HOME/pictures/own_photos/"
[[ "$PWF_ROOT_PATH" =~ ^[//$PWF_ALLOWED_CHARACTERS]*$ ]] || \
    >&2 echo "ERROR: PWF_ROOT_PATH path contains illegal characters!"
# PWF_ROOT_PATH can be considered save from now on...

# Set up fzf environment:
export FZF_CTRL_T_COMMAND="find -L $PWF_ROOT_PATH"
export FZF_ALT_C_COMMAND="find -L $PWF_ROOT_PATH -type d"

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

# Enable fuzzy completion for pwf commands
alias ll >/dev/null 2>&1 || alias ll="ls -alF"
_fzf_setup_completion dir ll
_fzf_setup_completion dir pwf_check.py
_fzf_setup_completion path pwf_extract_previews.py
_fzf_setup_completion dir pwf_import.py
_fzf_setup_completion path pwf_protect.py
_fzf_setup_completion dir pwf_prepare_lab.py
_fzf_setup_completion dir pwf_statistics.py
_fzf_setup_completion path pwf_rename_by_date.py
_fzf_setup_completion dir pwf_cleanup.py
_fzf_setup_completion path pwf_downsize_image.py
_fzf_setup_completion path pwf_downsize_video.py
_fzf_setup_completion path pwf_link.py

