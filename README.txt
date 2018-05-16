Run with the command py reengage_email.py <inputfilename> [options]

<inputfilename> is required to be the first parameter.  It can be relative (to the location of reengage_email.py) or absolute.
If it's a directory it should be a maildir containing inboxes to convert into an mbox file.  It shoudl not end with "/"
If it's a file, it should be an mbox file.

OPTIONS
-c <outfile>: convert the emails in the specified directory to an mbox file;  outfile must be specified
-p: run the parser
-v: show the visualization

The things you'll use most often are:
1. py reengage_email.py input.mbox -p -- Just parse the specified mbox file
2. py reengage_email.py input.mbox -pv -- Parse the specified mbox file and display the graph
3. py reengage_email.py inputdir -c  output.mbox -p -- Convert inputdir, then parse it
