Tasks
=====

Adding additional tasks is a relatively straightforward process although there
are a few pitfalls to mind. First add the implementation of your algorithm to
the nidaba source directory and ensure that you have written tests that
thoroughly cover your new module. It is of utmost importance to not break any
other functionality. 

Next find the module in the tasks package that is most fitting for the problem
your extension solves. If your code introduces a whole new step in the
pipeline, for example a new kind of post-processing, create a new module so the
command line util is able to utilize it. Write the wrapper functions
encapsulating your new code in tasks, i.e. function that accept and return
storage tupels.

Finally add parameters to the cli parsers and document your addition in the docs.
