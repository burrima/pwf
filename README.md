# Photo-Editing Work-Flow (PWF) Bash Tools

This repository contains self-developed Bash scripts (small tools) for my personal photo editing workflow. These scripts can be used by anyone, that's why I put them onto Github.

## Motivation

The main motivation between this project is the whish to be independent of any third-party photo-organizing and workflow tools. The problem I see with these tools is that they get overtaken by other tools over time and might even become unmaintained and obsolete one day. Migration from one tool to another is usually not so easy, as each tool tries to keep its "customers" by making the migration hard on purpose (or at least does not see this as use-case). That's how I see it and what I have seen by experience.

I have a database of photos which I want to keep for the rest of my life - with no buy-in to any tools (or at least the minimum amount required).

## What to expect

The small scripts in this repo are no rocket-science. They provide a very basic workflow to store, sort, process and publish photos. Nothing which could not be done manually - but in an automated way, to make it more effective and less error-prone. There are no fancy tools involved: It is all about copying, moving, linking and protecting of image files. Photos can be edited with any tool of choice. PWF ensures that the originals are untouched and that any sidecar-files placed next to the edited files are securely stored for the future.

## Prerequisites

To use the PWF tools, you must be familiar with the Bash shell and have at least some basic Linux understanding. I personally use Debian-based distros (Raspberry Pi OS and Ubuntu). In addition to this, you must install the following software:

  * Fuzzy-Find-Files (FZF)
  * exiv2
  * imagemagick
  * cksum
  * md5sum
  * ffmpeg (for video resizing only)

On my machine, I was able to install this with the following command (note: cksum and md5sum are standard software):

    sudo apt install fzf exiv2 imagemagick ffmpeg

These tools are the only fixed dependency from any third-party software. They are long-living tools. Should one die, it should be fairly easy to replace it with another one.

## Folder structure

The PWF tools require certain folder structures to be as expected in order to operate successfully. The requirements are described in this section.

### Top-level structure

PWF tools only work with the following top-level folder structure:

    0_new/       # place where new photos are prepared before integration
    1_original/  # protected place where all original files are stored
    2_lab/       # place where the laboratory activities are done
    3_album/     # place where photos to show are stored (albums)
    4_print/     # place where printed photos are stored

Details of each folder are provided in the [Workflow](#workflow) description below. These folders must be created initially by the user, there is no tool to do this.

### Event folders

Generally, files of an event are stored inside an event folder, which is named as follows:

    <year>-<month>-<day>_<eventname>

So, for example:

    2024-10-26_Very-exciting-event

Inside an event folder, files are stored in sub-folders:

    jpg/    # JPG and JPEG files
    raw/    # RAW files from camera
    video/  # video files of any type
    audio/  # audio files of any type

There might be other folders - but this is the ones I use by my own. More on extending the scripts later. I mostly care about photos - but video and audio files are also interesting sometimes.

### Naming restrictions

There are restrictions on the file and event folder names. The reason behind this is that the Bash shell is tricky when it comes to certain characters (e.g. spaces) and I had my bad experience in the long past with a messed up photo archive. Very properly coded Bash scripts are able to handle these special characters - but for safety and time reasons, I decided to rather limit myself on the used characters than to risk again a corrupted archive. The allowed characters are:

  * Alphanumerics (A-z, a-z, 0-9)
  * German Umlaute: ä, ö, ü, Ä, Ö, Ü
  * French é
  * Tilde ~
  * Dot .
  * Underscore _
  * Dash -

The allowed characters are defined in the variable `PWF_ALLOWED_CHARACTERS`, set by the `envsetup.sh` script.

## Usage basics

### In-tool help

Any script can be called with the parameter -h to get further help.

### FZF tool integration

Scripts usually take a PATH as parameter. This can be a folder or a file. Normal Bash-like providing of paths was too slow and annoying for me. Pressing the Tab key repeatedly, trying to navigate to the correct path is a boring activity.

With the integration of the FZF tool, things become interesting. As an example, try the following:

    pwf-check **<tab>

This brings the FZF tool to the front. Now, you can type any part of the path you are looing for, the FZF tool will make a best guess of what you mean. For example, to provide the follwing path as arguemnt to `pwf-check`:

    0_new/2024-10-26_Crazy_new_event/raw/

I would maybe literally type the following:

    pwf-check **<tab>
    0Crazyraw

FZF would directly find the folder from out of the whole tree. If several hits are similar, I can use the arrow keys up and down to select the next proposal, or I could refine the FZF search further. How cool is that?

## Workflow

The PWF tools are useless without proper workflow definition. The workflow specifies the different steps to work with the photos and where to use which tool.

### Preparation

Before anything can be done, the following command is required:

    source envsetup.sh

This loads a virtual environment (similar to Python venv) for the PWF tools. It helps simplifying PWF internas and furthermore, it integrates the Fuzzy-Find-File FZF tool to work very efficiently. More on this later.

### Step 0: Prepare new photos for integration

Before any files can be integrated into the PWF folder structure, they must meet certain conditions. Therefore, put the files into a new event folder inside `0_new/`, for example:

    0_new/2024-10-26 some new event/jpg/001.jpg
    0_new/2024-10-26 some new event/raw/1234.RAW

Note the spaces in the name of the event folder name. After placing the files, it is essential to meet the [Naming restrictions](#h-naming-restrictions). To check this, the tool `pwf-check` can be used. Calling it with -h shows that it has an automatic fixing option:

    pwf-check -f PATH

At the end, it shall report: `pwf-check: OK` - If not, carefully read the output. Maybe you have to manually interact. It is important to make the check pass, otherwise other tools may fail.

After this, it is a good time to look through the photos and already delete the ones which are for sure not needed any longer. To efficiently walk through the raw files, the script `pwf-extract-previews` can be used. It creates preview files along the raw files, which can be easily deleted again with:

    rm PATH/*-preview.jpg

Once you are confident about the content and structure of the new event folder to import, proceed to the next step.

### Step 1: Integrate new photos to the data base

### Step 2a: Prepare the laboratory

### Step 2b: Work on the photos

### Step 2c: Finalize lab activities and cleanup

### Step 3: Collect files for presentation

### Step 4: Collect files for print