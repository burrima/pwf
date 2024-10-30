# Photo-Editing Work-Flow (PWF) Bash Tools

This repository contains self-developed Bash scripts (small tools) for my personal photo editing workflow. These scripts can be used by anyone, that's why I put them onto Github.

## Motivation

The main motivation between this project is the whish to be independent of any third-party photo-organizing and workflow tools. The problem I see with these tools is that they get overtaken by other tools over time and might even become unmaintained and obsolete one day. Migration from one tool to another is usually not so easy, as each tool tries to keep its "customers" by making the migration hard on purpose (or at least does not see this as use-case). That's how I see it and what I have seen by experience.

I have a database of photos which I want to keep for the rest of my life - with no buy-in to any tools (or at least the minimum amount required).

## What to expect

The small scripts in this repo are no rocket-science. They support me realizing a very basic workflow to store, sort, process and publish photos, with the goal to automate the regular tasks. Nothing which could not be done manually - but more effective and less error-prone. There are no fancy tools involved: It is all about copying, moving, linking and protecting of image files (and video, audio along). Photos can be edited with any tool of choice. PWF ensures that the originals are untouched and that any sidecar-files placed next to the edited files are securely stored for the future.

> [!WARNING]
> The code in this repository comes without any waranty! It is my personal code opened to the public (under [MIT License](LICENSE)).

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

In addition to the tools, you must specify the base folder of your library in `envsetup.sh` (variable `PWF_HOME`).

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

    2024-10-26_very-exciting-event

Inside an event folder, files are stored in sub-folders:

    jpg/    # JPG and JPEG files
    raw/    # RAW files from camera
    video/  # video files of any type
    audio/  # audio files of any type

There might be other folders - but this is the ones I use by my own. More on extending the scripts later. I mostly care about photos - but video and audio files are also interesting sometimes to make a nice diashow complete.

### Naming restrictions

There are restrictions on the file and event folder names. The reason behind this is that the Bash shell is tricky when it comes to certain characters (e.g. spaces) and I had my bad experience in the past with a messed up photo archive. Very properly coded Bash scripts are able to handle these special characters - but for safety and time reasons, I decided to rather limit myself on the used characters than to risk again a corrupted archive. The allowed characters are:

  * Alphanumerics (A-z, a-z, 0-9)
  * German Umlaute: ä, ö, ü, Ä, Ö, Ü
  * French é
  * Tilde ~
  * Dot .
  * Underscore _
  * Dash -

The allowed characters are defined in the variable `PWF_ALLOWED_CHARACTERS`, set by the `envsetup.sh` script. You can extend it at your own risk.

## Usage basics

Scripts can be called from any location as they are able to operate on absolute and relative paths. Don't forget to source the `envsetup.sh` before using any PWF script.

### In-tool help

Any script can be called with the parameter `-h` to get further help.

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

The PWF tools are useless without proper workflow definition. The workflow specifies the different steps to work with the photos and where to use which tool. The workflow basically consists of the following steps:

  * Step 0: Prepare new files for integration
  * Step 1: Import new files to the data base
  * Step 2: Process files in the laboratory
  * Step 3: Further organize files in albums
  * Step 4: Publish albums to the web

### Preparation

Before anything can be done, the following command is required:

    source envsetup.sh

This loads a virtual environment (similar to Python venv) for the PWF tools. It helps simplifying PWF internas and furthermore, it integrates the Fuzzy-Find-File FZF tool to work very efficiently. More on this later.

### Step 0: Prepare new files for integration

Before any files can be integrated into the PWF folder structure, they must meet certain conditions. Put the files into a new event folder inside `0_new/`, for example:

    0_new/2024-10-26 some new event/jpg/001.jpg
    0_new/2024-10-26 some new event/raw/1234.RAW

