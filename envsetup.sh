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

echo "Check preconditions"
for tool in fzf ffmpeg; do  # TODO: any python replacement for ffmpeg?
    [[ $(type -P $tool) ]] || >&2 echo "ERROR: $tool not installed!"
done

echo "Define and check root path"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
(cd $SCRIPT_DIR && python3 -m venv venv --prompt pwf)
. "$SCRIPT_DIR"/venv/bin/activate

echo "Install required python packages into venv"
pip install pillow rawpy pytest mypy

echo "Add bin folder to PATH variable"
export PATH="$SCRIPT_DIR/bin/:$PATH"
export PYTHONPATH="$SCRIPT_DIR/bin/:$PYTHONPATH"

echo "Define global variables for pwf scripts"
export PWF_ROOT_PATH="$HOME/pictures/own_photos/"
python3 -m common  # check root path

echo "Set up fzf environment"

export FZF_CTRL_T_COMMAND="find -L $PWF_ROOT_PATH"
export FZF_ALT_C_COMMAND="find -L $PWF_ROOT_PATH -type d"

eval "$(fzf --bash)"

_fzf_compgen_path() {
    $FZF_CTRL_T_COMMAND
}

_fzf_compgen_dir() {
    $FZF_ALT_C_COMMAND
}

alias ll >/dev/null 2>&1 || alias ll="ls -alF"
_fzf_setup_completion dir ll
_fzf_setup_completion dir ls
_fzf_setup_completion dir pwf_check.py
_fzf_setup_completion dir pwf_cleanup.py
_fzf_setup_completion dir pwf_import.py
_fzf_setup_completion dir pwf_prepare_lab.py
_fzf_setup_completion dir pwf_statistics.py
_fzf_setup_completion path pwf_downsize.py
_fzf_setup_completion path pwf_extract_previews.py
_fzf_setup_completion path pwf_link.py
_fzf_setup_completion path pwf_protect.py
_fzf_setup_completion path pwf_rename_by_date.py
