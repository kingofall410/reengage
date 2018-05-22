
Please create two empty directories in the same place that you place the .py files called "logs" and "data"!!!!
(I'll fix this tomorrow)

Run with the command py reengage_email.py <inputfilename> [options]

<inputfilename> is required to be the first parameter.  It can be relative (to the location of reengage_email.py) or absolute.
If it's a directory it should be a maildir containing inboxes to convert into an mbox file.  It should not end with "\"
If it's a file it can be an mbox or pickle file

OPTIONS
-c <outfile>: where you want to store the output of an mbox conversion.  By default it will go into "data\<infile>.mbox"
-p <outfile>: where you want to store the output of an mbox parse.  By default it will go into "data\<infile_directory>.pickle"
-v: show the visualization
-d: run debug logs

The things you'll use most often are:
1. py reengage_email.py input.mbox - parse the mbox and save input.pickle for future use
2. py reengage_email.py input.pickle - load the previously parsed mbox and analyze