Note the spaces in the name of the event folder name. After placing the files, it is essential to meet the [Naming restrictions](#h-naming-restrictions). To check this, the tool `pwf-check` can be used. Calling it with `-h` shows that it has an automatic fixing option:

    pwf-check -f PATH

At the end, it shall report: `pwf-check: OK` - If not, carefully read the output. Maybe you have to manually interact. It is important to make the check pass, otherwise other tools may fail.

After this, it is a good time to look through the photos and already delete the ones which are for sure not needed any longer. To efficiently walk through the raw files, the script `pwf-extract-previews` can be used. It creates preview files along the raw files, which can be easily deleted again with:

    rm PATH/*-preview.jpg

Once you are confident about the content and structure of the new event folder to import, proceed to the next step.

### Step 1: Import new files to the data base

During this step, all files prepared in a new event folder inside `0_new/` will be archived forever and there will be no (easy) way to remove them again (adding is easy though). So, you must be really confident that the folder-to-integrate is ready.

Use the following command to integrate the new files to the `1_original/` archive:

    pwf-move-new-to-original PATH

This again runs `pwf-check` before doing anything. If passed, it moves the whole event folder into the archive. Then, it runs `pwf-protect` to protect the files against (intentional or unintentional) manipulation. Also this script shall report `OK` at the end.

Archive integrity chan be checked anytime with:

    pwf-check PATH

Furthermore, statistics can be retrieved with:

    pwf-statistics PATH

### Step 2a: Prepare the laboratory

The folder `1_original/` is the storage for the original files. No file in this structure shall be deleted nor changed over time. Files and folders are write-protected and additionally protected by MD5 sums. Working on images is done within the `2_lab/` folder structure. This has the benefit that the user can be sure at any time that no manipulation can compromise the original files.

To prepare the lab for an event, use the following script:

    pwf-prepare-lab PATH_TO_ORIG_EVENT

The first time this script is called (i.e. when no corresponding event folder is present in the `2_lab/` folder structure) it creates a new event  folder in the lab directory and puts only the preview files into `1_previews/` (jpg and raw previes combined). Furthermore, it uses `pwf-rename-by-date` to append a date prefix in front of each preview file name. This brings the files from different cameras into order.

Now you can do filtering (delete unused previews) and fix the dates stored inside the pictures (if cameras were not aligned). More on this later.

### Step 2b: Process files in the laboratory

After sorting out the unnededed previews, call the script again:

    pwf-prepare-lab PATH_TO_ORIG_EVENT

This time, all original files are soft-linked into the lab dir (into corresponding sub-folders:

    2_original_jpg/
    2_original_raw/
    2_original_audio/
    2_original_video/

Now is the time to use your tools of choice to work on the files. Time for creativity! All sidecar files from the production process can remain along the files in the `2_original_xy` folders. Any original file therein can still be deleted because it's only a soft-link to the original stored in `1_original/`.

All final files to keep shall now be moved into these folders inside the lab event folder:

    3_final_jpg/  # including JPG-converted RAW files
    3_final_audio/
    3_final_video/

This is manual work because no script can know what your intentions are. Unprocessed final files (e.g. video files which you don't want to further process) can be copied or moved directly from `2_original_xy/` (remember: these are only soft-links). When done, proceed to the next step.

### Step 2c: Finalize lab activities and cleanup

After the creative process there are many small files lying around in the `2_lab/` folders. This is not a problem per se, but it fills up the harddrive unnecessarily. Furthermore, you may want to start another creative process later, preserving the first attempt. To cleanup, call:

    pwf-cleanup PATH_TO_LAB_EVENT

This creates a `.tar.bz2` file of all previews and all files in the `2_original_xy` sub-folders. Note that previews are not really stored, instead a list of the existing previews is put into the tar-file. This makes it smaller with the same result - previews can be re-generated at any time in future, given that the original archive is not touched.

The cleanup reduces the number of stored files and allows you to re-create the lab-session anytime later in future (more on this later).

### Step 3a: Put final files to albums

After all files are processed to taste and the lab is cleaned up, it is time to distribute the pictures (and other files) to albums. However, the final files in the `2_final_xy/` lab sub-folders shall remain where they are. They shall be linked from the album folders. This is a zero-copy approach with some benefits:

  * The real data is only stored once on the hard-drive, while pictures may be referenced from different albums
  * Exchanging a picture in all albums with a new version is extremely simple (just overwrite the final version in the lab folder)

However:

  * Lab final files must remain there forever, to not risk album corruption
  * Publishing an album to another place (e.g. cloud storage) must be done with care, such that the real files are published, not the links

The last point is normally not a problem because for cloud storage I use smaller versions of the pictures, which are auto-generated and stored in the albums-folder.

An album can be created by manually linking the files or with the following script:

    pwf-link SRC DST_DIR

> [!NOTE]
> Version 1.0 of the PWF scripts only provides rudimentary support for this step.

### Step 3b: Organize prints

Whenever I print a picture, I take special care about the processing. This might be much different than for screen presentation. No problem: the final file for printing is stored in the lab final folder and a link to it is stored in the `4_print` folder. This allows me to find printed photos easily for later re-printing if required.

This is manual work for the time being (as I don't print often, there was no need for a script so far).

### Step 4: Publish albums to the web

I personally use a cloud storage to have my photos at hand world-wide and to share with friends and family. But of course I share only smaller versions of the photos for storage optimization and loading speed reasons. For screen presentation, a 4k UHD image is the maximum needed (even on 8k screens as long as you don't do pixel-peeping). I normally even use QHD resolution, which provides enough detail in my eyes.

There are 2 more PWF scripts which can be used for this:

    pwf-downsize-image
    pwf-downsize-video

Use the parameter `-h` to see the details how they work.

> [!NOTE]
> Version 1.0 of the PWF scripts only provides rudimentary support for this step.

## Other use of the PWF scripts

There are two scripts with has shown to be useful outside of the PWF workflow:

    pwf-protect
    pwf-check -i dup,name,path,raw

The first one I use to protect data archive folders (not necessarily pictures), and the second one I use to check the archive integrity (or sometimes just `md5sum -c` (see `man md5sum`).

## Future extensions

There are several ideas in my mind how to improve the PWF scripts:

  * Automate the initial album creation and later album update (pwf-link is not enough)
  * Protect the final files in the lab folders on lab completion
  * Automate the process from `0_new` to `3_album` for snapshot photos of events, where no lab activities are planned (save all the manual script invocations)
