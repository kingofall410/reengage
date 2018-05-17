
Please create two empty directories in the same place that you place the .py files called "logs" and "mbox"!!!!
(I'll fix this tomorrow)

Run with the command py reengage_email.py <inputfilename> [options]

<inputfilename> is required to be the first parameter.  It can be relative (to the location of reengage_email.py) or absolute.
If it's a directory it should be a maildir containing inboxes to convert into an mbox file.  It should not end with "\"
If it's a file, it should be an mbox file.

OPTIONS
-o <outfile>: where you want to store the output of an mbox conversion.  By default it will go into "mbox\<infile_directory>"
-p: run the parser
-v: show the visualization

The things you'll use most often are:
1. py reengage_email.py input.mbox -p -- Just parse the specified mbox file
2. py reengage_email.py input.mbox -pv -- Parse the specified mbox file and display the graph
3. py reengage_email.py inputdir -pv -- Convert inputdir, store in default location, then parse/visualize
